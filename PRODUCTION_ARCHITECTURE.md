# PRODUCTION ARCHITECTURE
## Amazon-Style Customer Support System

**Version:** 2.0  
**Date:** 2026-01-16  
**Status:** Production-Ready  

---

## EXECUTIVE SUMMARY

This document describes the production-ready architecture upgrade that transforms the Oudience chatbot into an Amazon-style automated customer support system with:

✅ **Automated Order Ingestion** - Orders automatically enter the system  
✅ **Event-Driven Workflows** - n8n-style automation for order lifecycle  
✅ **Production-Grade Security** - Environment-based config, JWT auth, encryption  
✅ **Scalable Data Layer** - PostgreSQL/MySQL support with migration path  
✅ **User-Persistent Sessions** - User mapping with order history  
✅ **AI Safety Boundaries** - Strict separation of AI and business logic  

---

## SYSTEM ARCHITECTURE OVERVIEW

```
┌──────────────────────────────────────────────────────────────────────┐
│                   PRODUCTION ARCHITECTURE                             │
├──────────────────────────────────────────────────────────────────────┤
│                                                                       │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │              EXTERNAL SYSTEMS & TRIGGERS                        │ │
│  ├────────────────────────────────────────────────────────────────┤ │
│  │  • Ecommerce Platform (Shopify/WooCommerce/Custom)            │ │
│  │  • Payment Gateway (Stripe/Razorpay)                          │ │
│  │  • Shipping Carriers (FedEx/DHL/Amazon Logistics)             │ │
│  │  • Email/SMS Notification Services                            │ │
│  └────────────────────────────────────────────────────────────────┘ │
│                          ↓ Webhooks/APIs                              │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │              AUTOMATION LAYER (n8n-style)                      │ │
│  ├────────────────────────────────────────────────────────────────┤ │
│  │  Workflow Engine:                                              │ │
│  │  • Order Ingestion Workflow                                   │ │
│  │  • Order Status Update Workflow                               │ │
│  │  • Payment Verification Workflow                              │ │
│  │  • Shipping Notification Workflow                             │ │
│  │  • Retry & Error Handling                                     │ │
│  └────────────────────────────────────────────────────────────────┘ │
│                          ↓ REST API                                   │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │              APPLICATION LAYER (Flask)                         │ │
│  ├────────────────────────────────────────────────────────────────┤ │
│  │  Public Endpoints:                                             │ │
│  │  • POST /api/v1/chat/query       → Chatbot interaction       │ │
│  │  • POST /api/v1/auth/register    → User registration         │ │
│  │  • POST /api/v1/auth/login       → User authentication       │ │
│  │  • GET  /api/v1/orders/history   → User order history        │ │
│  │                                                                │ │
│  │  Automation Endpoints (API Key Auth):                          │ │
│  │  • POST /api/v1/webhooks/order/create   → New order intake   │ │
│  │  • POST /api/v1/webhooks/order/update   → Status updates     │ │
│  │  • POST /api/v1/webhooks/payment/confirm → Payment events    │ │
│  │  • POST /api/v1/webhooks/shipping/track  → Tracking updates  │ │
│  │                                                                │ │
│  │  Admin Endpoints (JWT Auth):                                   │ │
│  │  • POST /api/v1/admin/login      → Admin authentication      │ │
│  │  • POST /api/v1/admin/kb/upload  → Knowledge base upload     │ │
│  │  • GET  /api/v1/admin/analytics  → System analytics          │ │
│  └────────────────────────────────────────────────────────────────┘ │
│                          ↓                                            │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │              BUSINESS LOGIC LAYER                              │ │
│  ├────────────────────────────────────────────────────────────────┤ │
│  │  • UserService         → User management & authentication     │ │
│  │  • OrderService        → Order CRUD & lifecycle management    │ │
│  │  • IntentHandler       → Intent detection & routing           │ │
│  │  • WorkflowService     → Automation workflow execution        │ │
│  │  • NotificationService → Email/SMS notifications              │ │
│  │  • AnalyticsService    → Metrics & reporting                  │ │
│  │  • SecurityService     → Encryption, validation, rate limiting│ │
│  └────────────────────────────────────────────────────────────────┘ │
│                          ↓                                            │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │              DATA LAYER                                        │ │
│  ├────────────────────────────────────────────────────────────────┤ │
│  │  Database (PostgreSQL/MySQL):                                  │ │
│  │  • users               → User accounts & profiles             │ │
│  │  • orders              → Order data & history                 │ │
│  │  • order_items         → Order line items                     │ │
│  │  • order_status_log    → Status change audit trail            │ │
│  │  • user_sessions       → Active sessions with JWT             │ │
│  │  • knowledge_base      → RAG document chunks                  │ │
│  │  • workflow_logs       → Automation execution logs            │ │
│  │  • api_keys            → Webhook authentication               │ │
│  │                                                                │ │
│  │  Cache Layer (Redis - Optional):                               │ │
│  │  • Session data        → Fast session lookup                  │ │
│  │  • Rate limiting       → API throttling                       │ │
│  │  • Embeddings cache    → RAG performance                      │ │
│  └────────────────────────────────────────────────────────────────┘ │
│                                                                       │
└──────────────────────────────────────────────────────────────────────┘
```

