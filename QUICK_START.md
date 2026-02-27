# QUICK START GUIDE
## Amazon-Style Customer Support System v2.0

**Get up and running in 5 minutes!**

---

## Prerequisites

- Python 3.9+
- pip (Python package manager)
- Terminal/Command Prompt

---

## Step-by-Step Setup

### 1. Install Dependencies

```bash
pip install -r requirements_v2.txt
```

**Wait for installation to complete** (~2-3 minutes)

### 2. Create Environment File

```bash
# Copy the example environment file
cp .env.example .env

# On Windows:
copy .env.example .env
```

**The default values work for local testing!** No need to edit for now.

### 3. Start the Application

```bash
python app_v2.py
```

**Expected output:**
```
🚀 Oudience 2.0 running at http://127.0.0.1:5001
📦 Environment: development
🔐 Webhooks: Enabled
```

### 4. Test It Works

**Open your browser:**
- Chat Interface: http://localhost:5001
- Admin Panel: http://localhost:5001/admin

**Or test with curl:**
```bash
curl http://localhost:5001/health
```

**Expected:** `{"status": "healthy", ...}`

---

## Test Webhook Integration

### Option A: Automated Test (Recommended)

```bash
# In a NEW terminal (keep app running in first terminal)
python test_webhook_integration.py
```

**Expected:** 6/6 tests passed ✅

### Option B: Manual Test with curl

```bash
# Create an order via webhook
curl -X POST http://localhost:5001/api/v1/webhooks/order/create \
  -H "X-API-Key: dev-webhook-key-replace-in-production" \
  -H "Content-Type: application/json" \
  -d @testpayloads/order_created_example.json

# Check if chatbot can find it
curl -X POST http://localhost:5001/query \
  -H "Content-Type: application/json" \
  -d '{"query": "Track SHOP-2026-12345"}'
```

**Expected:** Chatbot responds with order details!

---

## Quick Feature Tour

### 1. Chat with the Bot

**Open:** http://localhost:5001

**Try these queries:**
- "Track AMZ123456789"
- "9876543210" (phone number)
- "Where is my order?"
- "What is your return policy?"

### 2. Create Order via Webhook

```bash
curl -X POST http://localhost:5001/api/v1/webhooks/order/create \
  -H "X-API-Key: dev-webhook-key-replace-in-production" \
  -H "Content-Type: application/json" \
  -d '{
    "order_id": "MY-TEST-001",
    "customer": {
      "email": "test@example.com",
      "phone": "1234567890",
      "name": "Test User"
    },
    "items": [
      {
        "name": "Test Product",
        "quantity": 1,
        "price": 999.00
      }
    ],
    "totals": {
      "total": 999.00
    },
    "payment": {
      "status": "completed"
    }
  }'
```

**Then ask chatbot:** "Track MY-TEST-001"

### 3. Update Order Status

```bash
curl -X POST http://localhost:5001/api/v1/webhooks/order/update \
  -H "X-API-Key: dev-webhook-key-replace-in-production" \
  -H "Content-Type: application/json" \
  -d '{
    "order_id": "MY-TEST-001",
    "status": "shipped",
    "tracking_id": "TRK123456",
    "carrier": "FedEx"
  }'
```

**Chatbot will show updated status!**

---

## What's Different from v1.0?

### New Features

✅ **Automated Order Ingestion**  
Orders automatically created via webhooks (no manual database insertion)

✅ **User Accounts**  
Users automatically created and linked to their orders

✅ **Persistent Order History**  
Users can view all their orders across sessions

✅ **Webhook Endpoints**  
`/api/v1/webhooks/order/create` - Create orders  
`/api/v1/webhooks/order/update` - Update status  
`/api/v1/webhooks/payment/confirm` - Payment updates

✅ **Environment Configuration**  
All settings in `.env` file (NO hardcoded secrets)

✅ **Production-Ready**  
PostgreSQL support, security, logging, health checks

### Still Works (Backward Compatible)

✅ All existing chatbot features  
✅ All 9 intent types  
✅ Order lookup by ID/email/phone  
✅ Session management  
✅ RAG knowledge base  
✅ Admin panel  

**Nothing was broken!**

---

## Project Structure

```
├── app_v2.py                    ← NEW: Production app
├── user_service.py               ← NEW: User management
├── webhook_service.py            ← NEW: Webhook automation
├── order_service.py              ← ENHANCED: Added create_order()
├── intent_handler.py             ← Same as before
├── .env.example                  ← NEW: Environment template
├── requirements_v2.txt           ← UPDATED: New dependencies
│
├── PRODUCTION_ARCHITECTURE.md    ← Complete system design
├── DEPLOYMENT_GUIDE.md           ← Deployment instructions
├── UPGRADE_SUMMARY.md            ← What changed & why
├── QUICK_START.md                ← This file
│
├── test_webhook_integration.py  ← Automated tests
├── test_payloads/                ← Example webhook payloads
    ├── order_created_example.json
    └── order_update_example.json
```

---

## Next Steps

### For Local Development

1. **Read the docs:**
   - `UPGRADE_SUMMARY.md` - Overview of changes
   - `PRODUCTION_ARCHITECTURE.md` - System design

2. **Explore the code:**
   - `app_v2.py` - Main application
   - `webhook_service.py` - Automation logic
   - `user_service.py` - User management

3. **Customize:**
   - Edit `.env` for your settings
   - Add your e-commerce webhook URLs
   - Test with your order data

### For Production Deployment

1. **Follow the guide:**
   - Read `DEPLOYMENT_GUIDE.md` completely
   - Setup PostgreSQL database
   - Configure production `.env`

2. **Security:**
   - Generate secure `SECRET_KEY`
   - Change `WEBHOOK_API_KEY`
   - Setup HTTPS with SSL

3. **External Services:**
   - Configure your e-commerce platform webhooks
   - Point to `https://yourdomain.com/api/v1/webhooks/order/create`
   - Add your API key in webhook headers

---

## Troubleshooting

### Server won't start

**Check:**
- Python version: `python --version` (need 3.9+)
- Dependencies installed: `pip list | grep flask`
- Port 5001 available: Try different port in `.env`

### Webhook returns 403 Forbidden

**Check:**
- API key matches `.env` setting
- Header is `X-API-Key` (case-sensitive)
- Default: `dev-webhook-key-replace-in-production`

### Order not appearing in chatbot

**Check:**
- Webhook returned `{"success": true}`
- Order ID in payload matches chatbot query
- Check logs: `tail -f logs/webhooks.log`

### Database errors

**Solution:**
- Delete `analytics.db` (will recreate with new schema)
- Or migrate manually (see DEPLOYMENT_GUIDE.md)

---

## Support

- **Documentation:** See `PRODUCTION_ARCHITECTURE.md` and `DEPLOYMENT_GUIDE.md`
- **Examples:** Check `test_payloads/` directory
- **Logs:** Check `logs/` directory for debugging

---

## Success Criteria

You'll know it's working when:

✅ Server starts without errors  
✅ Chat interface loads in browser  
✅ Webhook test passes (all 6 tests)  
✅ Orders created via webhook appear in chatbot immediately  
✅ Bot can track orders by ID, email, or phone  

**If all above pass, you're ready for production deployment!**

---

**Version:** 2.0  
**Last Updated:** 2026-01-16  

🚀 **Happy Building!**
