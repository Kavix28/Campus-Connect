# ORDER UPDATE GUIDE
**Oudience Customer Support System**  
**Date:** 2026-01-16  
**Version:** 1.0 & 2.0  

---

## OVERVIEW

There are **3 ways** to update orders in the Oudience system:

1. **Manual Database Update** (v1.0 - Current)
2. **Webhook Automation** (v2.0 - Production Ready)
3. **Admin API Endpoint** (Custom Implementation)

---

## METHOD 1: MANUAL DATABASE UPDATE (v1.0)

### When to Use
- Development/testing environment
- One-time order corrections
- System is running v1.0 (app.py)

### Option A: Direct SQLite Update

#### Step 1: Stop the Server (Optional but Recommended)
```bash
# Press Ctrl+C in the terminal running python app.py
```

#### Step 2: Access Database
```bash
# Using SQLite command line
sqlite3 analytics.db
```

#### Step 3: View Current Orders
```sql
SELECT order_id, shipment_status, tracking_id, expected_delivery 
FROM orders;
```

**Example Output:**
```
AMZ123456789|shipped|TRK789012345|2026-01-11
AMZ987654321|delivered||2026-01-08
AMZ555666777|processing||2026-01-13
ORD-10293|out_for_delivery|TRK123456789|2026-01-10
```

#### Step 4: Update Order Status
```sql
-- Update shipment status
UPDATE orders 
SET shipment_status = 'delivered',
    last_updated = datetime('now')
WHERE order_id = 'AMZ123456789';

-- Add tracking information
UPDATE orders 
SET tracking_id = 'TRK999888777',
    carrier = 'FedEx',
    last_updated = datetime('now')
WHERE order_id = 'AMZ555666777';

-- Update expected delivery date
UPDATE orders 
SET expected_delivery = '2026-01-20',
    last_updated = datetime('now')
WHERE order_id = 'ORD-10293';
```

#### Step 5: Verify Changes
```sql
SELECT * FROM orders WHERE order_id = 'AMZ123456789';
```

#### Step 6: Exit SQLite
```sql
.exit
```

#### Step 7: Restart Server
```bash
python app.py
```

---

### Option B: Using Python Script

Create `update_order.py`:

```python
import sqlite3
from datetime import datetime

def update_order_status(order_id, updates):
    """
    Update order in database
    
    Args:
        order_id: Order ID to update
        updates: Dictionary of fields to update
                 Example: {'shipment_status': 'delivered', 'tracking_id': 'TRK123'}
    """
    conn = sqlite3.connect('analytics.db')
    cursor = conn.cursor()
    
    # Add last_updated timestamp
    updates['last_updated'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Build UPDATE query
    set_clause = ", ".join([f"{k} = ?" for k in updates.keys()])
    values = list(updates.values()) + [order_id]
    
    query = f"UPDATE orders SET {set_clause} WHERE order_id = ?"
    
    cursor.execute(query, values)
    conn.commit()
    
    print(f"✅ Updated order {order_id}")
    print(f"   Changes: {updates}")
    
    conn.close()

# Example Usage
if __name__ == "__main__":
    # Update shipment status
    update_order_status('AMZ123456789', {
        'shipment_status': 'delivered'
    })
    
    # Update multiple fields
    update_order_status('AMZ555666777', {
        'shipment_status': 'shipped',
        'tracking_id': 'TRK999888777',
        'carrier': 'Blue Dart',
        'expected_delivery': '2026-01-18'
    })
    
    # Update payment status
    update_order_status('ORD-10293', {
        'payment_status': 'refunded'
    })
```

**Run the script:**
```bash
python update_order.py
```

---

### Option C: Update via JSON File (Fallback Storage)

If using `orders.json` instead of SQLite:

#### Step 1: Open orders.json
```bash
notepad orders.json  # Windows
nano orders.json     # Linux/Mac
```