---

## ORDER LIFECYCLE AUTOMATION

### How Orders Enter the System

**Method 1: E-commerce Webhook (Recommended)**

```
Customer Places Order → E-commerce Platform → Webhook Trigger →
Automation Workflow → Database Insertion → Order Available for Chatbot
```

**Method 2: API Integration**

```
E-commerce System → Direct API Call → POST /api/v1/webhooks/order/create →
Validation → Database Insertion → Confirmation Response
```

**Method 3: Batch Import (Legacy Systems)**

```
CSV/JSON Export → Upload via Admin Panel → Batch Processing →
Database Insertion → Import Report
```

### Order Creation Flow (Detailed)

```
┌─────────────────────────────────────────────────────────────────┐
│ STEP 1: ORDER PLACED ON E-COMMERCE PLATFORM                    │
├─────────────────────────────────────────────────────────────────┤
│ Customer completes checkout                                     │
│ Payment processed successfully                                  │
│ E-commerce system generates order ID: ORD-2026123456           │
└─────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│ STEP 2: WEBHOOK TRIGGER                                        │
├─────────────────────────────────────────────────────────────────┤
│ E-commerce platform sends POST request:                        │
│ URL: https://yourdomain.com/api/v1/webhooks/order/create      │
│ Headers: { "X-API-Key": "secure_webhook_key" }                │
│ Body: {                                                        │
│   "order_id": "ORD-2026123456",                               │
│   "user_email": "customer@example.com",                       │
│   "user_phone": "9876543210",                                 │
│   "items": [...],                                             │
│   "total_amount": 5999,                                       │
│   "payment_status": "completed",                              │
│   "created_at": "2026-01-16T16:00:00Z"                        │
│ }                                                              │
└─────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│ STEP 3: WEBHOOK AUTHENTICATION                                 │
├─────────────────────────────────────────────────────────────────┤
│ Validate API key from headers                                  │
│ Check request signature (HMAC)                                 │
│ Verify request timestamp (prevent replay attacks)              │
│ Rate limit check (max 100 requests/min per API key)           │
└─────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│ STEP 4: DATA VALIDATION                                        │
├─────────────────────────────────────────────────────────────────┤
│ Required fields present? → order_id, email/phone, items       │
│ Order ID format valid? → Regex validation                     │
│ Email format valid? → RFC 5322 compliant                      │
│ Phone format valid? → 10 digits, country code optional        │
│ Duplicate order check → Query database for existing order_id  │
└─────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│ STEP 5: USER LOOKUP/CREATION                                   │
├─────────────────────────────────────────────────────────────────┤
│ Search for existing user by email or phone                     │
│ If user exists:                                                │
│   → Link order to existing user_id                            │
│ If user doesn't exist:                                         │
│   → Create new user record                                    │
│   → Generate user_id                                          │
│   → Store email, phone, name (if provided)                    │
│   → Set created_at timestamp                                  │
└─────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│ STEP 6: DATABASE TRANSACTION                                   │
├─────────────────────────────────────────────────────────────────┤
│ BEGIN TRANSACTION;                                             │
│                                                                │
│ INSERT INTO orders (                                           │
│   order_id, user_id, total_amount, payment_status,           │
│   shipment_status, carrier, tracking_id,                      │
│   expected_delivery, created_at, last_updated                 │
│ ) VALUES (...);                                                │
│                                                                │
│ INSERT INTO order_items (                                      │
│   order_id, product_name, quantity, price                     │
│ ) VALUES (...);  -- For each item                             │
│                                                                │
│ INSERT INTO order_status_log (                                 │
│   order_id, status, message, created_at                       │
│ ) VALUES (                                                     │
│   'ORD-2026123456', 'processing',                            │
│   'Order received and being processed', NOW()                 │
│ );                                                             │
│                                                                │
│ COMMIT;                                                        │
└─────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│ STEP 7: POST-INSERTION WORKFLOWS                               │
├─────────────────────────────────────────────────────────────────┤
│ Trigger welcome email workflow                                 │
│ Log order creation event                                       │
│ Update analytics counters                                      │
│ Clear relevant caches                                          │
│ Return success response to webhook caller                      │
└─────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│ STEP 8: ORDER NOW AVAILABLE                                    │
├─────────────────────────────────────────────────────────────────┤
│ Customer can immediately ask chatbot:                          │
│ "Track my order" or "Where is ORD-2026123456?"               │
│                                                                │
│ Chatbot looks up order by:                                     │
│ • Order ID (ORD-2026123456)                                   │
│ • User email (customer@example.com)                           │
│ • User phone (9876543210)                                     │
│                                                                │
│ Response includes:                                             │
│ • Current status (processing)                                 │
│ • Payment confirmation                                         │
│ • Expected delivery date                                       │
│ • Order timeline                                              │
└─────────────────────────────────────────────────────────────────┘
```

