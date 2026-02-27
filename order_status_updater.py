"""
Background Order Status Updater
Automatically progresses order statuses to simulate real-time carrier updates
In production, replace with actual carrier webhook integration
"""

import time
import threading
import logging
from datetime import datetime, timedelta
from order_service import OrderService

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/status_updater.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class OrderStatusUpdater:
    """
    Background service that automatically updates order statuses
    
    Simulates carrier updates by:
    - Checking orders every N seconds
    - Applying status progression logic
    - Logging all changes
    
    In production: Replace with real carrier webhook handlers
    """
    
    def __init__(self, order_service=None, interval=60):
        """
        Initialize status updater
        
        Args:
            order_service: OrderService instance (None = create new)
            interval: Update interval in seconds (default: 60)
        """
        self.order_service = order_service or OrderService()
        self.interval = interval
        self.running = False
        self.thread = None
        
        logger.info(f"OrderStatusUpdater initialized (interval={interval}s)")
    
    def start(self):
        """Start background updater thread"""
        if self.running:
            logger.warning("Status updater already running")
            return
        
        self.running = True
        self.thread = threading.Thread(target=self._run, daemon=True, name="StatusUpdater")
        self.thread.start()
        logger.info("✅ Status updater started")
    
    def stop(self):
        """Stop background updater thread"""
        if not self.running:
            return
        
        logger.info("Stopping status updater...")
        self.running = False
        
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=self.interval + 5)
        
        logger.info("✅ Status updater stopped")
    
    def _run(self):
        """Main update loop (runs in background thread)"""
        logger.info("Status updater loop started")
        
        while self.running:
            try:
                start_time = time.time()
                
                # Update all pending orders
                stats = self._update_pending_orders()
                
                elapsed = time.time() - start_time
                logger.info(
                    f"Update cycle completed in {elapsed:.2f}s - "
                    f"Checked: {stats['checked']}, Updated: {stats['updated']}"
                )
                
            except Exception as e:
                logger.error(f"Error in status updater: {e}", exc_info=True)
            
            # Sleep until next cycle
            time.sleep(self.interval)
        
        logger.info("Status updater loop exited")
    
    def _update_pending_orders(self):
        """
        Find and update orders that aren't in terminal states
        
        Returns:
            dict: Statistics (checked count, updated count)
        """
        stats = {'checked': 0, 'updated': 0}
        
        # Get all active orders from database
        # (orders not yet delivered or cancelled)
        active_orders = self._get_active_orders()
        stats['checked'] = len(active_orders)
        
        for order in active_orders:
            try:
                # Refresh order status (applies progression logic)
                updated_order = self.order_service.refresh_order_status(order['order_id'])
                
                # Check if status actually changed
                if updated_order['shipment_status'] != order['shipment_status']:
                    stats['updated'] += 1
                    logger.info(
                        f"📦 Order {order['order_id']}: "
                        f"{order['shipment_status']} → {updated_order['shipment_status']}"
                    )
                    
                    # Log to status change file
                    self._log_status_change(
                        order['order_id'],
                        order['shipment_status'],
                        updated_order['shipment_status']
                    )
            
            except Exception as e:
                logger.error(f"Failed to update {order.get('order_id', 'UNKNOWN')}: {e}")
        
        return stats
    
    def _get_active_orders(self):
        """
        Get orders that need status updates
        
        Returns:
            list: Orders with status != delivered and != cancelled
        """
        # Access database directly for efficiency
        if self.order_service.use_sqlite:
            return self._get_active_orders_sqlite()
        else:
            # PostgreSQL implementation
            return self._get_active_orders_postgresql()
    
    def _get_active_orders_sqlite(self):
        """Get active orders from SQLite"""
        import sqlite3
        import json
        
        conn = sqlite3.connect(self.order_service.db_file)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                SELECT order_id, email, phone, items,payment_status, shipment_status,
                       carrier, tracking_id, expected_delivery, last_updated
                FROM orders
                WHERE shipment_status NOT IN ('delivered', 'cancelled')
            """)
            
            rows = cursor.fetchall()
            
            orders = []
            for row in rows:
                orders.append({
                    'order_id': row['order_id'],
                    'email': row['email'],
                    'phone': row['phone'],
                    'items': json.loads(row['items']) if row['items'] else [],
                    'payment_status': row['payment_status'],
                    'shipment_status': row['shipment_status'],
                    'carrier': row['carrier'],
                    'tracking_id': row['tracking_id'],
                    'expected_delivery': row['expected_delivery'],
                    'last_updated': row['last_updated']
                })
            
            return orders
        
        finally:
            conn.close()
    
    def _get_active_orders_postgresql(self):
        """Get active orders from PostgreSQL (future implementation)"""
        # TODO: Implement PostgreSQL query
        return []
    
    def _log_status_change(self, order_id, old_status, new_status):
        """Log status change to file"""
        import os
        import json
        
        os.makedirs('logs', exist_ok=True)
        
        log_entry = {
            'order_id': order_id,
            'old_status': old_status,
            'new_status': new_status,
            'timestamp': datetime.now().isoformat(),
            'updated_by': 'background_updater'
        }
        
        try:
            with open('logs/order_status_changes.log', 'a') as f:
                f.write(json.dumps(log_entry) + '\n')
        except Exception as e:
            logger.error(f"Failed to log status change: {e}")


def main():
    """
    Standalone execution for testing
    """
    import os
    os.makedirs('logs', exist_ok=True)
    
    print("🚀 Starting Order Status Updater (standalone mode)")
    print("Press Ctrl+C to stop\n")
    
    updater = OrderStatusUpdater(interval=30)  # 30s for testing
    updater.start()
    
    try:
        # Keep main thread alive
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n\n⏹️  Stopping updater...")
        updater.stop()
        print("✅ Updater stopped cleanly")


if __name__ == "__main__":
    main()
