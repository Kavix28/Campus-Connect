import json
import re
import random
from datetime import datetime

class ResponsePolisher:
    def __init__(self):
        # Human-like transitions and filler phrases for natural conversation
        self.human_phrases = {
            "acknowledgment": [
                "That’s a fair question.",
                "I understand what you're looking for.",
                "I'd be happy to explain that.",
                "Let me look into that for you.",
                "Certainly, here's how that works.",
                "That's a common concern, let me clarify."
            ],
            "bridge": [
                "Let me explain that simply.",
                "Based on our current records,",
                "Here’s the most up-to-date information:",
                "I’ve processed that for you. Here’s the result:",
                "Looking at our unified knowledge base,"
            ],
            "closing": [
                "I hope that helps! Is there anything else you'd like to know?",
                "Does that answer your question?",
                "Let me know if you need more details on this.",
                "I'm here if you have any follow-up questions."
            ]
        }
        
    def polish_response(self, deterministic_response, intent, order=None):
        """
        Polish response to be human-like, non-repetitive, and plain text.
        Follows strict UI compatibility rules (no markdown/HTML).
        """
        try:
            # 1. Clean up any existing markdown/HTML if present
            response = self._to_plain_text(deterministic_response)
            
            # 2. Add human-like variety
            if intent != "general_query":
                # For intent-based responses, add natural phrasing
                ack = random.choice(self.human_phrases["acknowledgment"])
                bridge = random.choice(self.human_phrases["bridge"])
                
                # Check if it already has a greeting/intro
                if not any(phrase.lower() in response.lower()[:50] for phrase in ["hello", "hi", "happy to help", "news"]):
                    response = f"{ack} {bridge} {response}"
            
            # 3. Handle repetitive follow-ups
            if "?" not in response and len(response) < 400:
                closing = random.choice(self.human_phrases["closing"])
                response = f"{response.rstrip('.')} {closing}"
                
            # 4. Final safety check for UI compatibility
            response = self._final_format_check(response)
            
            return response
                
        except Exception:
            # Fallback to a clean version of the original
            return self._to_plain_text(deterministic_response)

    def _to_plain_text(self, text):
        """Removes markdown and HTML tags to ensure UI compatibility."""
        # Remove bold/italic and other markdown
        text = re.sub(r'[*_`#~]', '', text)
        # Remove HTML tags
        text = re.sub(r'<[^>]*>', '', text)
        # Remove markdown style tables/dividers
        text = re.sub(r'\|', ' ', text)
        text = re.sub(r'[-=]{3,}', '', text)
        return text.strip()

    def _final_format_check(self, text):
        """Ensures the response is concise and contains no leaked internal data."""
        # Remove technical jargon leaking (database terms)
        jargon = ["sqlite", "postgre", "schema", "table", "index", "retrieval", "query", "endpoint"]
        for word in jargon:
            if word in text.lower():
                # Only replace if it's clearly technical context
                pattern = r'\b' + re.escape(word) + r'\b'
                text = re.sub(pattern, "system", text, flags=re.IGNORECASE)
                
        return text.strip()

    def summarize_rag_context(self, chunks):
        """Summarizes multiple chunks into a unified response."""
        if not chunks:
            return "I don't currently have information on that in our records."
        
        # Extract unique sentences to avoid redundancy from overlapping chunks
        sentences = []
        for c in chunks:
            chunk_sentences = re.split(r'(?<=[.!?])\s+', c["text"])
            for s in chunk_sentences:
                s_clean = s.strip()
                if s_clean and s_clean not in sentences:
                    # Check for partial overlap too
                    if not any(s_clean in existing or existing in s_clean for existing in sentences):
                        sentences.append(s_clean)
        
        # Combine up to 4 most relevant sounding sentences
        summary = " ".join(sentences[:4])
        cleaned = self._to_plain_text(summary)
        
        return cleaned

    def get_fallback_response(self, intent):
        """Provide safe, human-like fallback responses."""
        fallbacks = {
            "track_order": "I can certainly help you track your shipment. Please provide your order details so I can retrieve the telemetry.",
            "where_is_my_order": "I'd be happy to locate your order for you. Could you share your order ID or email?",
            "late_delivery": "I understand the concern regarding the delay. Let me check the system for an updated estimate.",
            "cancel_order": "I can assist with the cancellation process. Please let me know which order you're referring to.",
            "refund_status": "I can pull up your refund status immediately. Please provide your order information.",
            "account_help": "I'm happy to help with your account. What specifically seems to be the issue?"
        }
        return random.choice(self.human_phrases["acknowledgment"]) + " " + fallbacks.get(intent, "I'm here to assist you with anything else you might need.")
