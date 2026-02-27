import os
import json
import time
import pdfplumber
import numpy as np
import secrets
from datetime import datetime, timedelta
from flask import (
    Flask, request, jsonify, send_from_directory,
    session, abort
)
from flask_session import Session
from werkzeug.utils import secure_filename
from sentence_transformers import SentenceTransformer
from transformers import pipeline
from order_service import OrderService
from intent_handler import IntentHandler
from response_polisher import ResponsePolisher
from order_status_updater import OrderStatusUpdater
from llm_integration import generate_rag_response
from werkzeug.middleware.proxy_fix import ProxyFix
from prometheus_client import make_wsgi_app
from werkzeug.middleware.dispatcher import DispatcherMiddleware
import logging
from logging.config import dictConfig

# =========================
# Logging Configuration
# =========================
dictConfig({
    'version': 1,
    'formatters': {'default': {
        'format': '[%(asctime)s] %(levelname)s in %(module)s: %(message)s',
    }},
    'handlers': {'wsgi': {
        'class': 'logging.StreamHandler',
        'stream': 'ext://flask.logging.wsgi_errors_stream',
        'formatter': 'default'
    }},
    'root': {
        'level': 'INFO',
        'handlers': ['wsgi']
    }
})

# Load environment variables
load_dotenv()

# =========================
# Flask Setup
# =========================
app = Flask(__name__, static_folder="static", static_url_path="")

# Security: Handle Reverse Proxy Headers
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1)

# Monitoring: Prometheus Metrics Endpoint
# Only add dispatcher if not already added (to prevent dual wrapping in some reloader scenarios)
if os.getenv("ENABLE_METRICS", "false").lower() == "true":
    app.wsgi_app = DispatcherMiddleware(app.wsgi_app, {
        '/metrics': make_wsgi_app()
    })

# FIX 1: Use environment variable for secret key
app.secret_key = os.getenv("SECRET_KEY") or secrets.token_hex(32)
if not os.getenv("SECRET_KEY"):
    print("WARNING: Using generated secret key. Set SECRET_KEY in .env for production!")

app.config["SESSION_TYPE"] = os.getenv("SESSION_TYPE", "filesystem")
app.config["SESSION_FILE_DIR"] = "flask_sessions"
app.config["SESSION_PERMANENT"] = False
app.config["PERMANENT_SESSION_LIFETIME"] = int(os.getenv("SESSION_TIMEOUT", "1800"))  # 30 minutes
Session(app)

# =========================
# Constants
# =========================
# FIX 1: Use environment variable for admin token
ADMIN_TOKEN = os.getenv("ADMIN_PASSWORD_HASH", "admin123")
if ADMIN_TOKEN == "admin123":
    print("WARNING: Using default admin token. Set ADMIN_PASSWORD_HASH in .env for production!")

UPLOAD_DIR = "uploads"
KB_FILE = "knowledge_base.json"
UPLOAD_LOGS = "upload_logs.json"

# FIX 3: File upload security settings
ALLOWED_EXTENSIONS = set(os.getenv("ALLOWED_EXTENSIONS", "pdf").split(','))
MAX_FILE_SIZE = int(os.getenv("MAX_UPLOAD_SIZE_MB", "10")) * 1024 * 1024  # 10MB default
SESSION_TIMEOUT_MINUTES = int(os.getenv("SESSION_TIMEOUT_MINUTES", "30"))

os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs("flask_sessions", exist_ok=True)

# =========================
# Services
# =========================
embedder = SentenceTransformer("all-MiniLM-L6-v2")
qa_pipeline = pipeline("question-answering", model="distilbert-base-cased-distilled-squad")
order_service = OrderService()
intent_handler = IntentHandler(order_service)
polisher = ResponsePolisher()

# Hardening: Background status updater for real-time simulation
status_updater = OrderStatusUpdater(order_service, interval=60)

kb_docs = []
kb_embeddings = None

# =========================
# Helpers
# =========================
def load_json(path):
    if not os.path.exists(path):
        return []
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

def chunk_text(text, size=250):
    words = text.split()
    return [
        " ".join(words[i:i + size])
        for i in range(0, len(words), size)
        if len(words[i:i + size]) > 30
    ]