#### Step 2: Find and Edit Order
```json
{
  "order_id": "AMZ123456789",
  "email": "john@example.com",
  "phone": "9876543210",
  "items": [
    {"name": "Wireless Headphones", "quantity": 1, "price": 2999},
    {"name": "Phone Case", "quantity": 2, "price": 599}
  ],
  "payment_status": "paid",
  "shipment_status": "delivered",          // ← Change this
  "carrier": "Amazon Logistics",
  "tracking_id": "TRK789012345",
  "expected_delivery": "2026-01-11",
  "last_updated": "2026-01-16 21:45:00"    // ← Update timestamp
}
```

#### Step 3: Save File

#### Step 4: Restart Server
```bash
# Ctrl+C then
python app.py
```

---

## METHOD 2: WEBHOOK AUTOMATION (v2.0 - RECOMMENDED)

### When to Use
- Production environment
- Automatic updates from shipping carriers
- Real-time order status synchronization
- E-commerce platform integration

### Prerequisites
1. System running v2.0 (app_v2.py)
2. .env file configured
3. Webhook API key set

### Setup (One-Time)

#### Step 1: Configure Environment
```bash
# Copy .env.example to .env
copy .env.example .env

# Edit .env file
WEBHOOK_API_KEY=your-secure-api-key-here
WEBHOOK_SECRET_KEY=your-hmac-secret-key
```

#### Step 2: Start v2.0 Server
```bash
python app_v2.py
```

#### Step 3: Get Webhook Configuration
```bash
# Login as admin first, then:
GET http://localhost:5001/api/v1/webhooks/config
```

**Response:**
```json
{
  "order_create": {
    "url": "http://localhost:5001/api/v1/webhooks/order/create",
    "method": "POST",
    "headers": {
      "X-API-Key": "your-secure-api-key-here",
      "Content-Type": "application/json"
    }
  },
  "order_update": {
    "url": "http://localhost:5001/api/v1/webhooks/order/update",
    "method": "POST",
    "headers": {
      "X-API-Key": "your-secure-api-key-here",
      "Content-Type": "application/json"
    }
  }
}
```

---

### Update Order via Webhook

#### Using cURL (Testing)

**Update Shipment Status:**
```bash
curl -X POST http://localhost:5001/api/v1/webhooks/order/update \
  -H "X-API-Key: dev-webhook-key-replace-in-production" \
  -H "Content-Type: application/json" \
  -d '{
    "order_id": "AMZ123456789",
    "status": "delivered",
    "tracking_id": "TRK789012345",
    "carrier": "FedEx",
    "location": "Customer Location",
    "timestamp": "2026-01-16T21:45:00Z",
    "expected_delivery": "2026-01-17"
  }'
```

**Expected Response:**
```json
{
  "success": true,
  "order_id": "AMZ123456789",
  "updates_applied": ["shipment_status", "tracking_id", "carrier", "expected_delivery"],
  "message": "Order updated successfully"
}
```

---

#### Using Python Script

Create `webhook_update_order.py`:

```python
import requests
import json
from datetime import datetime

def update_order_via_webhook(order_id, status, tracking_id=None, carrier=None, expected_delivery=None):
    """
    Update order using webhook endpoint
    
    Args:
        order_id: Order ID to update
        status: New status (processing, shipped, out_for_delivery, delivered)
        tracking_id: Optional tracking number
        carrier: Optional carrier name
        expected_delivery: Optional delivery date (YYYY-MM-DD)
    """
    url = "http://localhost:5001/api/v1/webhooks/order/update"
    
    payload = {
        "order_id": order_id,
        "status": status,
        "timestamp": datetime.now().isoformat() + "Z"
    }
    
    if tracking_id:
        payload["tracking_id"] = tracking_id
    if carrier:
        payload["carrier"] = carrier
    if expected_delivery:
        payload["expected_delivery"] = expected_delivery
    
    headers = {
        "X-API-Key": "dev-webhook-key-replace-in-production",
        "Content-Type": "application/json"
    }
    
    response = requests.post(url, json=payload, headers=headers)
    
    if response.status_code == 200:
        result = response.json()
        if result.get("success"):
            print(f"✅ Order {order_id} updated successfully")
            print(f"   Updates: {result.get('updates_applied')}")
        else:
            print(f"❌ Update failed: {result.get('error')}")
    else:
        print(f"❌ HTTP {response.status_code}: {response.text}")
    
    return response

# Example Usage
if __name__ == "__main__":
    # Update to shipped status
    update_order_via_webhook(
        order_id="AMZ123456789",
        status="shipped",
        tracking_id="TRK999888777",
        carrier="Blue Dart"
    )
    
    # Update to out for delivery
    update_order_via_webhook(
        order_id="AMZ555666777",
        status="out_for_delivery",
        expected_delivery="2026-01-17"
    )
    
    # Update to delivered
    update_order_via_webhook(
        order_id="ORD-10293",
        status="delivered"
    )
```

