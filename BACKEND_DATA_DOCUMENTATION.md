# Backend Data Documentation

**Oudience Clone - Complete Backend Data Reference**  
Last Updated: 2026-01-15

---

## Table of Contents
1. [Overview](#overview)
2. [Data Storage Architecture](#data-storage-architecture)
3. [Orders Data](#orders-data)
4. [Knowledge Base Data](#knowledge-base-data)
5. [Upload Logs Data](#upload-logs-data)
6. [Session Data](#session-data)
7. [How to Add More Orders](#how-to-add-more-orders)
8. [Data Schema Reference](#data-schema-reference)

---

## Overview

The Oudience Clone backend uses two storage systems:
- **SQLite Database** (`analytics.db`) - Primary storage for orders (if exists)
- **JSON Files** - Fallback storage and knowledge base

Currently active storage: **SQLite Database** (since `analytics.db` exists)

---

## Data Storage Architecture

### Storage Files
| File | Purpose | Format |
|------|---------|--------|
| `analytics.db` | Orders database (SQLite) | Binary/SQLite |
| `orders.json` | Orders backup/fallback | JSON |
| `knowledge_base.json` | RAG knowledge chunks | JSON |
| `upload_logs.json` | PDF upload tracking | JSON |
| `flask_sessions/` | User sessions | Directory with session files |

### Storage Selection Logic
```python
# From order_service.py
if os.path.exists("analytics.db"):
    use_sqlite = True  # ✓ Currently active
else:
    use_sqlite = False  # Use JSON fallback
```

---

## Orders Data

### Current Orders in Database (4 Total)

#### Order #1: AMZ123456789
```json
{
  "order_id": "AMZ123456789",
  "email": "john@example.com",
  "phone": "9876543210",
  "items": [
    {
      "name": "Wireless Headphones",
      "quantity": 1,
      "price": 2999
    },
    {
      "name": "Phone Case",
      "quantity": 2,
      "price": 599
    }
  ],
  "payment_status": "paid",
  "shipment_status": "shipped",
  "carrier": "Amazon Logistics",
  "tracking_id": "TRK789012345",
  "expected_delivery": "2026-01-11",
  "last_updated": "2026-01-09 14:30:00"
}
```
**Total Order Value:** ₹4,197 (2999 + 599×2)

---

#### Order #2: ORD-10293
```json
{
  "order_id": "ORD-10293",
  "email": "user@example.com",
  "phone": "5551234567",
  "items": [
    {
      "name": "Laptop Stand",
      "quantity": 1,
      "price": 3499
    }
  ],
  "payment_status": "paid",
  "shipment_status": "out_for_delivery",
  "carrier": "FedEx",
  "tracking_id": "TRK987654321",
  "expected_delivery": "2026-01-10",
  "last_updated": "2026-01-10 09:15:00"
}
```
**Total Order Value:** ₹3,499

---

#### Order #3: AMZ987654321
```json
{
  "order_id": "AMZ987654321",
  "email": "jane@example.com",
  "phone": "8765432109",
  "items": [
    {
      "name": "Bluetooth Speaker",
      "quantity": 1,
      "price": 4999
    }
  ],
  "payment_status": "paid",
  "shipment_status": "delivered",
  "carrier": "Blue Dart",
  "tracking_id": "TRK456789012",
  "expected_delivery": "2026-01-08",
  "last_updated": "2026-01-08 16:45:00"
}
```
**Total Order Value:** ₹4,999

---

#### Order #4: AMZ555666777
```json
{
  "order_id": "AMZ555666777",
  "email": "mike@example.com",
  "phone": "7654321098",
  "items": [
    {
      "name": "Gaming Mouse",
      "quantity": 1,
      "price": 1899
    }
  ],
  "payment_status": "pending",
  "shipment_status": "processing",
  "carrier": "",
  "tracking_id": "",
  "expected_delivery": "2026-01-13",
  "last_updated": "2026-01-09 10:15:00"
}
```
**Total Order Value:** ₹1,899

---

### Order Status Summary

| Status | Count | Order IDs |
|--------|-------|-----------|
| **Delivered** | 1 | AMZ987654321 |
| **Out for Delivery** | 1 | ORD-10293 |
| **Shipped** | 1 | AMZ123456789 |
| **Processing** | 1 | AMZ555666777 |

### Payment Status Summary

| Status | Count |
|--------|-------|
| **Paid** | 3 |
| **Pending** | 1 |

---

## Knowledge Base Data

### Total Chunks: 10
**Source:** Sample_Policies.pdf  
**Uploaded:** 2026-01-10 16:00:00

#### Knowledge Base Entries

1. **Return Policy** (ID: 1)
   - Returns within 30 days
   - Full refund for original condition items
   - Refund processing: 5-7 business days

2. **Shipping Policy** (ID: 2)
   - Free shipping on orders >$35
   - Standard: 3-5 days
   - Express: 1-2 days ($9.99)
   - International shipping available

3. **Cancellation Policy** (ID: 3)
   - Free cancellation within 1 hour
   - Fees apply after processing
   - Shipped orders must be returned

4. **Refund Policy** (ID: 4)
   - Credit cards: 5-7 business days
   - PayPal: Instant
   - Bank transfers: Up to 10 business days

5. **Exchange Policy** (ID: 5)
   - Free exchanges for defects
   - Contact support with photos
   - Immediate replacement

6. **Customer Support** (ID: 6)
   - Hours: Monday-Friday 9AM-6PM EST
   - Email: support@oudience.com
   - Phone: 1-800-OUDIENCE
   - Response time: 24 hours

7. **Warranty Information** (ID: 7)
   - 1-year manufacturer warranty
   - Extended warranties available
   - Covers manufacturing defects only

8. **Privacy Policy** (ID: 8)
   - Personal data never sold
   - 256-bit encryption
   - Cookie usage for UX
   - Email opt-out available

9. **Payment Methods** (ID: 9)
   - Accepted: Visa, MasterCard, Amex, Discover, PayPal, Apple Pay, Google Pay
   - 256-bit SSL encryption
   - Payment info not stored

10. **Gift Cards** (ID: 10)
    - Denominations: $10-$500
    - Never expire
    - Cannot be redeemed for cash

---

## Upload Logs Data

### PDF Upload History

| Filename | Chunks Added | Upload Date |
|----------|-------------|-------------|
| Sample_Policies.pdf | 10 | 2026-01-10 16:00:00 |

---

## Session Data

### Session Storage Location
- **Directory:** `flask_sessions/`
- **Type:** Filesystem-based sessions
- **Session Count:** 57 active sessions

### Session Data Structure
```python
{
  "active_order_id": "AMZ123456789",  # Currently tracked order
  "verified_user": True,               # User verification status
  "last_intent": "track_order",        # Last detected intent
  "conversation_summary": "...",       # Conversation context (max 500 chars)
  "is_admin": False                    # Admin authentication
}
```

### Admin Authentication
- **Admin Token:** `admin123`
- **Session Key:** `is_admin`

---

## How to Add More Orders

### Method 1: Direct SQLite Database Insertion (Recommended)

#### Step 1: Install SQLite Browser (Optional)
Download DB Browser for SQLite: https://sqlitebrowser.org/

#### Step 2: Open Database
```bash
# Connect to database
sqlite3 analytics.db
```

#### Step 3: Insert New Order
```sql
INSERT INTO orders (
    order_id, 
    email, 
    phone, 
    items, 
    payment_status, 
    shipment_status, 
    carrier, 
    tracking_id, 
    expected_delivery, 
    last_updated
) VALUES (
    'AMZ999888777',
    'newcustomer@example.com',
    '9998887776',
    '[{"name": "Smart Watch", "quantity": 1, "price": 12999}]',
    'paid',
    'shipped',
    'DHL',
    'TRK999888777',
    '2026-01-16',
    '2026-01-15 10:00:00'
);
```

#### Step 4: Verify Insertion
```sql
SELECT * FROM orders WHERE order_id = 'AMZ999888777';
```

---

### Method 2: Edit JSON Directly (Fallback)

**⚠️ Warning:** This only works if you delete `analytics.db` first, or edit both files.

#### Step 1: Open `orders.json`
```bash
# Open in any text editor
notepad orders.json
```

#### Step 2: Add New Order Object
```json
{
  "order_id": "AMZ999888777",
  "email": "newcustomer@example.com",
  "phone": "9998887776",
  "items": [
    {
      "name": "Smart Watch",
      "quantity": 1,
      "price": 12999
    }
  ],
  "payment_status": "paid",
  "shipment_status": "shipped",
  "carrier": "DHL",
  "tracking_id": "TRK999888777",
  "expected_delivery": "2026-01-16",
  "last_updated": "2026-01-15 10:00:00"
}
```

#### Step 3: Save and Restart
```bash
# Restart Flask app
# CTRL+C to stop
python app.py
```

---

### Method 3: Create Python Script

Create `add_order.py`:

```python
import sqlite3
import json
from datetime import datetime

def add_order_to_sqlite(order_data):
    """Add order to SQLite database"""
    conn = sqlite3.connect('analytics.db')
    cursor = conn.cursor()
    
    cursor.execute('''
        INSERT INTO orders (order_id, email, phone, items, payment_status, 
                          shipment_status, carrier, tracking_id, expected_delivery, last_updated)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        order_data['order_id'],
        order_data['email'],
        order_data['phone'],
        json.dumps(order_data['items']),
        order_data['payment_status'],
        order_data['shipment_status'],
        order_data['carrier'],
        order_data['tracking_id'],
        order_data['expected_delivery'],
        order_data['last_updated']
    ))
    
    conn.commit()
    conn.close()
    print(f"✓ Order {order_data['order_id']} added successfully!")

def add_order_to_json(order_data):
    """Add order to JSON file"""
    with open('orders.json', 'r') as f:
        orders = json.load(f)
    
    orders.append(order_data)
    
    with open('orders.json', 'w') as f:
        json.dump(orders, f, indent=2)
    
    print(f"✓ Order {order_data['order_id']} added to JSON!")

# Example usage
new_order = {
    "order_id": "AMZ999888777",
    "email": "newcustomer@example.com",
    "phone": "9998887776",
    "items": [
        {"name": "Smart Watch", "quantity": 1, "price": 12999}
    ],
    "payment_status": "paid",
    "shipment_status": "shipped",
    "carrier": "DHL",
    "tracking_id": "TRK999888777",
    "expected_delivery": "2026-01-16",
    "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
}

# Add to both databases
add_order_to_sqlite(new_order)
add_order_to_json(new_order)
```

Run the script:
```bash
python add_order.py
```

---

### Method 4: Bulk Import from CSV

Create `bulk_import_orders.py`:

```python
import sqlite3
import json
import csv
from datetime import datetime

def bulk_import_from_csv(csv_file):
    """Import multiple orders from CSV file"""
    
    conn = sqlite3.connect('analytics.db')
    cursor = conn.cursor()
    
    with open(csv_file, 'r') as f:
        reader = csv.DictReader(f)
        
        for row in reader:
            # Parse items from JSON string in CSV
            items = json.loads(row['items'])
            
            cursor.execute('''
                INSERT INTO orders (order_id, email, phone, items, payment_status, 
                                  shipment_status, carrier, tracking_id, expected_delivery, last_updated)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                row['order_id'],
                row['email'],
                row['phone'],
                row['items'],
                row['payment_status'],
                row['shipment_status'],
                row['carrier'],
                row['tracking_id'],
                row['expected_delivery'],
                datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            ))
            
            print(f"✓ Imported: {row['order_id']}")
    
    conn.commit()
    conn.close()
    print("\n✓ Bulk import completed!")

# Usage
bulk_import_from_csv('orders_to_import.csv')
```

**CSV Format** (`orders_to_import.csv`):
```csv
order_id,email,phone,items,payment_status,shipment_status,carrier,tracking_id,expected_delivery
AMZ111222333,alice@example.com,1112223334,"[{\"name\":\"Keyboard\",\"quantity\":1,\"price\":2499}]",paid,processing,Amazon Logistics,TRK111222333,2026-01-18
AMZ444555666,bob@example.com,4445556667,"[{\"name\":\"Monitor\",\"quantity\":1,\"price\":15999}]",paid,shipped,Blue Dart,TRK444555666,2026-01-17
```

---

## Data Schema Reference

### Orders Table Schema (SQLite)

```sql
CREATE TABLE orders (
    order_id TEXT PRIMARY KEY,
    email TEXT,
    phone TEXT,
    items TEXT,              -- JSON array string
    payment_status TEXT,      -- "paid" | "pending" | "failed"
    shipment_status TEXT,     -- "processing" | "shipped" | "out_for_delivery" | "delivered"
    carrier TEXT,
    tracking_id TEXT,
    expected_delivery TEXT,   -- Format: "YYYY-MM-DD"
    last_updated TEXT         -- Format: "YYYY-MM-DD HH:MM:SS"
);
```

### Field Constraints

| Field | Type | Required | Allowed Values |
|-------|------|----------|----------------|
| `order_id` | TEXT | ✓ | Unique identifier (e.g., AMZ123456789) |
| `email` | TEXT | ✓ | Valid email format |
| `phone` | TEXT | ✓ | 10-digit number |
| `items` | JSON | ✓ | Array of `{name, quantity, price}` |
| `payment_status` | TEXT | ✓ | `"paid"`, `"pending"`, `"failed"` |
| `shipment_status` | TEXT | ✓ | `"processing"`, `"shipped"`, `"out_for_delivery"`, `"delivered"` |
| `carrier` | TEXT | ✗ | Any courier name (empty for processing) |
| `tracking_id` | TEXT | ✗ | Tracking number (empty for processing) |
| `expected_delivery` | TEXT | ✓ | `YYYY-MM-DD` format |
| `last_updated` | TEXT | ✓ | `YYYY-MM-DD HH:MM:SS` format |

### Items Schema (JSON Array)

```typescript
type Item = {
  name: string;        // Product name
  quantity: number;    // Quantity ordered
  price: number;       // Price per unit in INR
}

type Items = Item[];
```

**Example:**
```json
[
  {"name": "Wireless Mouse", "quantity": 2, "price": 899},
  {"name": "USB Cable", "quantity": 3, "price": 199}
]
```

---

### Knowledge Base Schema

```typescript
type KnowledgeChunk = {
  id: number;          // Unique chunk ID
  source: string;      // Source PDF filename
  text: string;        // Chunk text (max ~250 words)
}
```

### Upload Logs Schema

```typescript
type UploadLog = {
  filename: string;      // PDF filename
  chunks: number;        // Number of chunks created
  uploaded_at: string;   // "YYYY-MM-DD HH:MM:SS"
}
```

---

## Status Progression Logic

The system auto-updates order status based on time:

```python
# From order_service.py
status_progression = {
    "processing": ["shipped", "out_for_delivery"],
    "shipped": ["out_for_delivery", "delivered"],
    "out_for_delivery": ["delivered"]
}

# Auto-update conditions:
# - If order not updated in 60+ minutes
# - Random 30% chance
# - Progresses to random next status
```

---

## Quick Reference Commands

### View All Orders (SQLite)
```bash
sqlite3 analytics.db "SELECT order_id, email, shipment_status FROM orders;"
```

### Count Orders by Status
```bash
sqlite3 analytics.db "SELECT shipment_status, COUNT(*) FROM orders GROUP BY shipment_status;"
```

### Delete Specific Order
```bash
sqlite3 analytics.db "DELETE FROM orders WHERE order_id = 'AMZ123456789';"
```

### Export All Orders to JSON
```bash
sqlite3 analytics.db -json "SELECT * FROM orders;" > exported_orders.json
```

### View Knowledge Base Chunks
```bash
python -c "import json; print(json.dumps(json.load(open('knowledge_base.json')), indent=2))"
```

---

## Testing Your New Orders

### Via API (POST /order/lookup)
```bash
curl -X POST http://127.0.0.1:5001/order/lookup \
  -H "Content-Type: application/json" \
  -d '{
    "order_id": "AMZ999888777"
  }'
```

### Via Chatbot
Just ask:
- "Track my order AMZ999888777"
- "Where is my order for newcustomer@example.com?"
- "Check order with phone 9998887776"

---

## Backup Recommendations

### Before Adding Orders
```bash
# Backup SQLite database
cp analytics.db analytics.db.backup

# Backup JSON files
cp orders.json orders.json.backup
cp knowledge_base.json knowledge_base.json.backup
```

### Restore from Backup
```bash
# Restore database
cp analytics.db.backup analytics.db

# Restart application
python app.py
```

---

## Additional Notes

### Order ID Formats
- **Amazon-style:** `AMZ` + 9 digits (e.g., `AMZ123456789`)
- **Generic:** `ORD-` + number (e.g., `ORD-10293`)
- **Custom:** Any unique string

### Phone Number Search
- Users can search with last 4 digits
- Example: Phone `9876543210` → Search `"3210"`

### Email Search
- Case-insensitive matching
- Example: `John@Example.COM` matches `john@example.com`

### Dynamic Status Updates
Orders automatically progress between statuses if not updated for 60+ minutes (30% chance per query).

---

## Support Intents Handled

The chatbot recognizes these intents:
1. ✓ `track_order` - Track order status
2. ✓ `where_is_my_order` - Location queries
3. ✓ `late_delivery` - Delayed delivery complaints
4. ✓ `cancel_order` - Order cancellation
5. ✓ `refund_status` - Refund inquiries
6. ✓ `replace_item` - Item replacement
7. ✓ `payment_issue` - Payment problems
8. ✓ `account_help` - Account assistance
9. ✓ `general` - RAG-based responses

---

## End of Documentation

**Last Updated:** 2026-01-15  
**Version:** 1.0  
**Maintainer:** Oudience Team

For any questions or issues with data management, refer to:
- `app.py` - Main application logic
- `order_service.py` - Order management
- `intent_handler.py` - Intent processing