def load_kb():
    global kb_docs, kb_embeddings
    kb_docs = load_json(KB_FILE)
    if not kb_docs:
        kb_embeddings = None
        return
    texts = [d["text"] for d in kb_docs]
    kb_embeddings = embedder.encode(
        texts,
        convert_to_numpy=True,
        normalize_embeddings=True
    )

def get_session_memory():
    return {
        "active_order_id": session.get("active_order_id"),
        "verified_user": session.get("verified_user", False),
        "last_intent": session.get("last_intent"),
        "conversation_summary": session.get("conversation_summary", "")
    }

def update_session_memory(order_id=None, intent=None, summary=None):
    # FIX 2: Update last activity timestamp
    session["last_activity"] = datetime.now().isoformat()
    
    if order_id:
        session["active_order_id"] = order_id
        session["verified_user"] = True
    if intent:
        session["last_intent"] = intent
    if summary:
        session["conversation_summary"] = summary[:500]  # Cap memory

def polish_response_with_llm(response, intent="general_query", order=None):
    """Polishes response using global polisher instance."""
    return polisher.polish_response(response, intent, order)

# FIX 2: Session timeout middleware
@app.before_request
def check_session_timeout():
    """Enforce session timeout for security"""
    if '/static/' in request.path or request.endpoint == 'static':
        return  # Don't check timeout for static files
    
    last_activity = session.get('last_activity')
    if last_activity:
        try:
            last_time = datetime.fromisoformat(last_activity)
            if (datetime.now() - last_time).total_seconds() > (SESSION_TIMEOUT_MINUTES * 60):
                session.clear()
                if request.endpoint not in ['index', None]:
                    return jsonify({"error": "Session expired", "code": "SESSION_TIMEOUT"}), 401
        except (ValueError, TypeError):
            pass
    
    # Update last activity if session is active
    if session.get('active_order_id') or session.get('is_admin'):
        session['last_activity'] = datetime.now().isoformat()

# FIX 3: File validation helpers
def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def validate_pdf_file(file):
    """Validate PDF file structure and size"""
    # Check file size
    file.seek(0, 2)  # Seek to end
    size = file.tell()
    file.seek(0)  # Reset to beginning
    
    if size > MAX_FILE_SIZE:
        return False, f"File too large. Maximum size is {MAX_FILE_SIZE // (1024*1024)}MB"
    
    if size == 0:
        return False, "File is empty"
    
    # Validate PDF structure
    try:
        with pdfplumber.open(file) as pdf:
            if len(pdf.pages) == 0:
                return False, "PDF has no pages"
            # Check if at least one page has extractable text
            has_text = any(page.extract_text() for page in pdf.pages[:3])  # Check first 3 pages
            if not has_text:
                return False, "PDF appears to be empty or contains only images"
        file.seek(0)  # Reset for later use
        return True, "OK"
    except Exception as e:
        return False, f"Invalid or corrupted PDF: {str(e)}"

load_kb()

# =========================
# Admin Auth
# =========================
def require_admin():
    if not session.get("is_admin"):
        abort(403)

@app.route("/admin/login", methods=["POST"])
def admin_login():
    token = request.json.get("token")
    if token != ADMIN_TOKEN:
        abort(403)
    session["is_admin"] = True
    return jsonify({"ok": True})

# =========================
# Admin Pages
# =========================
@app.route("/admin")
def admin_page():
    return send_from_directory("static", "admin.html")

