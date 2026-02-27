import logging
from flask import jsonify
from datetime import datetime

class ErrorHandler:
    def __init__(self):
        self.setup_logging()
        
    def setup_logging(self):
        """Configure logging for production use"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('chatbot_errors.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    def handle_order_not_found(self, search_criteria):
        """Handle order not found scenarios"""
        self.logger.info(f"Order not found with criteria: {search_criteria}")
        return {
            "response": "I couldn't find an order with that information. Could you please double-check your order ID, email address, or phone number? I'm here to help once we locate your order.",
            "error_type": "order_not_found",
            "requires_clarification": True
        }
    
    def handle_system_error(self, error, context=""):
        """Handle system errors safely"""
        error_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.logger.error(f"System error [{error_id}]: {str(error)} - Context: {context}")
        
        return {
            "response": "I'm experiencing some technical difficulties right now. Please try again in a few moments, or contact our support team if the issue persists.",
            "error_type": "system_error",
            "error_id": error_id
        }
    
    def handle_session_expired(self):
        """Handle expired sessions gracefully"""
        self.logger.info("Session expired - clearing context")
        return {
            "response": "I'd be happy to help you! Could you please provide your order ID, email, or phone number so I can assist you?",
            "error_type": "session_expired",
            "requires_order_info": True
        }
    
    def handle_invalid_order_state(self, order_id, requested_action, current_state):
        """Handle invalid order state for requested action"""
        self.logger.info(f"Invalid state for order {order_id}: {requested_action} not allowed in {current_state}")
        
        state_messages = {
            ("cancel_order", "delivered"): f"Order {order_id} has already been delivered. I can help you initiate a return instead if needed.",
            ("cancel_order", "shipped"): f"Order {order_id} has already shipped. You can refuse delivery when it arrives, or I can help with a return once delivered.",
            ("refund_status", "paid"): f"I don't see any refund requests for order {order_id}. Would you like to start a return and refund process?",
        }
        
        key = (requested_action, current_state)
        message = state_messages.get(key, f"I can't perform that action on order {order_id} in its current state. Let me suggest some alternatives.")
        
        return {
            "response": message,
            "error_type": "invalid_order_state",
            "suggested_actions": self.get_suggested_actions(current_state)
        }
    
    def handle_llm_failure(self, deterministic_response, intent):
        """Handle LLM processing failures"""
        self.logger.warning(f"LLM processing failed for intent: {intent}")
        return {
            "response": deterministic_response,  # Always fallback to deterministic
            "error_type": "llm_failure",
            "fallback_used": True
        }
    
    def handle_validation_error(self, field, value):
        """Handle input validation errors"""
        self.logger.info(f"Validation error - {field}: {value}")
        
        validation_messages = {
            "order_id": "Please provide a valid order ID (e.g., AMZ123456789 or ORD-12345).",
            "email": "Please provide a valid email address.",
            "phone": "Please provide a valid phone number.",
            "intent": "I didn't understand your request. Could you please rephrase what you need help with?"
        }
        
        message = validation_messages.get(field, "Please check your input and try again.")
        
        return {
            "response": message,
            "error_type": "validation_error",
            "field": field
        }
    
    def get_suggested_actions(self, order_state):
        """Get suggested actions based on order state"""
        suggestions = {
            "delivered": ["initiate_return", "report_issue", "track_return"],
            "shipped": ["track_order", "delivery_instructions", "refuse_delivery"],
            "processing": ["cancel_order", "modify_order", "track_order"],
            "out_for_delivery": ["track_order", "delivery_instructions", "contact_carrier"]
        }
        return suggestions.get(order_state, ["track_order", "contact_support"])
    
    def create_safe_response(self, error_info):
        """Create a safe JSON response from error info"""
        return jsonify({
            "response": error_info["response"],
            "metadata": {
                "error_handled": True,
                "error_type": error_info.get("error_type"),
                "timestamp": datetime.now().isoformat()
            }
        })
    
    def log_user_interaction(self, user_query, intent, order_id=None, response_type="success"):
        """Log user interactions for analytics"""
        self.logger.info(f"User interaction - Query: {user_query[:50]}... | Intent: {intent} | Order: {order_id} | Type: {response_type}")
    
    def handle_rate_limit_exceeded(self, user_identifier):
        """Handle rate limiting"""
        self.logger.warning(f"Rate limit exceeded for user: {user_identifier}")
        return {
            "response": "You're sending messages too quickly. Please wait a moment before trying again.",
            "error_type": "rate_limit",
            "retry_after": 60
        }