### Order Status Update Flow

```
┌─────────────────────────────────────────────────────────────────┐
│ TRIGGER: Shipping carrier provides tracking update             │
├─────────────────────────────────────────────────────────────────┤
│ Carrier Webhook → POST /api/v1/webhooks/shipping/track        │
│ Body: {                                                        │
│   "order_id": "ORD-2026123456",                               │
│   "tracking_id": "TRK789012345",                              │
│   "status": "shipped",                                         │
│   "carrier": "FedEx",                                          │
│   "location": "Mumbai Distribution Center",                    │
│   "timestamp": "2026-01-16T18:30:00Z"                         │
│ }                                                              │
└─────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│ PROCESSING                                                     │
├─────────────────────────────────────────────────────────────────┤
│ 1. Validate webhook authentication                             │
│ 2. Find order in database                                      │
│ 3. Update shipment_status to 'shipped'                        │
│ 4. Update tracking_id and carrier                             │
│ 5. Update last_updated timestamp                              │
│ 6. Log status change in order_status_log                      │
│ 7. Trigger notification workflow (email/SMS)                   │
│ 8. Update expected_delivery if carrier provides ETA           │
└─────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│ CUSTOMER INTERACTION                                           │
├─────────────────────────────────────────────────────────────────┤
│ Customer: "Where is my order?"                                 │
│ Chatbot: "Great news! Your order ORD-2026123456 has been     │
│ shipped via FedEx (Tracking: TRK789012345). It's currently   │
│ at Mumbai Distribution Center. Expected delivery: Jan 18,     │
│ 2026. Last updated 5 minutes ago."                            │
└─────────────────────────────────────────────────────────────────┘
```

---

## AUTOMATION LAYER DESIGN

### n8n-Style Workflow Architecture

We use an event-driven workflow system similar to n8n/Zapier:

**Workflow Components:**

1. **Trigger Nodes** - Events that start workflows
2. **Action Nodes** - Operations performed  
3. **Condition Nodes** - Decision points
4. **Integration Nodes** - External service calls

### Workflow 1: Order Ingestion Workflow