**Run:**
```bash
python webhook_update_order.py
```

---

### Configure External Services (Production)

For automatic updates from shipping carriers:

#### FedEx Integration
```json
{
  "webhook_url": "https://yourdomain.com/api/v1/webhooks/order/update",
  "events": ["shipment.status_changed", "shipment.delivered"],
  "headers": {
    "X-API-Key": "your-production-api-key"
  }
}
```

#### Blue Dart Integration
```json
{
  "callback_url": "https://yourdomain.com/api/v1/webhooks/order/update",
  "authentication": {
    "type": "api_key",
    "header": "X-API-Key",
    "value": "your-production-api-key"
  }
}
```

---

## METHOD 3: ADMIN API ENDPOINT (Custom)

### Create Custom Update Endpoint

Add to `app_v2.py`:

```python
@app.route("/api/admin/order/update", methods=["POST"])
def admin_update_order():
    """
    Admin endpoint to manually update orders
    Requires authentication
    """
    require_admin()
    
    data = request.json or {}
    order_id = data.get("order_id")
    
    if not order_id:
        return jsonify({"error": "order_id required"}), 400
    
    # Find order
    order = order_service.get_order_by_id(order_id)
    if not order:
        return jsonify({"error": f"Order {order_id} not found"}), 404
    
    # Prepare updates
    updates = {}
    if "shipment_status" in data:
        updates["shipment_status"] = data["shipment_status"]
    if "tracking_id" in data:
        updates["tracking_id"] = data["tracking_id"]
    if "carrier" in data:
        updates["carrier"] = data["carrier"]
    if "expected_delivery" in data:
        updates["expected_delivery"] = data["expected_delivery"]
    if "payment_status" in data:
        updates["payment_status"] = data["payment_status"]
    
    if not updates:
        return jsonify({"error": "No updates provided"}), 400
    
    # Apply updates
    order_service._update_order_status(order_id, updates)
    
    return jsonify({
        "success": True,
        "order_id": order_id,
        "updates": updates
    })
```

### Use Admin Endpoint

```bash
# 1. Login as admin
curl -X POST http://localhost:5001/admin/login \
  -H "Content-Type: application/json" \
  -d '{"token": "admin123"}'

# 2. Update order (with session cookie)
curl -X POST http://localhost:5001/api/admin/order/update \
  -H "Content-Type: application/json" \
  -b cookies.txt \
  -d '{
    "order_id": "AMZ123456789",
    "shipment_status": "delivered",
    "tracking_id": "TRK999888777"
  }'
```

---

## STATUS PROGRESSION GUIDE

### Valid Status Values

**Shipment Status:**
- `processing` - Order confirmed, preparing for shipment
- `shipped` - Package dispatched from warehouse
- `out_for_delivery` - Package with delivery agent
- `delivered` - Package delivered to customer
- `cancelled` - Order cancelled

**Payment Status:**
- `pending` - Payment not confirmed
- `paid` - Payment successful
- `failed` - Payment failed
- `refunded` - Money returned to customer

### Logical Status Flow
```
processing → shipped → out_for_delivery → delivered
    ↓
cancelled (can happen at any stage before delivered)
```

### Status Update Examples

**Order Shipped:**
```json
{
  "shipment_status": "shipped",
  "tracking_id": "TRK123456789",
  "carrier": "FedEx",
  "expected_delivery": "2026-01-18"
}
```

**Out for Delivery:**
```json
{
  "shipment_status": "out_for_delivery",
  "location": "Mumbai Local Hub"
}
```

