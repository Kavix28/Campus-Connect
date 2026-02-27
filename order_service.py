import json
import os
import sqlite3
from datetime import datetime, timedelta
import random

class OrderService:
    def __init__(self):
        self.db_file = "analytics.db"
        self.orders_file = "orders.json"
        self._init_storage()
    
    def _init_storage(self):
        if os.path.exists(self.db_file):
            self._init_sqlite()
        else:
            self._init_json()
    
    def _init_sqlite(self):
        self.use_sqlite = True
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS orders (
                order_id TEXT PRIMARY KEY,
                user_id INTEGER,
                email TEXT,
                phone TEXT,
                items TEXT,
                payment_status TEXT,
                shipment_status TEXT,
                carrier TEXT,
                tracking_id TEXT,
                expected_delivery TEXT,
                last_updated TEXT,
                created_at TEXT
            )
        ''')
        
        # Add user_id column if it doesn't exist (migration for existing databases)
        try:
            cursor.execute("ALTER TABLE orders ADD COLUMN user_id INTEGER")
            cursor.execute("ALTER TABLE orders ADD COLUMN created_at TEXT")
            conn.commit()
        except sqlite3.OperationalError:
            # Column already exists
            pass
        
        cursor.execute("SELECT COUNT(*) FROM orders")
        if cursor.fetchone()[0] == 0:
            mock_orders = [
                ("AMZ123456789", "john@example.com", "9876543210", 
                 '[{"name": "Wireless Headphones", "quantity": 1, "price": 2999}, {"name": "Phone Case", "quantity": 2, "price": 599}]',
                 "paid", "shipped", "Amazon Logistics", "TRK789012345", "2026-01-11", "2026-01-09 14:30:00"),
                ("AMZ987654321", "jane@example.com", "8765432109",
                 '[{"name": "Bluetooth Speaker", "quantity": 1, "price": 4999}]',
                 "paid", "delivered", "Blue Dart", "TRK456789012", "2026-01-08", "2026-01-08 16:45:00"),
                ("AMZ555666777", "mike@example.com", "7654321098",
                 '[{"name": "Gaming Mouse", "quantity": 1, "price": 1899}]',
                 "pending", "processing", "", "", "2026-01-13", "2026-01-09 10:15:00"),
                ("ORD-10293", "test@example.com", "5551234567",
                 '[{"name": "Test Product", "quantity": 1, "price": 1999}]',
                 "paid", "out_for_delivery", "FedEx", "TRK123456789", "2026-01-10", "2026-01-10 09:15:00")
            ]
            
            cursor.executemany('''
                INSERT INTO orders (order_id, email, phone, items, payment_status, 
                                  shipment_status, carrier, tracking_id, expected_delivery, last_updated)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', mock_orders)
        
        conn.commit()
        conn.close()
    
    def _init_json(self):
        self.use_sqlite = False
        if not os.path.exists(self.orders_file):
            mock_orders = [
                {
                    "order_id": "AMZ123456789",
                    "email": "john@example.com",
                    "phone": "9876543210",
                    "items": [
                        {"name": "Wireless Headphones", "quantity": 1, "price": 2999},
                        {"name": "Phone Case", "quantity": 2, "price": 599}
                    ],
                    "payment_status": "paid",
                    "shipment_status": "shipped",
                    "carrier": "Amazon Logistics",
                    "tracking_id": "TRK789012345",
                    "expected_delivery": "2026-01-11",
                    "last_updated": "2026-01-09 14:30:00"
                },
                {
                    "order_id": "AMZ987654321",
                    "email": "jane@example.com",
                    "phone": "8765432109",
                    "items": [
                        {"name": "Bluetooth Speaker", "quantity": 1, "price": 4999}
                    ],
                    "payment_status": "paid",
                    "shipment_status": "delivered",
                    "carrier": "Blue Dart",
                    "tracking_id": "TRK456789012",
                    "expected_delivery": "2026-01-08",
                    "last_updated": "2026-01-08 16:45:00"
                },
                {
                    "order_id": "AMZ555666777",
                    "email": "mike@example.com",
                    "phone": "7654321098",
                    "items": [
                        {"name": "Gaming Mouse", "quantity": 1, "price": 1899}
                    ],
                    "payment_status": "pending",
                    "shipment_status": "processing",
                    "carrier": "",
                    "tracking_id": "",
                    "expected_delivery": "2026-01-13",
                    "last_updated": "2026-01-09 10:15:00"
                },
                {
                    "order_id": "ORD-10293",
                    "email": "test@example.com",
                    "phone": "5551234567",
                    "items": [
                        {"name": "Test Product", "quantity": 1, "price": 1999}
                    ],
                    "payment_status": "paid",
                    "shipment_status": "out_for_delivery",
                    "carrier": "FedEx",
                    "tracking_id": "TRK123456789",
                    "expected_delivery": "2026-01-10",
                    "last_updated": "2026-01-10 09:15:00"
                }
            ]
            with open(self.orders_file, "w") as f:
                json.dump(mock_orders, f, indent=2)
    
    def _get_order_sqlite(self, where_clause, params):
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        
        cursor.execute(f'''
            SELECT order_id, email, phone, items, payment_status, shipment_status,
                   carrier, tracking_id, expected_delivery, last_updated
            FROM orders WHERE {where_clause}
        ''', params)
        
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return {
                "order_id": row[0],
                "email": row[1],
                "phone": row[2],
                "items": json.loads(row[3]),
                "payment_status": row[4],
                "shipment_status": row[5],
                "carrier": row[6],
                "tracking_id": row[7],
                "expected_delivery": row[8],
                "last_updated": row[9]
            }
        return None
    
    def _get_order_json(self, filter_func):
        with open(self.orders_file, "r") as f:
            orders = json.load(f)
        
        for order in orders:
            if filter_func(order):
                return order
        return None
    
    def get_order_by_id(self, order_id):
        if self.use_sqlite:
            return self._get_order_sqlite("order_id = ? COLLATE NOCASE", (order_id,))
        else:
            return self._get_order_json(lambda o: o["order_id"].upper() == order_id.upper())
    
    def get_order_by_email(self, email):
        if self.use_sqlite:
            return self._get_order_sqlite("email = ? COLLATE NOCASE", (email,))
        else:
            return self._get_order_json(lambda o: o["email"].lower() == email.lower())
    
    def get_order_by_phone_last4(self, last4):
        if self.use_sqlite:
            return self._get_order_sqlite("phone LIKE ?", (f"%{last4}",))
        else:
            return self._get_order_json(lambda o: o["phone"].endswith(last4))
    
    def refresh_order_status(self, order_id):
        order = self.get_order_by_id(order_id)
        if not order:
            return None
        
        last_updated = datetime.strptime(order["last_updated"], "%Y-%m-%d %H:%M:%S")
        now = datetime.now()
        minutes_ago = int((now - last_updated).total_seconds() / 60)
        
        status_progression = {
            "processing": ["shipped", "out_for_delivery"],
            "shipped": ["out_for_delivery", "delivered"],
            "out_for_delivery": ["delivered"]
        }
        
        current_status = order["shipment_status"]
        if current_status in status_progression and minutes_ago > 60:
            if random.random() < 0.3:
                next_statuses = status_progression[current_status]
                new_status = random.choice(next_statuses)
                self._update_order_status(order_id, {"shipment_status": new_status})
                order["shipment_status"] = new_status
                order["last_updated"] = now.strftime("%Y-%m-%d %H:%M:%S")
                minutes_ago = 0
        
        return {
            **order,
            "minutes_since_update": minutes_ago
        }
    
    def _update_order_status(self, order_id, updates):
        updates["last_updated"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        if self.use_sqlite:
            conn = sqlite3.connect(self.db_file)
            cursor = conn.cursor()
            
            set_clause = ", ".join([f"{k} = ?" for k in updates.keys()])
            values = list(updates.values()) + [order_id]
            
            cursor.execute(f"UPDATE orders SET {set_clause} WHERE order_id = ?", values)
            conn.commit()
            conn.close()
        else:
            with open(self.orders_file, "r") as f:
                orders = json.load(f)
            
            for order in orders:
                if order["order_id"] == order_id:
                    order.update(updates)
                    break
            
            with open(self.orders_file, "w") as f:
                json.dump(orders, f, indent=2)
    
    def find_order(self, order_id=None, email=None, phone=None, last_digits=None):
        if order_id:
            return self.get_order_by_id(order_id)
        elif email:
            return self.get_order_by_email(email)
        elif phone:
            if self.use_sqlite:
                return self._get_order_sqlite("phone = ?", (phone,))
            else:
                return self._get_order_json(lambda o: o["phone"] == phone)
        elif last_digits:
            return self.get_order_by_phone_last4(last_digits)
        return None
    
    def get_order_status(self, order_id):
        return self.refresh_order_status(order_id)
    
    def create_order(self, order_id, user_id=None, email=None, phone=None, 
                     items=None, total_amount=0.0, payment_status="pending", 
                     shipment_status="processing", carrier="", tracking_id="",
                     expected_delivery=None, created_at=None):
        """
        Create new order in database (used by webhooks for automated order ingestion).
        
        Args:
            order_id: Unique order identifier
            user_id: Foreign key to users table (optional)
           email: Customer email
            phone: Customer phone
            items: List of order items
            total_amount: Order total
            payment_status: Payment status
            shipment_status: Shipment status
            carrier: Shipping carrier
            tracking_id: Tracking number
            expected_delivery: Expected delivery date
            created_at: Order creation timestamp
        
        Returns:
            Created order dictionary
        """
        if items is None:
            items = []
        
        if created_at is None:
            created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        if expected_delivery is None:
            # Default: 3 days from now
            expected_delivery = (datetime.now() + timedelta(days=3)).strftime("%Y-%m-%d")
        
        last_updated = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        items_json = json.dumps(items) if isinstance(items, list) else items
        
        if self.use_sqlite:
            conn = sqlite3.connect(self.db_file)
            cursor = conn.cursor()
            
            try:
                cursor.execute("""
                    INSERT INTO orders (
                        order_id, user_id, email, phone, items, payment_status,
                        shipment_status, carrier, tracking_id, expected_delivery,
                        last_updated, created_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    order_id, user_id, email, phone, items_json, payment_status,
                    shipment_status, carrier, tracking_id, expected_delivery,
                    last_updated, created_at
                ))
                
                conn.commit()
                
                return {
                    "order_id": order_id,
                    "user_id": user_id,
                    "email": email,
                    "phone": phone,
                    "items": items if isinstance(items, list) else json.loads(items),
                    "payment_status": payment_status,
                    "shipment_status": shipment_status,
                    "carrier": carrier,
                    "tracking_id": tracking_id,
                    "expected_delivery": expected_delivery,
                    "last_updated": last_updated,
                    "created_at": created_at
                }
            finally:
                conn.close()
        else:
            # JSON file storage
            with open(self.orders_file, "r") as f:
                orders = json.load(f)
            
            new_order = {
                "order_id": order_id,
                "user_id": user_id,
                "email": email,
                "phone": phone,
                "items": items if isinstance(items, list) else json.loads(items),
                "payment_status": payment_status,
                "shipment_status": shipment_status,
                "carrier": carrier,
                "tracking_id": tracking_id,
                "expected_delivery": expected_delivery,
                "last_updated": last_updated,
                "created_at": created_at
            }
            
            orders.append(new_order)
            
            with open(self.orders_file, "w") as f:
                json.dump(orders, f, indent=2)
            
            return new_order