```yaml
workflow_name: "Order Ingestion"
trigger: "Webhook: POST /api/v1/webhooks/order/create"
description: "Automates new order creation from e-commerce platform"

nodes:
  - id: "trigger_1"
    type: "webhook_trigger"
    config:
      path: "/api/v1/webhooks/order/create"
      auth_type: "api_key"
      
  - id: "validate_1"
    type: "validation"
    parents: ["trigger_1"]
    config:
      required_fields: ["order_id", "user_email", "items"]
      schemas:
        order_id: "regex:^(AMZ|ORD)-[0-9]+$"
        user_email: "email"
        user_phone: "phone_10digit"
    on_error: "reject_with_400"
    
  - id: "check_duplicate_1"
    type: "database_query"
    parents: ["validate_1"]
    query: "SELECT id FROM orders WHERE order_id = :order_id"
    on_result:
      exists: "reject_duplicate"
      not_exists: "continue"
      
  - id: "find_user_1"
    type: "database_query"
    parents: ["check_duplicate_1"]
    query: "SELECT id FROM users WHERE email = :email OR phone = :phone"
    
  - id: "create_user_if_needed"
    type: "conditional_insert"
    parents: ["find_user_1"]
    condition: "user_not_found"
    query: "INSERT INTO users (email, phone, created_at) VALUES (...)"
    
  - id: "insert_order_1"
    type: "database_transaction"
    parents: ["create_user_if_needed"]
    operations:
      - "INSERT INTO orders (...) VALUES (...)"
      - "INSERT INTO order_items (...) VALUES (...)"
      - "INSERT INTO order_status_log (...) VALUES (...)"
    on_error: "rollback_and_reject"
    
  - id: "send_confirmation_email"
    type: "email_notification"
    parents: ["insert_order_1"]
    template: "order_confirmation"
    to: "{{user_email}}"
    async: true  # Don't wait for email to complete
    
  - id: "log_analytics_1"
    type: "analytics_event"
    parents: ["insert_order_1"]
    event_name: "order_created"
    properties:
      order_id: "{{order_id}}"
      amount: "{{total_amount}}"
      source: "webhook"
      
  - id: "respond_success"
    type: "webhook_response"
    parents: ["insert_order_1"]
    status: 200
    body:
      success: true
      order_id: "{{order_id}}"
      message: "Order created successfully"

retry_policy:
  max_attempts: 3
  backoff: "exponential"
  retry_on: ["database_timeout", "network_error"]
  
error_handling:
  log_failures: true
  notify_admin: true  # On critical failures
  fallback_response:
    status: 500
    body:
      success: false
      message: "Order processing failed. Please try again."
```

### Workflow 2: Order Status Update Workflow

```yaml
workflow_name: "Order Status Update"
trigger: "Webhook: POST /api/v1/webhooks/order/update"

nodes:
  - id: "trigger_update"
    type: "webhook_trigger"
    
  - id: "find_order"
    type: "database_query"
    query: "SELECT * FROM orders WHERE order_id = :order_id"
    on_error: "order_not_found"
    
  - id: "validate_status_transition"
    type: "business_logic"
    validation:
      allowed_transitions:
        processing: ["shipped", "cancelled"]
        shipped: ["out_for_delivery", "delivered"]
        out_for_delivery: ["delivered"]
      deny_transitions:
        delivered: "*"  # Cannot change from delivered
        
  - id: "update_order_status"
    type: "database_update"
    query: "UPDATE orders SET shipment_status = :new_status, last_updated = NOW()"
    
  - id: "log_status_change"
    type: "database_insert"
    query: "INSERT INTO order_status_log (order_id, old_status, new_status, changed_at)"
    
  - id: "notify_customer"
   type: "conditional_notification"
    conditions:
      - if: "status == 'shipped'"
        action: "send_email"
        template: "order_shipped"
      - if: "status == 'delivered'"
        action: "send_email"
        template: "order_delivered"
        
  - id: "update_expected_delivery"
    type: "conditional_update"
    condition: "carrier_eta_provided"
    query: "UPDATE orders SET expected_delivery = :carrier_eta"

retry_policy:
  max_attempts: 5
  backoff: "exponential"
```

### Workflow 3: Payment Verification Workflow

```yaml
workflow_name: "Payment Verification"
trigger: "Webhook: POST /api/v1/webhooks/payment/confirm"

nodes:
  - id: "trigger_payment"
    type: "webhook_trigger"
    
  - id: "verify_signature"
    type: "security_validation"
    validation_type: "hmac_sha256"
    secret: "{{env.PAYMENT_WEBHOOK_SECRET}}"
    
  - id: "find_order"
    type: "database_query"
    query: "SELECT * FROM orders WHERE order_id = :order_id"
    
  - id: "update_payment_status"
    type: "database_update"
    query: "UPDATE orders SET payment_status = :status"
    
  - id: "conditional_processing"
    type: "condition_branching"
    branches:
      - condition: "payment_status == 'success'"
        actions:
          - start_order_processing
          - send_confirmation_email
      - condition: "payment_status == 'failed'"
        actions:
          - mark_order_cancelled
          - send_failure_email
          - refund_if_charged
```

---

## USER-TO-ORDER MAPPING

### User Management System

**User Entity:**

