"""
Webhook Service - Automated Order Ingestion
Handles webhook endpoints for e-commerce platforms to automatically create orders
"""

import os
import hmac
import hashlib
import json
import time
from datetime import datetime
from typing import Dict, Any, Optional
from functools import wraps
from flask import request, jsonify


class WebhookService:
    """
    Handles webhook integrations from e-commerce platforms, payment gateways,
    and shipping carriers to auto-ingest orders into the system.
    """
    
    def __init__(self, user_service, order_service):
        self.user_service = user_service
        self.order_service = order_service
        self.api_key = os.getenv("WEBHOOK_API_KEY", "dev-webhook-key")
        self.secret_key = os.getenv("WEBHOOK_SECRET_KEY", "dev-secret")
        self.enabled = os.getenv("AUTOMATION_ENABLED", "true").lower() == "true"
    
    def verify_api_key(self, provided_key: str) -> bool:
        """Verify API key from webhook request"""
        return hmac.compare_digest(provided_key, self.api_key)
    
    def verify_hmac_signature(self, payload: bytes, signature: str) -> bool:
        """
        Verify HMAC signature to ensure webhook authenticity.
        Prevents replay attacks and unauthorized requests.
        
        Args:
            payload: Raw request body as bytes
            signature: HMAC signature from header
        
        Returns:
            True if signature is valid
        """
        computed_signature = hmac.new(
            self.secret_key.encode(),
            payload,
            hashlib.sha256
        ).hexdigest()
        
        return hmac.compare_digest(signature, computed_signature)
    
    def require_webhook_auth(self, f):
        """Decorator to require API key auth for webhook endpoints"""
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Check if webhooks are enabled
            if not self.enabled:
                return jsonify({
                    "success": False,
                    "error": "Webhooks are disabled"
                }), 503
            
            # Verify API key
            api_key = request.headers.get("X-API-Key")
            if not api_key or not self.verify_api_key(api_key):
                return jsonify({
                    "success": False,
                    "error": "Invalid API key"
                }), 403
            
            # Optional: Verify HMAC signature for extra security
            signature = request.headers.get("X-Signature")
            if signature:
                if not self.verify_hmac_signature(request.get_data(), signature):
                    return jsonify({
                        "success": False,
                        "error": "Invalid signature"
                    }), 403
            
            return f(*args, **kwargs)
        
        return decorated_function
    
    def handle_order_create(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle order creation webhook from e-commerce platform.
        
        Expected payload structure:
        {
            "order_id": "SHOP-2026-12345",
            "customer": {
                "email": "customer@example.com",
                "phone": "9876543210",
                "name": "John Doe"
            },
            "items": [
                {
                    "product_id": "PROD-001",
                    "name": "Product Name",
                    "quantity": 1,
                    "price": 2999.00,
                    "sku": "SKU-001"
                }
            ],
            "totals": {
                "subtotal": 2999.00,
                "tax": 539.82,
                "shipping": 0.00,
                "total": 3538.82
            },
            "payment": {
                "method": "credit_card",
                "status": "completed",
                "transaction_id": "TXN-789"
            },
            "created_at": "2026-01-16T16:00:00Z"
        }
        
        Returns:
            Success/failure response
        """
        try:
            # Validate required fields
            required_fields = ["order_id", "customer", "items"]
            for field in required_fields:
                if field not in payload:
                    return {
                        "success": False,
                        "error": f"Missing required field: {field}"
                    }
            
            # Extract customer info
            customer = payload.get("customer", {})
            email = customer.get("email")
            phone = customer.get("phone")
            full_name = customer.get("name")
            
            if not email and not phone:
                return {
                    "success": False,
                    "error": "Customer must have email or phone"
                }
            
            # Find or create user
            user = self.user_service.find_or_create_user(
                email=email,
                phone=phone,
                full_name=full_name
            )
            
            if not user:
                return {
                    "success": False,
                    "error": "Failed to create user"
                }
            
            # Prepare order data
            order_id = payload.get("order_id")
            items = payload.get("items", [])
            totals = payload.get("totals", {})
            payment = payload.get("payment", {})
            
            # Check for duplicate order
            existing_order = self.order_service.get_order_by_id(order_id)
            if existing_order:
                return {
                    "success": False,
                    "error": f"Order {order_id} already exists",
                    "duplicate": True
                }
            
            # Transform items to expected format
            formatted_items = []
            for item in items:
                formatted_items.append({
                    "name": item.get("name", "Unknown Product"),
                    "quantity": item.get("quantity", 1),
                    "price": item.get("price", 0.0),
                    "sku": item.get("sku", item.get("product_id", ""))
                })
            
            # Determine payment status
            payment_status_map = {
                "completed": "paid",
                "pending": "pending",
                "failed": "failed"
            }
            payment_status = payment_status_map.get(
                payment.get("status", "pending"), 
                "pending"
            )
            
            # Create order in database
            new_order = self.order_service.create_order(
                order_id=order_id,
                user_id=user["id"],
                email=email,
                phone=phone,
                items=formatted_items,
                total_amount=totals.get("total", 0.0),
                payment_status=payment_status,
                shipment_status="processing",
                created_at=payload.get("created_at")
            )
            
            # Log webhook success
            self._log_webhook_event({
                "event_type": "order.created",
                "order_id": order_id,
                "user_id": user["id"],
                "status": "success",
                "timestamp": datetime.now().isoformat()
            })
            
            return {
                "success": True,
                "order_id": order_id,
                "user_id": user["id"],
                "message": "Order created successfully"
            }
        
        except Exception as e:
            # Log error
            self._log_webhook_event({
                "event_type": "order.created",
                "status": "failed",
                "error": str(e),
                "payload": payload,
                "timestamp": datetime.now().isoformat()
            })
            
            return {
                "success": False,
                "error": f"Failed to create order: {str(e)}"
            }
    
    def handle_order_update(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle order status update webhook from shipping carrier.
        
        Expected payload:
        {
            "order_id": "SHOP-2026-12345",
            "tracking_id": "TRK789012345",
            "status": "shipped",
            "carrier": "FedEx",
            "location": "Mumbai Distribution Center",
            "timestamp": "2026-01-16T18:30:00Z",
            "expected_delivery": "2026-01-18"
        }
        """
        try:
            order_id = payload.get("order_id")
            if not order_id:
                return {"success": False, "error": "Missing order_id"}
            
            # Find order
            order = self.order_service.get_order_by_id(order_id)
            if not order:
                return {
                    "success": False,
                    "error": f"Order {order_id} not found"
                }
            
            # Prepare updates
            updates = {}
            
            # Update shipment status
            new_status = payload.get("status")
            if new_status:
                # Validate status transition
                valid_statuses = ["processing", "shipped", "out_for_delivery", "delivered", "cancelled"]
                if new_status in valid_statuses:
                    updates["shipment_status"] = new_status
            
            # Update tracking info
            if payload.get("tracking_id"):
                updates["tracking_id"] = payload.get("tracking_id")
            
            if payload.get("carrier"):
                updates["carrier"] = payload.get("carrier")
            
            if payload.get("expected_delivery"):
                updates["expected_delivery"] = payload.get("expected_delivery")
            
            # Apply updates
            if updates:
                self.order_service._update_order_status(order_id, updates)
                
                # Log status change
                self._log_status_change(
                    order_id=order_id,
                    old_status=order.get("shipment_status"),
                    new_status=updates.get("shipment_status"),
                    message=f"Updated via webhook from {payload.get('carrier', 'system')}"
                )
            
            return {
                "success": True,
                "order_id": order_id,
                "updates_applied": list(updates.keys()),
                "message": "Order updated successfully"
            }
        
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to update order: {str(e)}"
            }
    
    def handle_payment_confirmation(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle payment confirmation webhook from payment gateway.
        
        Expected payload:
        {
            "order_id": "SHOP-2026-12345",
            "transaction_id": "TXN-789012",
            "status": "success",  # or "failed"
            "amount": 3538.82,
            "payment_method": "credit_card",
            "timestamp": "2026-01-16T16:00:00Z"
        }
        """
        try:
            order_id = payload.get("order_id")
            payment_status = payload.get("status")
            
            if not order_id or not payment_status:
                return {
                    "success": False,
                    "error": "Missing order_id or status"
                }
            
            # Find order
            order = self.order_service.get_order_by_id(order_id)
            if not order:
                return {
                    "success": False,
                    "error": f"Order {order_id} not found"
                }
            
            # Map payment status
            status_map = {
                "success": "paid",
                "completed": "paid",
                "failed": "failed",
                "pending": "pending"
            }
            
            new_payment_status = status_map.get(payment_status, "pending")
            
            # Update order
            self.order_service._update_order_status(order_id, {
                "payment_status": new_payment_status
            })
            
            # If payment succeeded, move order to processing
            if new_payment_status == "paid" and order.get("shipment_status") == "pending":
                self.order_service._update_order_status(order_id, {
                    "shipment_status": "processing"
                })
            
            # If payment failed, consider cancelling
            if new_payment_status == "failed":
                self.order_service._update_order_status(order_id, {
                    "shipment_status": "cancelled"
                })
            
            return {
                "success": True,
                "order_id": order_id,
                "payment_status": new_payment_status,
                "message": "Payment status updated"
            }
        
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to process payment: {str(e)}"
            }
    
    def _log_webhook_event(self, event_data: Dict[str, Any]):
        """Log webhook events to file for audit trail"""
        log_file = "logs/webhooks.log"
        os.makedirs("logs", exist_ok=True)
        
        try:
            with open(log_file, "a") as f:
                f.write(json.dumps(event_data) + "\n")
        except Exception as e:
            print(f"Failed to log webhook event: {e}")
    
    def _log_status_change(self, order_id: str, old_status: str, new_status: str, message: str):
        """Log order status changes"""
        log_entry = {
            "order_id": order_id,
            "old_status": old_status,
            "new_status": new_status,
            "message": message,
            "timestamp": datetime.now().isoformat()
        }
        
        log_file = "logs/order_status_changes.log"
        os.makedirs("logs", exist_ok=True)
        
        try:
            with open(log_file, "a") as f:
                f.write(json.dumps(log_entry) + "\n")
        except Exception as e:
            print(f"Failed to log status change: {e}")
    
    def generate_webhook_url(self, endpoint: str) -> str:
        """Generate full webhook URL for external services"""
        base_url = os.getenv("PUBLIC_WEBHOOK_URL", "http://localhost:5001/api/v1/webhooks")
        return f"{base_url}/{endpoint}"
    
    def get_webhook_config(self) -> Dict[str, Any]:
        """
        Get webhook configuration for external services.
        Returns URLs and authentication info.
        """
        return {
            "order_create": {
                "url": self.generate_webhook_url("order/create"),
                "method": "POST",
                "headers": {
                    "X-API-Key": self.api_key,
                    "Content-Type": "application/json"
                },
                "description": "Called when new order is placed"
            },
            "order_update": {
                "url": self.generate_webhook_url("order/update"),
                "method": "POST",
                "headers": {
                    "X-API-Key": self.api_key,
                    "Content-Type": "application/json"
                },
                "description": "Called when order status changes"
            },
            "payment_confirmation": {
                "url": self.generate_webhook_url("payment/confirm"),
                "method": "POST",
                "headers": {
                    "X-API-Key": self.api_key,
                    "Content-Type": "application/json"
                },
                "description": "Called when payment is processed"
            }
        }