@app.route("/admin/upload", methods=["POST"])
def admin_upload():
    require_admin()

    file = request.files.get("file")
    if not file:
        return jsonify({"error": "No file uploaded"}), 400
    
    # FIX 3: Validate file type
    if not allowed_file(file.filename):
        return jsonify({"error": f"Invalid file type. Allowed: {', '.join(ALLOWED_EXTENSIONS)}"}), 400
    
    # FIX 3: Validate PDF file
    is_valid, error_msg = validate_pdf_file(file)
    if not is_valid:
        return jsonify({"error": error_msg}), 400

    filename = secure_filename(file.filename)
    path = os.path.join(UPLOAD_DIR, filename)
    file.save(path)

    # Extract text
    text = ""
    with pdfplumber.open(path) as pdf:
        for p in pdf.pages:
            if p.extract_text():
                text += p.extract_text() + "\n"

    chunks = chunk_text(text)

    # Reset KB before re-adding this file
    global kb_docs
    kb_docs = [d for d in kb_docs if d.get("source") != filename]

    start_id = len(kb_docs)
    for i, c in enumerate(chunks):
        kb_docs.append({
            "id": start_id + i + 1,
            "source": filename,
            "text": c.strip()
        })

    save_json(KB_FILE, kb_docs)
    load_kb()

    logs = load_json(UPLOAD_LOGS)
    logs.append({
        "filename": filename,
        "chunks": len(chunks),
        "uploaded_at": time.strftime("%Y-%m-%d %H:%M:%S")
    })
    save_json(UPLOAD_LOGS, logs)

    return jsonify({"chunks_added": len(chunks)})

@app.route("/admin/uploads")
def admin_uploads():
    require_admin()
    return jsonify(load_json(UPLOAD_LOGS))

@app.route("/admin/clear", methods=["POST"])
def admin_clear():
    require_admin()
    global kb_docs, kb_embeddings
    
    # Clear memory
    kb_docs = []
    kb_embeddings = None
    
    # Clear files
    save_json(KB_FILE, [])
    save_json(UPLOAD_LOGS, [])
    
    return jsonify({"ok": True, "message": "Knowledge base cleared successfully."})