```sql
CREATE TABLE users (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    email VARCHAR(255) UNIQUE NOT NULL,
    phone VARCHAR(20) UNIQUE,
    full_name VARCHAR(255),
    password_hash VARCHAR(255),  -- For registered users
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP,
    INDEX idx_email (email),
    INDEX idx_phone (phone)
);
```

**Session Persistence:**

```sql
CREATE TABLE user_sessions (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    user_id BIGINT NOT NULL,
    session_token VARCHAR(512) UNIQUE NOT NULL,
    jwt_token TEXT,
    active_order_id VARCHAR(50),
    last_intent VARCHAR(50),
    conversation_summary TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP NOT NULL,
    last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id),
    INDEX idx_session_token (session_token),
    INDEX idx_user_id (user_id),
    INDEX idx_expires_at (expires_at)
);
```

### Amazon-Style Continuity

**Scenario: Customer returns after 2 weeks**

```
1. Customer visits chatbot
2. Frontend sends session token (stored in cookie)
3. Backend validates session token
4. If expired:
   → Prompt for email/phone
   → Send OTP for verification
   → Create new session
5. If valid:
   → Load user_id from session
   → Fetch all orders for user_id
   → Restore conversation context
   
Customer: "What's my order status?"
Chatbot: "Welcome back! You have 3 orders:
  • ORD-123 (Delivered on Jan 10)
  • ORD-456 (Out for delivery, arrives tomorrow)
  • ORD-789 (Processing)
Which one would you like to check?"
```

**Session Lifecycle:**

```
New Visitor → Anonymous Session (30 min)
   ↓
User Provides Email/Phone → Identified Session (7 days)
   ↓
User Registers Account → Authenticated Session (30 days)
   ↓
Session Expires → Re-authenticate (OTP or Password)
```

**Context Preservation:**

```python
# Session data structure
session = {
    "user_id": 12345,
    "active_order_id": "ORD-789",
    "conversation_context": {
        "last_intent": "track_order",
        "mentioned_orders": ["ORD-789", "ORD-456"],
        "unresolved_queries": []
    },
    "preferences": {
        "language": "en",
        "notification_email": true
    }
}
```

---

## DATABASE SCHEMA DESIGN

### Complete Schema

```sql
-- Users table
CREATE TABLE users (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    email VARCHAR(255) UNIQUE NOT NULL,
    phone VARCHAR(20) UNIQUE,
    full_name VARCHAR(255),
    password_hash VARCHAR(255),
    is_verified BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP,
    metadata JSON,  -- For extensibility
    INDEX idx_email (email),
    INDEX idx_phone (phone)
);

-- Orders table
CREATE TABLE orders (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    order_id VARCHAR(50) UNIQUE NOT NULL,
    user_id BIGINT NOT NULL,
    total_amount DECIMAL(10, 2),
    payment_status ENUM('pending', 'paid', 'failed', 'refunded') DEFAULT 'pending',
    shipment_status ENUM('processing', 'shipped', 'out_for_delivery', 'delivered', 'cancelled') DEFAULT 'processing',
    carrier VARCHAR(100),
    tracking_id VARCHAR(100),
    expected_delivery DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    metadata JSON,
    FOREIGN KEY (user_id) REFERENCES users(id),
    INDEX idx_order_id (order_id),
    INDEX idx_user_id (user_id),
    INDEX idx_shipment_status (shipment_status),
    INDEX idx_created_at (created_at)
);

-- Order items table
CREATE TABLE order_items (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    order_id BIGINT NOT NULL,
    product_name VARCHAR(255) NOT NULL,
    quantity INT NOT NULL,
    price DECIMAL(10, 2) NOT NULL,
    sku VARCHAR(100),
    FOREIGN KEY (order_id) REFERENCES orders(id) ON DELETE CASCADE,
    INDEX idx_order_id (order_id)
);

-- Order status audit log
CREATE TABLE order_status_log (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    order_id BIGINT NOT NULL,
    old_status VARCHAR(50),
    new_status VARCHAR(50) NOT NULL,
    message TEXT,
    changed_by VARCHAR(100) DEFAULT 'system',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (order_id) REFERENCES orders(id) ON DELETE CASCADE,
    INDEX idx_order_id (order_id),
    INDEX idx_created_at (created_at)
);

-- User sessions
CREATE TABLE user_sessions (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    user_id BIGINT NOT NULL,
    session_token VARCHAR(512) UNIQUE NOT NULL,
    jwt_token TEXT,
    active_order_id VARCHAR(50),
    last_intent VARCHAR(50),
    conversation_summary TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP NOT NULL,
    last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_session_token (session_token),
    INDEX idx_user_id (user_id),
    INDEX idx_expires_at (expires_at)
);

-- API keys for webhooks
CREATE TABLE api_keys (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    key_name VARCHAR(100) NOT NULL,
    api_key VARCHAR(512) UNIQUE NOT NULL,
    secret_key VARCHAR(512),  -- For HMAC signing
    permissions JSON,  -- ["order.create", "order.update"]
    is_active BOOLEAN DEFAULT TRUE,
    rate_limit INT DEFAULT 100,  -- Requests per minute
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_used TIMESTAMP,
    INDEX idx_api_key (api_key),
    INDEX idx_is_active (is_active)
);

-- Knowledge base chunks
CREATE TABLE knowledge_base (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    source_file VARCHAR(255),
    chunk_index INT,
    content TEXT NOT NULL,
    embedding BLOB,  -- Store embeddings as binary
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_source_file (source_file)
);

-- Workflow execution logs
CREATE TABLE workflow_logs (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    workflow_name VARCHAR(100) NOT NULL,
    trigger_type VARCHAR(50),
    input_data JSON,
    output_data JSON,
    status ENUM('success', 'failed', 'retrying') DEFAULT 'success',
    error_message TEXT,
    execution_time_ms INT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_workflow_name (workflow_name),
    INDEX idx_status (status),
    INDEX idx_created_at (created_at)
);
```