**Delivered:**
```json
{
  "shipment_status": "delivered",
  "expected_delivery": "2026-01-16"  // Actual delivery date
}
```

**Cancelled:**
```json
{
  "shipment_status": "cancelled",
  "payment_status": "refunded"
}
```

---

## TESTING ORDER UPDATES

### Test Workflow

```bash
# 1. Create test order (v2.0 webhook)
curl -X POST http://localhost:5001/api/v1/webhooks/order/create \
  -H "X-API-Key: dev-webhook-key-replace-in-production" \
  -H "Content-Type: application/json" \
  -d @test_payloads/order_created_example.json

# 2. Verify in chatbot
# Ask: "Track SHOP-2026-12345"
# Should show: Status = processing

# 3. Update to shipped
curl -X POST http://localhost:5001/api/v1/webhooks/order/update \
  -H "X-API-Key: dev-webhook-key-replace-in-production" \
  -H "Content-Type: application/json" \
  -d '{
    "order_id": "SHOP-2026-12345",
    "status": "shipped",
    "tracking_id": "TRK123",
    "carrier": "FedEx"
  }'

# 4. Verify update in chatbot
# Ask: "Track SHOP-2026-12345"
# Should show: Status = shipped, Tracking = TRK123

# 5. Update to delivered
curl -X POST http://localhost:5001/api/v1/webhooks/order/update \
  -H "X-API-Key: dev-webhook-key-replace-in-production" \
  -H "Content-Type: application/json" \
  -d '{
    "order_id": "SHOP-2026-12345",
    "status": "delivered"
  }'

# 6. Final verification
# Ask: "Track SHOP-2026-12345"
# Should show: Status = delivered
```

---

## TROUBLESHOOTING

### Issue: Update Not Reflecting in Chatbot

**Cause:** Server caching or database not refreshed

**Solution:**
```bash
# Clear session
curl -X POST http://localhost:5001/session/clear

# Or restart server
# Ctrl+C then python app.py (or app_v2.py)
```

---

### Issue: Webhook Returns 403 Forbidden

**Cause:** Invalid API key

**Solution:**
```bash
# Check .env file
cat .env | grep WEBHOOK_API_KEY

# Use correct key in header
-H "X-API-Key: your-actual-key-here"
```

---

### Issue: Invalid Status Value

**Cause:** Typo in status name

**Solution:**
Use exact values:
- ✅ `shipped` (lowercase)
- ❌ `Shipped` (incorrect)
- ❌ `SHIPPED` (incorrect)

---

## QUICK REFERENCE

### Manual Update (SQLite)
```sql
UPDATE orders 
SET shipment_status = 'delivered', last_updated = datetime('now') 
WHERE order_id = 'AMZ123456789';
```

### Webhook Update (cURL)
```bash
curl -X POST http://localhost:5001/api/v1/webhooks/order/update \
  -H "X-API-Key: dev-webhook-key-replace-in-production" \
  -H "Content-Type: application/json" \
  -d '{"order_id": "AMZ123", "status": "delivered"}'
```

### Python Script Update
```python
from order_service import OrderService
os = OrderService()
os._update_order_status("AMZ123456789", {"shipment_status": "delivered"})
```

---

## BEST PRACTICES

1. **Always update `last_updated` timestamp**
2. **Use webhooks for production** (automated, auditable)
3. **Validate status transitions** (don't jump from processing → delivered)
4. **Include tracking info** when updating to "shipped"
5. **Log all updates** for audit trail
6. **Test in development** before production updates

---

## SUMMARY

| Method | v1.0 | v2.0 | Best For |
|--------|------|------|----------|
| Manual SQL | ✅ | ✅ | Development, one-off fixes |
| Python Script | ✅ | ✅ | Batch updates |
| Webhook API | ❌ | ✅ | Production, automation |
| Admin Endpoint | ❌ | Custom | Admin dashboard integration |

**Recommended:** Use **Webhooks (v2.0)** for production, **Manual SQL** for development.

---

**Last Updated:** 2026-01-16  
**Version:** 1.0  

**END OF GUIDE**
