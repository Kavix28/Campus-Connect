"""
Order Placement Simulator
Simulates e-commerce orders for testing the automatic ingestion system
"""

import requests
import json
import random
import time
from datetime import datetime, timedelta


class OrderSimulator:
    """
    Simulates order creation from e-commerce platforms
    """
    
    def __init__(self, webhook_url="http://localhost:5001/api/v1/webhooks/order/create",
                 api_key="dev-webhook-key-replace-in-production"):
        self.webhook_url = webhook_url
        self.api_key = api_key
        self.order_counter = 1000
    
    def generate_order(self, customer_email=None, customer_phone=None, customer_name=None):
        """
        Generate realistic order payload
        
        Args:
            customer_email: Override customer email
            customer_phone: Override customer phone
            customer_name: Override customer name
        
        Returns:
            dict: Order payload ready for webhook
        """
        # Generate order ID
        order_id = f"SIM-{datetime.now().strftime('%Y%m%d')}-{self.order_counter:04d}"
        self.order_counter += 1
        
        # Sample customer data
        if not customer_email:
            first_names = ["John", "Jane", "Mike", "Sarah", "David", "Emma"]
            last_names = ["Smith", "Johnson", "Williams", "Brown", "Davis"]
            fname = random.choice(first_names).lower()
            lname = random.choice(last_names).lower()
            customer_email = f"{fname}.{lname}@example.com"
        
        if not customer_phone:
            customer_phone = f"98765{random.randint(10000, 99999)}"
        
        if not customer_name:
            customer_name = customer_email.split('@')[0].replace('.', ' ').title()
        
        # Sample products
        products = [
            {"name": "Wireless Headphones", "price": 2999.00, "sku": "WH-BT-001"},
            {"name": "Phone Case", "price": 599.00, "sku": "PC-SIL-002"},
            {"name": "Bluetooth Speaker", "price": 4999.00, "sku": "SP-BT-003"},
            {"name": "Smartwatch", "price": 12999.00, "sku": "SW-FIT-004"},
            {"name": "Power Bank", "price": 1499.00, "sku": "PB-20K-005"},
            {"name": "USB Cable", "price": 299.00, "sku": "CB-USB-006"},
            {"name": "Screen Protector", "price": 399.00, "sku": "SP-GLASS-007"},
            {"name": "Laptop Stand", "price": 1899.00, "sku": "LS-ALU-008"}
        ]
        
        # Select 1-3 random products
        selected_products = random.sample(products, random.randint(1, 3))
        
        items = []
        subtotal = 0.0
        
        for product in selected_products:
            quantity = random.randint(1, 2)
            price = product["price"]
            items.append({
                "product_id": product["sku"],
                "name": product["name"],
                "quantity": quantity,
                "price": price,
                "sku": product["sku"]
            })
            subtotal += price * quantity
        
        # Calculate totals
        tax = subtotal * 0.18  # 18% GST
        shipping = 0.0 if subtotal > 500 else 50.0
        total = subtotal + tax + shipping
        
        # Build order payload (matches webhook_service expected format)
        payload = {
            "order_id": order_id,
            "customer": {
                "email": customer_email,
                "phone": customer_phone,
                "name": customer_name
            },
            "items": items,
            "totals": {
                "subtotal": round(subtotal, 2),
                "tax": round(tax, 2),
                "shipping": shipping,
                "total": round(total, 2)
            },
            "payment": {
                "method": random.choice(["credit_card", "debit_card", "upi", "netbanking"]),
                "status": "completed",
                "transaction_id": f"TXN-{random.randint(100000, 999999)}"
            },
            "created_at": datetime.now().isoformat() + "Z"
        }
        
        return payload
    
    def place_order(self, payload):
        """
        Send order to webhook endpoint
        
        Args:
            payload: Order payload dict
        
        Returns:
            Response object
        """
        headers = {
            "X-API-Key": self.api_key,
            "Content-Type": "application/json"
        }
        
        try:
            response = requests.post(
                self.webhook_url,
                json=payload,
                headers=headers,
                timeout=10
            )
            
            return {
                "success": response.status_code == 200,
                "status_code": response.status_code,
                "response": response.json() if response.text else {},
                "order_id": payload["order_id"]
            }
        
        except requests.exceptions.RequestException as e:
            return {
                "success": False,
                "error": str(e),
                "order_id": payload["order_id"]
            }
    
    def simulate_single_order(self, **customer_kwargs):
        """
        Simulate single order placement
        
        Args:
            **customer_kwargs: Optional customer overrides
                - customer_email
                - customer_phone
                - customer_name
        
        Returns:
            Result dict
        """
        payload = self.generate_order(**customer_kwargs)
        result = self.place_order(payload)
        
        return {
            "payload": payload,
            "result": result
        }
    
    def simulate_batch_orders(self, count=5, delay=1.0):
        """
        Simulate multiple orders in sequence
        
        Args:
            count: Number of orders to create
            delay: Delay between orders in seconds
        
        Returns:
            List of results
        """
        results = []
        
        for i in range(count):
            print(f"\n📦 Creating order {i+1}/{count}...")
            
            order_data = self.simulate_single_order()
            results.append(order_data)
            
            order_id = order_data["payload"]["order_id"]
            
            if order_data["result"]["success"]:
                print(f"   ✅ Order {order_id} created successfully")
            else:
                error = order_data["result"].get("error", "Unknown error")
                print(f"   ❌ Order {order_id} failed: {error}")
            
            if i < count - 1:  # Don't delay after last order
                time.sleep(delay)
        
        return results


