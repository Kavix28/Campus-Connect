import re
from datetime import datetime

class IntentHandler:
    def __init__(self, order_service):
        self.order_service = order_service
        
    def detect_intent(self, query, has_context=False):
        query_lower = query.lower()
        
        # Priority 1: Specific follow-up patterns IF we have context
        if has_context:
            attribute_triggers = [
                "item", "product", "contain", "buy", "bought", "package",
                "courier", "carrier", "shipping", "deliver",
                "price", "cost", "amount", "total", "pay",
                "tracking", "track id", "trking", "trscking",
                "when", "date", "estimated", "arrival", "delivery time",
                "where", "location", "destination", "address", "going to",
                "status", "update", "progress"
            ]
            # Use stronger context indicators
            context_indicators = ["this", "that", "it", "the order", "my order", "the package", "the details"]
            
            has_trigger = any(t in query_lower for t in attribute_triggers)
            has_context_indicator = any(ci in query_lower for ci in context_indicators)
            
            # If it has a trigger and a context indicator, or just a trigger if it's very specific
            if has_trigger and (has_context_indicator or len(query_lower.split()) < 5):
                return "order_followup_query"
        
        # Track order patterns
        if any(phrase in query_lower for phrase in ["track my order", "order status", "tracking ID", "track order"]):
            return "track_order"
        
        # Where is my order patterns - be careful with "location"
        if any(phrase in query_lower for phrase in ["where is my order", "where's my order", "find my order", "delivery location"]):
            return "where_is_my_order"
        
        # Late delivery patterns
        if any(phrase in query_lower for phrase in ["late", "delayed", "not delivered", "when will", "overdue", "still waiting"]):
            return "late_delivery"
        
        # Cancel order patterns
        if any(phrase in query_lower for phrase in ["cancel", "stop order", "don't want", "cancel my order", "stop my order"]):
            return "cancel_order"
        
        # Refund status patterns
        if any(phrase in query_lower for phrase in ["refund", "money back", "return money", "refund status", "get my money"]):
            return "refund_status"
        
        # Replace item patterns
        if any(phrase in query_lower for phrase in ["replace", "exchange", "wrong item", "defective", "damaged", "swap"]):
            return "replace_item"
        
        # Payment issue patterns
        if any(phrase in query_lower for phrase in ["payment", "charged", "billing", "card", "payment failed", "charge issue"]):
            return "payment_issue"
        
        # Account help patterns
        if any(phrase in query_lower for phrase in ["account", "login", "password", "profile", "sign in", "my account"]):
            return "account_help"
            
        # Return policy patterns
        if any(phrase in query_lower for phrase in ["return policy", "how to return", "policy for returns", "return period", "conditions for return", "can i return"]):
            return "return_policy"
        
        # Order items pattern
        if any(phrase in query_lower for phrase in ["item", "product", "buy", "bought", "package contains", "what's in", "contained in"]):
            if any(p in query_lower for p in ["order", "package", "parcel", "delivery"]):
                return "get_order_items"
        
        # Check for company information keywords AFTER order-specific ones
        # If "location" is paired with "office", "company", "oudience", or stands alone without order context
        if "location" in query_lower and not has_context:
            # If it's specifically about an order, we would have caught it above or will catch it below if order ID is present
            # But let's assume "location of [company]" is a general query
            company_hints = ["oudience", "company", "office", "branch", "headquarters", "hq"]
            if any(hint in query_lower for hint in company_hints):
                return "general_query"
            
            # If no order info is present and user just asks "location", assume company location
            has_extractable_data = (
                re.search(r'(AMZ\d+|ORD-\d+)', query.upper()) or 
                re.search(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', query) or 
                re.search(r'\b\d{10}\b', query)
            )
            if not has_extractable_data:
                return "general_query"

        # CRITICAL FIX: If user provides order information (phone/email/order ID) 
        # without explicit intent keywords, infer track_order intent
        order_info_indicators = [
            "phone", "email", "order id", "order number", 
            "amz", "ord-", "@", "number is", "my order", "this order", "that order"
        ]
        has_order_info = any(indicator in query_lower for indicator in order_info_indicators)
        
        # Check if query contains extractable order information
        has_extractable_data = (
            re.search(r'(AMZ\d+|ORD-\d+)', query.upper()) or  # Order ID
            re.search(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', query) or  # Email
            re.search(r'\b\d{10}\b', query)  # Phone number
        )
        
        if (has_order_info or has_extractable_data) and "location" not in query_lower:
            # Avoid misclassifying company contact info as track_order
            company_contact_hints = ["contact", "support email", "hr email", "helpdesk", "office phone"]
            if any(hint in query_lower for hint in company_contact_hints):
                return "general_query"
            
            # If it's a "what is" question about email/phone, it's likely general
            if query_lower.startswith(("what is", "what's", "how to contact", "give me")):
                # Unless it specifically mentions "my order" or similar
                if "my order" not in query_lower and "tracking" not in query_lower:
                    return "general_query"
                    
            return "track_order"
        
        return "general_query"
    
    def extract_order_info(self, query):
        # Extract order ID patterns (AMZ followed by digits OR ORD- followed by digits)
        order_id_match = re.search(r'(AMZ\d+|ORD-\d+)', query.upper())
        if order_id_match:
            return {"order_id": order_id_match.group()}
        
        # Fallback: if user provides just 9 digits (common for AMZ orders)
        nine_digit_match = re.search(r'\b\d{9}\b', query)
        if nine_digit_match:
            return {"order_id": f"AMZ{nine_digit_match.group()}"}

        # Extract email patterns
        email_match = re.search(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', query)
        if email_match:
            return {"email": email_match.group()}
        
        # Extract phone patterns (10 digits)
        phone_match = re.search(r'\b\d{10}\b', query)
        if phone_match:
            return {"phone": phone_match.group()}
        
        # Extract last 4 digits patterns
        last_digits_match = re.search(r'(?:last\s*4|ending\s*in|ends\s*with).*?(\d{4})', query.lower())
        if last_digits_match:
            return {"last_digits": last_digits_match.group(1)}
        
        return {}
    
    def validate_order_context(self, order, intent):
        if not order:
            return False, "I need your order information to help you. Please provide your order ID, email, or phone number."
        
        # Specific validations per intent
        if intent == "cancel_order":
            if order["shipment_status"] == "delivered":
                return False, f"Order {order['order_id']} has already been delivered. For returns, I can help you initiate a return process instead."
        
        if intent == "refund_status":
            if order["payment_status"] not in ["refunded", "refund_pending"]:
                return False, f"I don't see any refund requests for order {order['order_id']}. Would you like to initiate a return and refund?"
        
        return True, ""
    
    def _format_time_ago(self, minutes):
        """Converts minutes to a human-friendly string."""
        if minutes < 1:
            return "just now"
        if minutes < 60:
            return f"about {minutes} minutes ago"
        hours = minutes // 60
        if hours < 24:
            return f"about {hours} hours ago"
        days = hours // 24
        return f"{days} days ago"

    def handle_track_order(self, order, session):
        if not order:
            return "I'd be happy to help you track your order. Could you please provide your order ID (starts with AMZ), email address, or phone number?"
        
        status = order["shipment_status"]
        time_ago = self._format_time_ago(order.get("minutes_since_update", 0))
        
        if status == "delivered":
            return f"Great news! Your order {order['order_id']} was delivered on {order['expected_delivery']}. The status was confirmed {time_ago}."
        
        elif status == "out_for_delivery":
            return f"Your order {order['order_id']} is out for delivery! It's currently in your local area and should arrive by end of day. Carrier: {order['carrier']}. Last scan was {time_ago}."
        
        elif status == "shipped":
            return f"Your order {order['order_id']} is on its way. Tracking ID: {order['tracking_id']} via {order['carrier']}. We expect delivery by {order['expected_delivery']}. The latest transit update was {time_ago}."
        
        elif status == "processing":
            return f"Your order {order['order_id']} is being carefully prepared for shipment at our fulfillment center. We expect it to ship soon, with an estimated delivery of {order['expected_delivery']}."
        
        else:
            return f"Looking at order {order['order_id']}, the current status is {status}. This was updated {time_ago}."
    
    def handle_where_is_my_order(self, order, session):
        if not order:
            return "I can help you locate your order. Please provide your order ID, email address, or phone number so I can check the current location."
        
        status = order["shipment_status"]
        
        if status == "delivered":
            return f"Your order {order['order_id']} was delivered on {order['expected_delivery']}. If you can't find it, please check with neighbors or building management."
        
        elif status == "out_for_delivery":
            return f"Your order {order['order_id']} is currently out for delivery with {order['carrier']}. It should arrive today."
        
        elif status == "shipped":
            return f"Your order {order['order_id']} is in transit with {order['carrier']}. Tracking ID: {order['tracking_id']}. Expected delivery: {order['expected_delivery']}."
        
        elif status == "processing":
            return f"Your order {order['order_id']} is still being processed at our fulfillment center. It will ship soon."
        
        else:
            return f"Your order {order['order_id']} is currently {status}. I can provide more details if needed."
    
    def handle_late_delivery(self, order, session):
        if not order:
            return "I understand your concern about a delayed delivery. Could you please provide your order ID so I can investigate the delay?"
        
        expected = datetime.strptime(order["expected_delivery"], "%Y-%m-%d")
        today = datetime.now()
        
        if today.date() > expected.date():
            days_late = (today.date() - expected.date()).days
            return f"I sincerely apologize that order {order['order_id']} is {days_late} day(s) late. Let me check with our logistics team and provide you with an updated delivery estimate within 2 hours. You may also be eligible for compensation."
        
        elif today.date() == expected.date():
            return f"Your order {order['order_id']} is expected to arrive today ({order['expected_delivery']}). Current status: {order['shipment_status']}. If it doesn't arrive by end of day, please contact me again."
        
        else:
            return f"Your order {order['order_id']} is still within the expected delivery window (by {order['expected_delivery']}). Current status: {order['shipment_status']}."
    
    def handle_cancel_order(self, order, session):
        if not order:
            return "I can help you cancel your order. Please provide your order ID to proceed with the cancellation."
        
        valid, message = self.validate_order_context(order, "cancel_order")
        if not valid:
            return message
        
        if order["shipment_status"] == "shipped" or order["shipment_status"] == "out_for_delivery":
            return f"Order {order['order_id']} has already shipped. You can refuse the delivery when it arrives, or I can help you with a return once it's delivered."
        
        elif order["shipment_status"] == "processing":
            return f"I can cancel order {order['order_id']} since it hasn't shipped yet. Would you like me to proceed with the cancellation? You'll receive a full refund within 3-5 business days."
        
        else:
            return f"Let me check if order {order['order_id']} can still be cancelled. Current status: {order['shipment_status']}. I'll process this request immediately."
    
    def handle_refund_status(self, order, session):
        if not order:
            return "I can check your refund status. Please provide your order ID to look up any refund information."
        
        if order["payment_status"] == "refunded":
            return f"Your refund for order {order['order_id']} has been processed and should appear in your account within 3-5 business days. The refund was issued to your original payment method."
        
        elif order["payment_status"] == "refund_pending":
            return f"Your refund for order {order['order_id']} is being processed. You should see it in your account within 3-5 business days."
        
        else:
            return f"I don't see any refund requests for order {order['order_id']}. Would you like to initiate a return and refund? I can help you start that process."
    
    def handle_replace_item(self, order, session):
        if not order:
            return "I can help you replace an item from your order. Please provide your order ID so I can assist you."
        
        items_list = ", ".join([item["name"] for item in order["items"]])
        return f"I can help you replace an item from order {order['order_id']}. Your order contains: {items_list}. Which item needs to be replaced and what's the issue with it?"
    
    def handle_payment_issue(self, order, session):
        if not order:
            return "I can help resolve payment issues. Please provide your order ID so I can review the payment details."
        
        if order["payment_status"] == "pending":
            return f"I see order {order['order_id']} has a pending payment. Would you like me to help you complete the payment or update your payment method?"
        
        elif order["payment_status"] == "failed":
            return f"There was an issue processing payment for order {order['order_id']}. I can help you retry the payment with the same method or update to a different payment method."
        
        elif order["payment_status"] == "paid":
            return f"Order {order['order_id']} shows as paid successfully. What specific payment concern can I help you with?"
        
        else:
            return f"Let me review the payment details for order {order['order_id']}. Current payment status: {order['payment_status']}. How can I help resolve this?"
    
    def handle_account_help(self, order, session):
        return "I can help with account-related questions. What specific account issue are you experiencing? For security reasons, I may need to verify your identity before making any account changes."
    
    def handle_return_policy(self, order, session):
        """Hardened customer-facing return policy response."""
        return (
            "Our customer return policy allows you to return most items within 30 days of delivery for a full refund. "
            "Items must be in their original condition and packaging. Once we receive your return, "
            "refunds are typically processed within 5-7 business days to your original payment method. "
            "We also offer free exchanges for defective or damaged items. Would you like to start a return for your current order?"
        )
    
    def handle_order_followup(self, order, session):
        """Granular handling of specific order attribute inquiries."""
        if not order:
            return "I need your order information to answer that. Could you please provide your order ID, email, or phone number?"
        
        query_lower = session.get("current_query", "").lower()
        
        # Identify what specific detail the user wants
        if any(k in query_lower for k in ["item", "product", "bought", "contain"]):
            items = order.get("items", [])
            if not items: return f"I don't see any items listed for order {order['order_id']}."
            item_list = [f"{i['quantity']}x {i['name']}" for i in items]
            return f"Order {order['order_id']} contains: {', '.join(item_list)}."
            
        elif any(k in query_lower for k in ["courier", "carrier", "shipping company", "who is delivering"]):
            carrier = order.get("carrier", "not yet assigned")
            if not carrier: return f"A carrier hasn't been assigned to order {order['order_id']} yet. It's still in processing."
            return f"The carrier for your order {order['order_id']} is {carrier}."
            
        elif any(k in query_lower for k in ["price", "cost", "amount", "total", "pay"]):
            items = order.get("items", [])
            total = sum(i.get("price", 0) * i.get("quantity", 1) for i in items)
            return f"The total amount for order {order['order_id']} is ₹{total}."
            
        elif any(k in query_lower for k in ["tracking", "track id"]):
            tracking = order.get("tracking_id")
            if not tracking: return f"Tracking is not yet available for order {order['order_id']}."
            return f"The tracking ID for your order is {tracking} via {order.get('carrier', 'our logistics partner')}."
            
        elif any(k in query_lower for k in ["when", "date", "arrival", "expected"]):
            return f"Order {order['order_id']} is expected to arrive by {order['expected_delivery']}."
            
        elif any(k in query_lower for k in ["where", "location", "destination", "address", "going to"]):
            # Note: We don't store full address in this mock, but we can verify status
            return f"Order {order['order_id']} is currently {order['shipment_status'].replace('_', ' ')} and heading to the address on your profile."
            
        # Default follow-up: status
        return self.handle_track_order(order, session)

    def route_intent(self, intent, order, session):
        intent_handlers = {
            "track_order": self.handle_track_order,
            "where_is_my_order": self.handle_where_is_my_order,
            "late_delivery": self.handle_late_delivery,
            "cancel_order": self.handle_cancel_order,
            "refund_status": self.handle_refund_status,
            "replace_item": self.handle_replace_item,
            "payment_issue": self.handle_payment_issue,
            "account_help": self.handle_account_help,
            "return_policy": self.handle_return_policy,
            "order_followup_query": self.handle_order_followup
        }
        
        handler = intent_handlers.get(intent)
        if handler:
            return handler(order, session)
        
        return "I'm here to help! I can assist with order tracking, deliveries, returns, cancellations, and account questions. What would you like to know?"