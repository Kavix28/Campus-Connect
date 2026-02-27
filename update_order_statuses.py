import sqlite3
import json

# Connect to the database
conn = sqlite3.connect('analytics.db')
cursor = conn.cursor()

# Read the orders from orders.json
with open('orders.json', 'r') as f:
    orders = json.load(f)

# Update each order in the database
for order in orders:
    cursor.execute('''
        UPDATE orders 
        SET shipment_status = ?,
            expected_delivery = ?,
            last_updated = ?
        WHERE order_id = ?
    ''', (
        order['shipment_status'],
        order['expected_delivery'],
        order['last_updated'],
        order['order_id']
    ))
    
    # If order doesn't exist, insert it
    if cursor.rowcount == 0:
        cursor.execute('''
            INSERT INTO orders (
                order_id, email, phone, items, payment_status,
                shipment_status, carrier, tracking_id,
                expected_delivery, last_updated, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            order['order_id'],
            order['email'],
            order['phone'],
            json.dumps(order['items']),
            order['payment_status'],
            order['shipment_status'],
            order['carrier'],
            order['tracking_id'],
            order['expected_delivery'],
            order['last_updated'],
            order.get('created_at', order['last_updated'])
        ))
        print(f"Inserted new order: {order['order_id']}")
    else:
        print(f"Updated order: {order['order_id']} - Status: {order['shipment_status']}")

# Commit changes
conn.commit()

# Verify the updates
print("\n=== Current Order Statuses ===")
cursor.execute('SELECT order_id, shipment_status, expected_delivery FROM orders')
for row in cursor.fetchall():
    print(f"{row[0]}: {row[1]} (Expected: {row[2]})")

conn.close()
print("\n✅ Database updated successfully!")