def interactive_menu():
    """Interactive CLI for order simulation"""
    simulator = OrderSimulator()
    
    print("=" * 60)
    print("🚀 ORDER PLACEMENT SIMULATOR")
    print("=" * 60)
    print()
    
    while True:
        print("\nOptions:")
        print("1. Create single order (random customer)")
        print("2. Create single order (specific customer)")
        print("3. Create batch of orders (5)")
        print("4. Create batch of orders (custom count)")
        print("5. Exit")
        print()
        
        choice = input("Enter choice (1-5): ").strip()
        
        if choice == "1":
            print("\n📦 Creating random order...")
            result = simulator.simulate_single_order()
            
            print(f"\nOrder Details:")
            print(f"  Order ID: {result['payload']['order_id']}")
            print(f"  Customer: {result['payload']['customer']['name']}")
            print(f"  Email: {result['payload']['customer']['email']}")
            print(f"  Phone: {result['payload']['customer']['phone']}")
            print(f"  Items: {len(result['payload']['items'])}")
            print(f"  Total: ₹{result['payload']['totals']['total']:.2f}")
            
            if result["result"]["success"]:
                print(f"\n✅ Order created successfully!")
                print(f"   Response: {result['result']['response']}")
            else:
                print(f"\n❌ Order creation failed!")
                print(f"   Error: {result['result'].get('error', 'Unknown')}")
        
        elif choice == "2":
            print("\n📝 Enter customer details:")
            email = input("  Email: ").strip()
            phone = input("  Phone (10 digits): ").strip()
            name = input("  Name: ").strip()
            
            result = simulator.simulate_single_order(
                customer_email=email or None,
                customer_phone=phone or None,
                customer_name=name or None
            )
            
            if result["result"]["success"]:
                print(f"\n✅ Order {result['result']['order_id']} created!")
            else:
                print(f"\n❌ Failed: {result['result'].get('error')}")
        
        elif choice == "3":
            print("\n📦 Creating batch of 5 orders...")
            results = simulator.simulate_batch_orders(count=5, delay=0.5)
            
            successful = sum(1 for r in results if r["result"]["success"])
            print(f"\n✅ {successful}/{len(results)} orders created successfully")
        
        elif choice == "4":
            try:
                count = int(input("\nHow many orders? "))
                print(f"\n📦 Creating batch of {count} orders...")
                results = simulator.simulate_batch_orders(count=count, delay=0.5)
                
                successful = sum(1 for r in results if r["result"]["success"])
                print(f"\n✅ {successful}/{len(results)} orders created successfully")
            except ValueError:
                print("❌ Invalid number")
        
        elif choice == "5":
            print("\n👋 Goodbye!")
            break
        
        else:
            print("❌ Invalid choice")


def quick_test():
    """Quick test - create 3 orders and verify"""
    simulator = OrderSimulator()
    
    print("🧪 QUICK TEST MODE")
    print("=" * 60)
    print("\n📦 Creating 3 test orders...\n")
    
    results = simulator.simulate_batch_orders(count=3, delay=1.0)
    
    print("\n" + "=" * 60)
    print("📊 SUMMARY")
    print("=" * 60)
    
    successful = [r for r in results if r["result"]["success"]]
    failed = [r for r in results if not r["result"]["success"]]
    
    print(f"\n✅ Successful: {len(successful)}")
    print(f"❌ Failed: {len(failed)}")
    
    if successful:
        print("\n📋 Created Orders:")
        for r in successful:
            print(f"   • {r['payload']['order_id']} - {r['payload']['customer']['email']} - ₹{r['payload']['totals']['total']:.2f}")
    
    print("\n" + "=" * 60)
    print("💡 Now try querying the chatbot:")
    print("   • Visit http://localhost:5001")
    for r in successful[:2]:
        print(f"   • Ask: 'Track {r['payload']['order_id']}'")
        print(f"   • Or: '{r['payload']['customer']['email']}'")
    print("=" * 60)


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "--quick":
        quick_test()
    else:
        interactive_menu()
