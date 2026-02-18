# Oudience - Amazon-Style Customer Support Chatbot

## Project Overview

Oudience is an AI-powered customer support chatbot that combines traditional RAG (Retrieval-Augmented Generation) capabilities with Amazon-style order management and customer service functionality. The system provides intelligent responses to customer queries while maintaining strict deterministic control over business logic and order data.

### Key Capabilities
- **Order Management**: Track orders, check delivery status, handle cancellations and refunds
- **Session-Aware Conversations**: Persistent order context across multiple messages
- **Real-Time Status Updates**: Dynamic order status with timestamp-based messaging
- **Amazon-Style Intent Handling**: Professional, polite customer service responses
- **Hybrid Intelligence**: RAG for general queries + deterministic logic for order operations
- **Zero-Hallucination Safety**: LLM restricted to response phrasing only

### Design Principles
1. **Deterministic-First**: Business logic never relies on LLM decisions
2. **Session Persistence**: Order context maintained across conversation
3. **Safety-First**: Strict guardrails prevent data hallucination
4. **Performance-Optimized**: Minimal token usage, fast response times
5. **Amazon-Style UX**: Professional, helpful, and trustworthy interactions

## System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    Oudience Chatbot System                      │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Frontend Layer (Unchanged):                                   │
│  ├─ index.html (Chat Interface)                               │
│  └─ admin.html (Admin Dashboard)                              │
│                                                                 │
│  Flask Application Layer:                                      │
│  ├─ /query (Main Chat Endpoint)                               │
│  ├─ /admin/* (Admin Routes)                                   │
│  └─ /test/* (Backend Testing)                                 │
│                                                                 │
│  Core Services Layer:                                          │
│  ├─ IntentHandler (Amazon-style intent routing)               │
│  ├─ OrderService (Deterministic order operations)             │
│  ├─ SessionManager (Conversation memory)                      │
│  ├─ ResponsePolisher (LLM safety + tone)                      │
│  └─ RealtimeMessaging (Status updates)                        │
│                                                                 │
│  Data Layer:                                                   │
│  ├─ orders.json (Order database)                              │
│  ├─ knowledge_base.json (RAG content)                         │
│  └─ flask_sessions/ (Session storage)                         │
│                                                                 │
│  AI/ML Layer:                                                  │
│  ├─ SentenceTransformer (Embeddings)                          │
│  └─ Cosine Similarity (RAG matching)                          │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Request Flow
```
User Query → Intent Detection → Order Context Resolution → 
Deterministic Logic → Response Polishing → Real-time Enhancement → 
Session Update → Final Response
```

## Backend Flow

### Chat Request Lifecycle

1. **Request Reception**: `/query` endpoint receives user message
2. **Session Refresh**: Check session validity, clear if expired
3. **Intent Detection**: Classify user intent using pattern matching
4. **Order Info Extraction**: Parse order IDs, emails, phone numbers from message
5. **Order Context Resolution**: 
   - Use extracted info to find order, OR
   - Retrieve active order from session memory
6. **Intent Routing**: Route to appropriate handler based on intent
7. **Deterministic Processing**: Execute business logic without LLM involvement
8. **Response Polishing**: Apply Amazon-style tone using rule-based system
9. **Real-time Enhancement**: Add timestamps and status change notifications
10. **Session Update**: Store order context and conversation summary
11. **Response Delivery**: Return polished response to user

### Session Memory Handling

The `SessionManager` maintains conversation state:

```python
Session Data:
- active_order_id: Currently discussed order
- verified_user: Authentication status
- last_intent: Previous user intent
- compact_conversation_summary: Compressed chat history
- last_known_status: For change detection
- session_start/last_activity: Timeout management
```

**Memory Rules**:
- 30-minute session timeout with automatic cleanup
- Order context persists until session expires
- Conversation summary capped at 300 characters
- Safe reset on session expiry

### Order Context Persistence

Once an order is identified:
1. Order ID stored in `active_order_id`
2. User marked as `verified_user`
3. Subsequent messages automatically use stored order
4. No re-asking for order information
5. Context maintained across intent changes

## OrderService Design

### Data Model

```python
Order Object:
{
  "order_id": "AMZ123456789",
  "email": "user@example.com", 
  "phone": "9876543210",
  "items": [
    {"name": "Product", "quantity": 1, "price": 2999}
  ],
  "payment_status": "paid|pending|failed|refunded",
  "shipment_status": "processing|shipped|out_for_delivery|delivered",
  "carrier": "Amazon Logistics",
  "tracking_id": "TRK789012345",
  "expected_delivery": "2026-01-11",
  "last_updated": "2026-01-09 14:30:00"
}
```

### Data Source Strategy

1. **Primary**: Check for existing SQLite database (`analytics.db`)
2. **Fallback**: Use JSON file storage (`orders.json`)
3. **Auto-initialization**: Create mock data if no orders exist

### Core Functions

- `get_order_by_id(order_id)`: Retrieve by order ID
- `get_order_by_email(email)`: Retrieve by customer email
- `get_order_by_phone_last4(last4)`: Retrieve by phone last 4 digits
- `refresh_order_status(order_id)`: Simulate real-time updates
- `find_order(**kwargs)`: Unified search interface

### Real-Time Status Simulation

The system simulates real-time updates by:
- Checking time since last update
- Randomly progressing status if sufficient time passed
- Following logical status progression: processing → shipped → out_for_delivery → delivered
- Updating timestamps on status changes

## Intent Engine

### Supported Intents

| Intent | Trigger Patterns | Purpose |
|--------|------------------|---------|
| `track_order` | "track", "tracking", "order status" | Get current order status |
| `where_is_my_order` | "where is", "location of", "find my order" | Get order location |
| `late_delivery` | "late", "delayed", "overdue" | Handle delivery delays |
| `cancel_order` | "cancel", "stop order", "don't want" | Process cancellations |
| `refund_status` | "refund", "money back", "return money" | Check refund status |
| `replace_item` | "replace", "exchange", "defective" | Handle item replacements |
| `payment_issue` | "payment", "charged", "billing" | Resolve payment problems |
| `account_help` | "account", "login", "password" | Account assistance |

### Intent Routing Logic

1. **Pattern Matching**: Use regex and keyword matching for intent detection
2. **Order Validation**: Verify order context exists before processing
3. **State Validation**: Check order state compatibility with requested action
4. **Deterministic Responses**: Generate responses using business rules only
5. **Fallback Handling**: Graceful degradation for edge cases

### Validation Rules

- **Cancel Order**: Cannot cancel if already delivered
- **Refund Status**: Only show refunds for eligible orders  
- **Late Delivery**: Compare against expected delivery date
- **Order Context**: Ask for order info if missing and required

## LLM Safety & Guardrails

### Why LLM is Restricted

1. **Data Integrity**: Prevent hallucination of order details, prices, dates
2. **Business Logic**: Ensure consistent policy application
3. **Customer Trust**: Avoid incorrect information that could mislead customers
4. **Performance**: Minimize latency and token costs
5. **Reliability**: Deterministic responses for critical operations

### Hallucination Prevention

The `ResponsePolisher` implements multiple safety layers:

```python
Safety Mechanisms:
- Extract only safe, non-sensitive context for LLM
- Rule-based tone adjustment (no LLM for most cases)
- Validate responses don't contain hallucinated data
- Pattern matching to detect unauthorized data injection
- Length checks to prevent excessive generation
- Fallback to deterministic response on any safety violation
```

### Token & Latency Optimizations

- **Zero LLM Calls**: Most responses use rule-based tone adjustment
- **Context Filtering**: Only safe metadata passed to LLM when used
- **Response Validation**: Strict checks prevent hallucinated content
- **Deterministic Fallbacks**: Always available if LLM processing fails
- **Session Capping**: Conversation summaries limited to 300 characters

## Libraries & Dependencies

### Core Framework
- **Flask**: Web framework for API endpoints and session management
- **Flask-Session**: Server-side session storage with filesystem backend

### AI/ML Stack
- **sentence-transformers**: Semantic embeddings for RAG functionality
- **transformers**: Hugging Face transformer models
- **torch**: PyTorch backend for neural networks
- **numpy**: Numerical computing for vector operations

### Data Processing
- **pdfplumber**: PDF text extraction for knowledge base uploads
- **sqlite3**: Database operations (built-in Python)
- **json**: JSON data serialization

### Utilities
- **werkzeug**: Secure filename handling for uploads
- **waitress**: Production WSGI server
- **python-multipart**: Multipart form data handling

### Why Each Library

- **Flask**: Lightweight, flexible web framework suitable for chatbot APIs
- **sentence-transformers**: State-of-the-art semantic search for RAG
- **pdfplumber**: Reliable PDF text extraction with good formatting preservation
- **Flask-Session**: Secure session management with filesystem persistence
- **waitress**: Production-ready WSGI server with good performance

## Error Handling & Reliability

### Failure Scenarios

1. **Order Not Found**: 
   - Response: "Order not found. Please check your order ID, email, or phone number."
   - Action: Request clarification politely

2. **System Unavailable**:
   - Response: "I'm experiencing technical difficulties. Please try again in a few moments."
   - Action: Log error, return safe fallback

3. **Session Expired**:
   - Response: Continue conversation but ask for order info again
   - Action: Clear session, start fresh

4. **Invalid Order State**:
   - Response: Explain why action cannot be performed
   - Action: Suggest alternative actions

5. **LLM Processing Failure**:
   - Response: Use deterministic fallback response
   - Action: Log error, continue with rule-based response

### User-Safe Responses

- **Never expose**: Stack traces, internal errors, system details
- **Always provide**: Helpful next steps, alternative options
- **Maintain tone**: Professional, apologetic when appropriate
- **Preserve context**: Don't lose order information due to errors

### Production Hardening

- **Input Validation**: Sanitize all user inputs
- **Rate Limiting**: Prevent abuse of API endpoints
- **Session Security**: HTTPOnly cookies, secure session storage
- **Error Logging**: Comprehensive logging without exposing sensitive data
- **Graceful Degradation**: System continues functioning with reduced capabilities
- **Data Backup**: Regular backups of order and knowledge base data

## How to Run the Project

### Environment Setup

1. **Clone Repository**
```bash
git clone <repository-url>
cd oudience-chatbot
```

2. **Create Virtual Environment**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install Dependencies**
```bash
pip install -r requirements.txt
```

4. **Initialize Data**
```bash
# Orders and knowledge base will be auto-created on first run
mkdir -p uploads flask_sessions
```

### Run Commands

**Development Server**:
```bash
python app.py
```

**Production Server**:
```bash
waitress-serve --host=0.0.0.0 --port=5001 app:app
```

**Access Points**:
- Chat Interface: http://localhost:5001/
- Admin Dashboard: http://localhost:5001/admin
- API Testing: http://localhost:5001/test/order/by_id/AMZ123456789

### Configuration

Key configuration in `app.py`:
- `ADMIN_TOKEN`: Admin authentication token
- `SESSION_FILE_DIR`: Session storage directory
- `UPLOAD_DIR`: PDF upload directory
- Port: 5001 (configurable)

## Design Philosophy

### Why Deterministic-First

1. **Reliability**: Business operations must be predictable and consistent
2. **Trust**: Customers need accurate information about their orders
3. **Performance**: Rule-based logic is faster than LLM inference
4. **Maintainability**: Easier to debug and modify business rules
5. **Cost**: Reduces LLM API costs and token usage

### Why Amazon-Style Flow

1. **User Expectations**: Customers expect Amazon-level service quality
2. **Conversation Flow**: Natural, context-aware interactions
3. **Professional Tone**: Polite, helpful, and solution-oriented responses
4. **Efficiency**: Minimize back-and-forth by remembering context
5. **Trust Building**: Consistent, reliable service builds customer confidence

### Scalability Considerations

1. **Stateless Design**: Each request can be handled independently
2. **Session Cleanup**: Automatic session expiry prevents memory leaks
3. **Database Abstraction**: Easy migration from JSON to proper database
4. **Caching Strategy**: Embeddings cached in memory for performance
5. **Horizontal Scaling**: Session storage can be moved to Redis/database
6. **Load Balancing**: Stateless design supports multiple server instances

---

## Technical Implementation Notes

The system successfully combines the flexibility of RAG-based chatbots with the reliability requirements of customer service operations. By keeping business logic deterministic and using LLM only for response polishing, we achieve the best of both worlds: intelligent conversation capabilities with guaranteed accuracy for critical operations.

The architecture is designed for production use with proper error handling, session management, and safety guardrails while maintaining the conversational quality expected in modern customer service applications.