### Migration Strategy

**From SQLite to PostgreSQL:**

```bash
# Step 1: Export existing data
python migration_tools/export_sqlite.py --output=data_export.json

# Step 2: Set up PostgreSQL
createdb oudience_production
psql oudience_production < schema/postgresql_schema.sql

# Step 3: Import data
python migration_tools/import_to_postgresql.py --input=data_export.json

# Step 4: Verify data integrity
python migration_tools/verify_migration.py

# Step 5: Update .env
DATABASE_URL=postgresql://user:pass@localhost/oudience_production

# Step 6: Restart application
# Application auto-detects PostgreSQL from DATABASE_URL
```

---

## SECURITY & PRODUCTION READINESS

### Environment-Based Configuration

**.env file (NOT committed to git):**

```bash
# Environment
ENVIRONMENT=production  # development, staging, production

# Database
DATABASE_URL=postgresql://user:password@localhost:5432/oudience_prod
DB_POOL_SIZE=20
DB_MAX_OVERFLOW=10

# Security
SECRET_KEY=<generated-secret-32-bytes>
JWT_SECRET=<generated-jwt-secret>
ADMIN_PASSWORD_HASH=<bcrypt-hash>

# API Keys
WEBHOOK_API_KEY=<generated-api-key>
WEBHOOK_SECRET_KEY=<hmac-secret>

# External Services
SENDGRID_API_KEY=<sendgrid-key>
TWILIO_ACCOUNT_SID=<twilio-sid>
TWILIO_AUTH_TOKEN=<twilio-token>

# Redis (optional)
REDIS_URL=redis://localhost:6379/0

# Rate Limiting
RATE_LIMIT_REQUESTS=100
RATE_LIMIT_WINDOW=60  # seconds

# Session
SESSION_TIMEOUT=1800  # 30 minutes
JWT_EXPIRY=2592000  # 30 days

# Monitoring
SENTRY_DSN=<sentry-dsn>
LOG_LEVEL=INFO
```

### JWT Authentication

```python
# Token structure
{
    "user_id": 12345,
    "email": "user@example.com",
    "role": "customer",  # customer, admin
    "iat": 1642348800,  # Issued at
    "exp": 1644940800   # Expiry
}

# Token usage
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

### Rate Limiting

```python
# Per-endpoint limits
RATE_LIMITS = {
    "/api/v1/chat/query": "60/minute",
    "/api/v1/webhooks/*": "100/minute", 
    "/api/v1/admin/*": "10/minute"
}

# Per-user limits
USER_RATE_LIMITS = {
    "anonymous": "20/minute",
    "authenticated": "60/minute",
    "admin": "unlimited"
}
```

### Input Validation

```python
# All inputs validated using Pydantic
from pydantic import BaseModel, EmailStr, validator

