from datetime import datetime
import json

class RealtimeMessaging:
    def __init__(self):
        self.status_hierarchy = {
            "processing": 1,
            "shipped": 2,
            "out_for_delivery": 3,
            "delivered": 4
        }
    
    def get_time_since_update(self, last_updated_str):
        """Calculate time since last update in human-readable format"""
        try:
            last_updated = datetime.strptime(last_updated_str, "%Y-%m-%d %H:%M:%S")
            now = datetime.now()
            diff = now - last_updated
            
            total_minutes = int(diff.total_seconds() / 60)
            
            if total_minutes < 1:
                return "just now"
            elif total_minutes < 60:
                return f"{total_minutes} minute{'s' if total_minutes != 1 else ''} ago"
            elif total_minutes < 1440:  # Less than 24 hours
                hours = total_minutes // 60
                return f"{hours} hour{'s' if hours != 1 else ''} ago"
            else:
                days = total_minutes // 1440
                return f"{days} day{'s' if days != 1 else ''} ago"
        except:
            return "recently"
    
    def detect_status_change(self, current_order, session_memory):
        """Detect if order status has changed since last interaction"""
        if not session_memory or not current_order:
            return False, None
        
        # Get last known status from session
        last_known_status = session_memory.get("last_known_status")
        current_status = current_order.get("shipment_status")
        
        if not last_known_status:
            return False, None
        
        # Check if status has progressed
        if last_known_status != current_status:
            last_level = self.status_hierarchy.get(last_known_status, 0)
            current_level = self.status_hierarchy.get(current_status, 0)
            
            if current_level > last_level:
                return True, {
                    "from_status": last_known_status,
                    "to_status": current_status,
                    "is_progression": True
                }
            else:
                return True, {
                    "from_status": last_known_status,
                    "to_status": current_status,
                    "is_progression": False
                }
        
        return False, None
    
    def generate_status_change_message(self, change_info, order):
        """Generate message highlighting status changes"""
        from_status = change_info["from_status"]
        to_status = change_info["to_status"]
        
        status_messages = {
            ("processing", "shipped"): "Great news! Your order has been shipped",
            ("shipped", "out_for_delivery"): "Your order is now out for delivery",
            ("out_for_delivery", "delivered"): "Excellent! Your order has been delivered",
            ("processing", "out_for_delivery"): "Your order is now out for delivery",
            ("shipped", "delivered"): "Excellent! Your order has been delivered"
        }
        
        change_key = (from_status, to_status)
        if change_key in status_messages:
            base_message = status_messages[change_key]
            return f"🔔 Status Update: {base_message}!"
        else:
            return f"🔔 Status Update: Your order status changed from {from_status} to {to_status}"
    
    def add_realtime_context(self, response, order, session_memory=None):
        """Add real-time messaging context to response"""
        if not order:
            return response
        
        time_since = self.get_time_since_update(order.get("last_updated", ""))
        
        # Check for status changes
        has_changed, change_info = self.detect_status_change(order, session_memory)
        
        if has_changed and change_info["is_progression"]:
            # Highlight positive status changes
            change_message = self.generate_status_change_message(change_info, order)
            response = f"{change_message}\n\n{response}"
        
        # Add timestamp context
        if "last updated" not in response.lower():
            response = f"{response} (Last updated {time_since})"
        else:
            # Replace existing timestamp with more natural language
            response = response.replace(
                f"Last updated {order.get('minutes_since_update', 0)} minutes ago",
                f"Last updated {time_since}"
            )
        
        return response
    
    def update_session_status(self, session_manager, order):
        """Update session with current order status for change detection"""
        if order and session_manager:
            # Store current status in session for future comparison
            from flask import session
            session["last_known_status"] = order.get("shipment_status")
            session["last_status_check"] = datetime.now().isoformat()
    
    def get_delivery_urgency_message(self, order):
        """Generate urgency-based messages for delivery timing"""
        if not order:
            return ""
        
        try:
            expected_delivery = order.get("expected_delivery", "")
            if not expected_delivery:
                return ""
            
            expected = datetime.strptime(expected_delivery, "%Y-%m-%d")
            today = datetime.now()
            days_diff = (expected.date() - today.date()).days
            
            status = order.get("shipment_status", "")
            
            if days_diff == 0 and status in ["shipped", "out_for_delivery"]:
                return "⏰ Arriving today! "
            elif days_diff == 1 and status == "shipped":
                return "📦 Arriving tomorrow! "
            elif days_diff < 0:
                return "⚠️ Delivery was expected earlier. "
            
            return ""
        except:
            return ""
    
    def enhance_response_with_realtime(self, response, order, session_memory=None, session_manager=None):
        """Main method to enhance response with real-time messaging"""
        if not order:
            return response
        
        # Add delivery urgency if applicable
        urgency_message = self.get_delivery_urgency_message(order)
        if urgency_message:
            response = urgency_message + response
        
        # Add real-time context
        enhanced_response = self.add_realtime_context(response, order, session_memory)
        
        # Update session for future change detection
        if session_manager:
            self.update_session_status(session_manager, order)
        
        return enhanced_response