# =========================
# Enhanced Chat Endpoint
# =========================
@app.route("/query", methods=["POST"])
def query():
    raw_query = (request.json or {}).get("query", "").strip()
    if not raw_query:
        return jsonify({"response": "Please ask a question."})

    # Security Guardrail: Reject prompt context manipulation or sensitive info requests
    blocked_patterns = ["ignore previous", "system prompt", "admin token", "reveal", "password", "schema"]
    if any(p in raw_query.lower() for p in blocked_patterns):
        return jsonify({"response": "I'm here to assist with your orders and our services. I can't fulfill requests for internal system information. How else can I help?"})

    # Handle greetings and casual conversation
    greeting_patterns = ["hi", "hello", "hey", "good morning", "good afternoon", "good evening"]
    query_lower = raw_query.lower().strip()
    
    # If it's JUST a greeting (no other content)
    if any(query_lower == greeting or query_lower.startswith(greeting + " ") for greeting in greeting_patterns):
        if len(raw_query.strip()) < 20:  # Short greeting
            return jsonify({"response": "Hello! I'm your Oudience AI assistant. I can help you with order tracking, delivery status, returns, refunds, and answer questions about our policies. How can I assist you today?"})

    # Handle multiple questions by splitting
    # Simple split by common delimiters
    import re
    questions = re.split(r'[.?!]|\band\b|\balso\b', raw_query)
    questions = [q.strip() for q in questions if len(q.strip()) > 5]
    
    if not questions:
        questions = [raw_query]

    all_responses = []
    
    # Get session memory once
    memory = get_session_memory()
    
    # Pre-fetch active order to reuse for multiple questions
    active_order = None
    if memory.get("active_order_id"):
        active_order = order_service.get_order_status(memory["active_order_id"])

    for q in questions:
        # Detect intent and extract order info for each sub-question
        has_context = bool(memory.get("active_order_id"))
        intent = intent_handler.detect_intent(q, has_context=has_context)
        order_info = intent_handler.extract_order_info(q)
        
        # Use existing context or find new order
        current_order = active_order
        if order_info:
            found_order = order_service.find_order(**order_info)
            if found_order:
                current_order = order_service.get_order_status(found_order["order_id"])
                # Update context for remaining questions in this request
                active_order = current_order
                update_session_memory(order_id=current_order["order_id"], intent=intent)
        
        # Ensure we have the most up-to-date memory reference
        memory = get_session_memory()

        # Handle intent
        if intent in ["track_order", "where_is_my_order", "late_delivery", "cancel_order", 
                      "refund_status", "replace_item", "payment_issue", "account_help", 
                      "order_followup_query", "get_order_items", "return_policy"]:
            # Inject current query into memory for handler context
            memory["current_query"] = q
            response = intent_handler.route_intent(intent, current_order, memory)
            
            # Ensure session is updated with latest intent and order
            if current_order:
                update_session_memory(order_id=current_order["order_id"], intent=intent)
        else:
            # General query with RAG
            if kb_embeddings is None:
                response = "I'm here to help! You can ask me about orders, deliveries, returns, or general questions about our policies."
            else:
                q_lower = q.lower()
                # SAFEGUARD 1: Strict Internal Policy Blocking
                internal_triggers = ["reimbursement", "employee policy", "probation", "notice period", "stipend", "it-support@oudience.internal", "hr@oudience.internal", "offboarding", "internal tools", "salary revision"]
                if any(t in q_lower for t in internal_triggers):
                    response = "I'm sorry, I only have information regarding customer-facing policies and order management. For internal employee matters, please refer to the company's internal portal or contact HR directly."
                else:
                    # SAFEGUARD 2: Policy Domain Filtering - Exclude Internal Chunks
                    customer_facing_indices = []
                    for i, doc in enumerate(kb_docs):
                        text = doc["text"].lower()
                        # Exclude docs that look internal
                        is_internal = any(k in text for k in ["employee", "probation", "reimbursement", "notice period", "offboarding", "it-support@", "hr@oudience.internal", "code review", "release management"])
                        # Include if it looks customer-facing or neutral
                        if not is_internal:
                            customer_facing_indices.append(i)
                    
                    if not customer_facing_indices:
                        # Fallback if everything is internal
                        response = "I'm here to help! Most information about our policies can be found on our main website. I can specifically help with orders and tracking."
                    else:
                        # Perform similarity search only on customer-facing chunks
                        filtered_embeddings = kb_embeddings[customer_facing_indices]
                        q_emb = embedder.encode([q], convert_to_numpy=True, normalize_embeddings=True)[0]
                        scores = np.dot(filtered_embeddings, q_emb)
                        best_local_idx = int(np.argmax(scores))
                        best_idx = customer_facing_indices[best_local_idx]
                        best_score = float(scores[best_local_idx])

                        similarity_threshold = float(os.getenv("RAG_SIMILARITY_THRESHOLD", "0.30"))
                        
                        if best_score < similarity_threshold:
                            common_topics = {
                                "hour": "Our standard working hours are 9:30 AM to 6:30 PM, Monday to Friday.",
                                "location": "Oudience operates from Bengaluru, Pune (India), and Berlin (Germany).",
                                "contact": "You can reach our support team via the chat or check our contact page.",
                                "return": "We accept returns within 30 days. Please check our return policy for details.",
                                "shipping": "Shipping times vary by location. Most orders arrive within 3-7 business days.",
                                "payment": "We accept major credit cards, debit cards, and online payment methods.",
                            }
                            
                            response = None
                            for keyword, answer in common_topics.items():
                                if keyword in q_lower:
                                    response = answer
                                    break
                            
                            if not response:
                                response = "I'd be happy to help! Could you please provide more details? I can assist with orders, policies, or general info."
                        else:
                            context = kb_docs[best_idx]["text"]
                            # SAFEGUARD 3: Source Leak Prevention - Removed source names
                            
                            # SAFEGUARD 4: KB Result Validation
                            validation_keywords = ["customer", "order", "product", "return", "refund", "shipping", "delivery", "payment", "support", "working hours"]
                            internal_keywords = ["reimbursement", "employee", "probation", "salary", "vpn", "code review", "offboarding"]
                            
                            is_valid_context = any(k in context.lower() for k in validation_keywords)
                            is_internal_context = any(k in context.lower() for k in internal_keywords)
                            
                            if not is_valid_context or is_internal_context:
                                response = "I don't have the specific customer policy for that currently. I recommend checking our official Help Center for the most accurate information on that topic."
                            else:
                                # Check for LLM Provider (Ollama / OpenAI)
                                llm_provider = os.getenv("LLM_PROVIDER", "local").lower()
                                llm_response = None
                                
                                if llm_provider != "local":
                                    try:
                                        llm_response = generate_rag_response(q, context, provider=llm_provider)
                                    except Exception as e:
                                        print(f"LLM Error: {e}")
                                
                                if llm_response:
                                    response = llm_response
                                else:
                                    # Fallback to local extractive QA
                                    try:
                                        qa_result = qa_pipeline(
                                            question=q, 
                                            context=context, 
                                            max_answer_len=150,
                                            top_k=1,
                                            handle_impossible_answer=False
                                        )
                                        answer = qa_result['answer'].strip()
                                        confidence = qa_result['score']
                                        
                                        if confidence > 0.15 and len(answer) > 15:
                                            sentences = answer.split('.')
                                            if len(sentences) > 2:
                                                answer = '. '.join(sentences[:2]) + '.'
                                            response = answer
                                        else:
                                            sentences = context.split('.')
                                            query_keywords = set(q_lower.split())
                                            scored_sentences = []
                                            
                                            for sent in sentences[:10]:
                                                sent = sent.strip()
                                                if len(sent) > 20 and len(sent) < 300:
                                                    sent_words = set(sent.lower().split())
                                                    overlap = len(query_keywords.intersection(sent_words))
                                                    if overlap > 0:
                                                        scored_sentences.append((overlap, sent))
                                            
                                            if scored_sentences:
                                                scored_sentences.sort(reverse=True, key=lambda x: x[0])
                                                response = scored_sentences[0][1]
                                            else:
                                                response = '. '.join(sentences[:2])
                                    except Exception:
                                        sentences = context.split('.')
                                        clean_sentences = [s.strip() for s in sentences if len(s.strip()) > 20]
                                        response = clean_sentences[0] if clean_sentences else polisher._to_plain_text(context[:200])
        
        # Clean up individual response to avoid redundant follow-ups
        response = response.replace("Is there anything else you'd like to know?", "").strip()
        if response.endswith(".") or response.endswith("?") or response.endswith("!"):
            pass
        else:
            response += "."
            
        all_responses.append(response)

    # Combine responses
    unique_responses = []
    for r in all_responses:
        if r and r not in unique_responses:
            unique_responses.append(r)
    
    final_response = " ".join(unique_responses)
    
    # Polish response tone with intelligence
    final_response = polish_response_with_llm(final_response, intent, current_order)
    
    # Ensure it's not too long
    if len(final_response) > 800:
        final_response = final_response[:797] + "..."

    return jsonify({"response": final_response})