class OrderCreateRequest(BaseModel):
    order_id: str
    user_email: EmailStr
    user_phone: str
    items: List[OrderItem]
    total_amount: Decimal
    
    @validator('order_id')
    def validate_order_id(cls, v):
        if not re.match(r'^(AMZ|ORD)-\d+$', v):
            raise ValueError('Invalid order ID format')
        return v
    
    @validator('user_phone')
    def validate_phone(cls, v):
        if not re.match(r'^\d{10}$', v):
            raise ValueError('Phone must be 10 digits')
        return v
```

### Encryption

```python
# Sensitive data encrypted at rest
from cryptography.fernet import Fernet

# Encrypt phone numbers
encrypted_phone = encrypt_pii(user.phone)
orders.phone = encrypted_phone

# Decrypt when needed
decrypted_phone = decrypt_pii(orders.phone)
```

---

## AI SAFETY BOUNDARIES

### Decision Matrix

```
┌─────────────────────────────────────────────────────────────┐
│              AI vs BUSINESS LOGIC DECISION TREE             │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Question Type: Order Tracking                              │
│  ├─ Who decides? → BUSINESS LOGIC                          │
│  ├─ AI Role? → Response phrasing only                      │
│  └─ Why? → Order data must be 100% accurate                │
│                                                             │
│  Question Type: Cancellation Request                        │
│  ├─ Who decides? → BUSINESS LOGIC                          │
│  ├─ AI Role? → None                                        │
│  └─ Why? → Financial transaction, no room for error        │
│                                                             │
│  Question Type: Return Policy Inquiry                       │
│  ├─ Who decides? → RAG SYSTEM                              │
│  ├─ AI Role? → Semantic search + answer extraction         │
│  └─ Why? → Informational, can verify against KB            │
│                                                             │
│  Question Type: General Help                                │
│  ├─ Who decides? → AI (with guardrails)                    │
│  ├─ AI Role? → Generate helpful response                   │
│  └─ Why? → Non-critical, improves UX                       │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### Fail-Safe Mechanisms

```python
# Hallucination detection
def validate_ai_response(response, context):
    # Check 1: No order IDs unless in context
    if re.search(r'(AMZ|ORD)-\d+', response) and not context.get('order_id'):
        return REJECT_HALLUCINATION
    
    # Check 2: No prices unless from database
    if re.search(r'\$\d+|\₹\d+', response) and not context.get('has_price_data'):
        return REJECT_HALLUCINATION
    
    # Check 3: No dates unless from database
    if re.search(r'\d{4}-\d{2}-\d{2}', response) and not context.get('has_date_data'):
        return REJECT_HALLUCINATION
    
    # Check 4: Length sanity check
    if len(response) > 500:
        return REJECT_TOO_LONG
    
    return APPROVED

# Fallback chain
try:
    response = ai_generate_response(query)
    if not validate_ai_response(response, context):
        raise HallucinationDetected()
except Exception:
    response = deterministic_fallback(query, context)
```

---

## DEPLOYMENT GUIDE (Summary)

### Local Development

```bash
# 1. Clone and setup
git clone <repo>
cd oudience_clone
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Setup environment
cp .env.example .env
# Edit .env with your values

# 4. Initialize database
python scripts/init_database.py

# 5. Run migrations
python scripts/run_migrations.py

# 6. Start server
python app.py
# Or with auto-reload:
flask run --debug
```

### Production Deployment

```bash
# 1. Server setup (Ubuntu 22.04)
sudo apt update
sudo apt install python3.10 python3-pip postgresql nginx

# 2. Create database
sudo -u postgres createdb oudience_production

# 3. Application setup
cd /opt/oudience
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 4. Environment configuration
sudo nano /opt/oudience/.env
# Set production values

# 5. Run with Gunicorn (production WSGI server)
gunicorn -w 4 -b 0.0.0.0:8000 app:app

# 6. Configure Nginx reverse proxy
sudo nano /etc/nginx/sites-available/oudience
# See DEPLOYMENT_GUIDE.md for full Nginx config

# 7. Enable HTTPS with Let's Encrypt
sudo certbot --nginx -d yourdomain.com

# 8. Setup systemd service for auto-start
sudo systemctl enable oudience
sudo systemctl start oudience
```

---

**END OF PRODUCTION_ARCHITECTURE.md**

This architecture provides a complete Amazon-style customer support system with automated order ingestion, production-grade security, and scalable infrastructure.