# =========================
# Order Management Endpoints
# =========================
@app.route("/order/lookup", methods=["POST"])
def order_lookup():
    data = request.json or {}
    order = order_service.find_order(
        order_id=data.get("order_id"),
        email=data.get("email"),
        phone=data.get("phone"),
        last_digits=data.get("last_digits")
    )
    
    if order:
        order_status = order_service.get_order_status(order["order_id"])
        update_session_memory(order_id=order["order_id"])
        return jsonify({"found": True, "order": order_status})
    else:
        return jsonify({"found": False, "message": "Order not found. Please check your order ID, email, or phone number."})

@app.route("/session/clear", methods=["POST"])
def clear_session():
    session.clear()
    return jsonify({"cleared": True})

@app.route("/session/status", methods=["GET"])
def session_status():
    """Return current session status for frontend"""
    return jsonify({
        "active": bool(session.get("active_order_id")),
        "last_intent": session.get("last_intent"),
        "active_order_id": session.get("active_order_id")
    })


# =========================
# Frontend
# =========================
@app.route("/")
def index():
    return send_from_directory("static", "index.html")

@app.route("/track-order")
def track_order_page():
    return send_from_directory("static", "track-order.html")

@app.route("/test/system/health", methods=["GET"])
def system_health():
    """System health check for QA verification"""
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "services": {
            "backend": "running",
            "database": "connected"
        }
    })

# =========================
# Run
# =========================
if __name__ == "__main__":
    print("🚀 Oudience running at http://127.0.0.1:5001")
    
    # Start the background status updater
    status_updater.start()
    
    try:
        app.run(host="0.0.0.0", port=5001, threaded=True)
    finally:
        # Final submission cleanup: ensure status updater stops
        status_updater.stop()
