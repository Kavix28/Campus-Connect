"""
User Service - User Management & Authentication
Handles user creation, authentication, and session management
"""

import os
import sqlite3
import json
import hashlib
import secrets
from datetime import datetime, timedelta
from typing import Optional, Dict, Any


class UserService:
    """
    Manages user accounts, authentication, and user-order mapping.
    Supports both SQLite and PostgreSQL backends.
    """
    
    def __init__(self):
        self.db_file = os.getenv("DATABASE_PATH", "./data/oudience.db")
        self.use_sqlite = os.getenv("DATABASE_TYPE", "sqlite") == "sqlite"
        self._init_storage()
    
    def _init_storage(self):
        """Initialize user storage (SQLite or PostgreSQL)"""
        if self.use_sqlite:
            self._init_sqlite()
        else:
            # PostgreSQL initialization handled by migrations
            pass
    
    def _init_sqlite(self):
        """Initialize SQLite database with users table"""
        os.makedirs(os.path.dirname(self.db_file) if os.path.dirname(self.db_file) else ".", exist_ok=True)
        
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        
        # Create users table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT UNIQUE NOT NULL,
                phone TEXT UNIQUE,
                full_name TEXT,
                password_hash TEXT,
                is_verified INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_login TIMESTAMP,
                metadata TEXT
            )
        """)
        
        # Create sessions table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                session_token TEXT UNIQUE NOT NULL,
                jwt_token TEXT,
                active_order_id TEXT,
                last_intent TEXT,
                conversation_summary TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                expires_at TIMESTAMP NOT NULL,
                last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        """)
        
        # Create indexes
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_users_email ON users(email)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_users_phone ON users(phone)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_sessions_token ON user_sessions(session_token)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_sessions_user_id ON user_sessions(user_id)")
        
        conn.commit()
        conn.close()
    
    def find_or_create_user(self, email: str = None, phone: str = None, full_name: str = None) -> Optional[Dict[str, Any]]:
        """
        Find user by email or phone, create if doesn't exist.
        This enables automatic user creation from order webhooks.
        
        Args:
            email: User email address
            phone: User phone number
            full_name: User full name (optional)
        
        Returns:
            User dictionary with id, email, phone, etc.
        """
        if not email and not phone:
            return None
        
        # Try to find existing user
        user = self.find_user(email=email, phone=phone)
        if user:
            return user
        
        # Create new user
        return self.create_user(email=email, phone=phone, full_name=full_name)
    
    def find_user(self, email: str = None, phone: str = None, user_id: int = None) -> Optional[Dict[str, Any]]:
        """Find user by email, phone, or user_id"""
        if self.use_sqlite:
            return self._find_user_sqlite(email, phone, user_id)
        else:
            # PostgreSQL implementation
            pass
    
    def _find_user_sqlite(self, email: str = None, phone: str = None, user_id: int = None) -> Optional[Dict[str, Any]]:
        """Find user in SQLite database"""
        conn = sqlite3.connect(self.db_file)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        try:
            if user_id:
                cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
            elif email:
                cursor.execute("SELECT * FROM users WHERE email = ? COLLATE NOCASE", (email,))
            elif phone:
                cursor.execute("SELECT * FROM users WHERE phone = ?", (phone,))
            else:
                return None
            
            row = cursor.fetchone()
            if not row:
                return None
            
            return {
                "id": row["id"],
                "email": row["email"],
                "phone": row["phone"],
                "full_name": row["full_name"],
                "is_verified": bool(row["is_verified"]),
                "created_at": row["created_at"],
                "last_login": row["last_login"],
                "metadata": json.loads(row["metadata"]) if row["metadata"] else {}
            }
        finally:
            conn.close()
    
    def create_user(self, email: str = None, phone: str = None, full_name: str = None, password_hash: str = None) -> Dict[str, Any]:
        """Create new user"""
        if self.use_sqlite:
            return self._create_user_sqlite(email, phone, full_name, password_hash)
        else:
            # PostgreSQL implementation
            pass
    
    def _create_user_sqlite(self, email: str, phone: str, full_name: str, password_hash: str) -> Dict[str, Any]:
        """Create user in SQLite database"""
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                INSERT INTO users (email, phone, full_name, password_hash, metadata)
                VALUES (?, ?, ?, ?, ?)
            """, (email, phone, full_name, password_hash, json.dumps({})))
            
            user_id = cursor.lastrowid
            conn.commit()
            
            return {
                "id": user_id,
                "email": email,
                "phone": phone,
                "full_name": full_name,
                "is_verified": False,
                "created_at": datetime.now().isoformat(),
                "metadata": {}
            }
        finally:
            conn.close()
    
    def create_session(self, user_id: int, expires_in_seconds: int = 1800) -> str:
        """
        Create session for user.
        
        Args:
            user_id: User ID
            expires_in_seconds: Session lifetime (default 30 minutes)
        
        Returns:
            Session token string
        """
        session_token = secrets.token_urlsafe(32)
        expires_at = datetime.now() + timedelta(seconds=expires_in_seconds)
        
        if self.use_sqlite:
            conn = sqlite3.connect(self.db_file)
            cursor = conn.cursor()
            
            try:
                cursor.execute("""
                    INSERT INTO user_sessions (user_id, session_token, expires_at)
                    VALUES (?, ?, ?)
                """, (user_id, session_token, expires_at.isoformat()))
                conn.commit()
            finally:
                conn.close()
        
        return session_token
    
    def get_session(self, session_token: str) -> Optional[Dict[str, Any]]:
        """Get session by token, return None if expired or invalid"""
        if self.use_sqlite:
            conn = sqlite3.connect(self.db_file)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            try:
                cursor.execute("""
                    SELECT * FROM user_sessions 
                    WHERE session_token = ? AND expires_at > datetime('now')
                """, (session_token,))
                
                row = cursor.fetchone()
                if not row:
                    return None
                
                # Update last_activity
                cursor.execute("""
                    UPDATE user_sessions 
                    SET last_activity = CURRENT_TIMESTAMP 
                    WHERE session_token = ?
                """, (session_token,))
                conn.commit()
                
                return {
                    "id": row["id"],
                    "user_id": row["user_id"],
                    "session_token": row["session_token"],
                    "active_order_id": row["active_order_id"],
                    "last_intent": row["last_intent"],
                    "conversation_summary": row["conversation_summary"],
                    "created_at": row["created_at"],
                    "expires_at": row["expires_at"],
                    "last_activity": row["last_activity"]
                }
            finally:
                conn.close()
        
        return None
    
    def update_session(self, session_token: str, active_order_id: str = None, last_intent: str = None, conversation_summary: str = None):
        """Update session data"""
        if self.use_sqlite:
            conn = sqlite3.connect(self.db_file)
            cursor = conn.cursor()
            
            try:
                updates = []
                params = []
                
                if active_order_id is not None:
                    updates.append("active_order_id = ?")
                    params.append(active_order_id)
                
                if last_intent is not None:
                    updates.append("last_intent = ?")
                    params.append(last_intent)
                
                if conversation_summary is not None:
                    updates.append("conversation_summary = ?")
                    params.append(conversation_summary[:2000])  # Limit size
                
                if updates:
                    params.append(session_token)
                    query = f"UPDATE user_sessions SET {', '.join(updates)} WHERE session_token = ?"
                    cursor.execute(query, params)
                    conn.commit()
            finally:
                conn.close()
    
    def hash_password(self, password: str) -> str:
        """Hash password using SHA256 (for production, use bcrypt)"""
        # Simple hashing for demo - use bcrypt in production
        salt = os.getenv("SECRET_KEY", "default-salt")
        return hashlib.sha256((password + salt).encode()).hexdigest()
    
    def verify_password(self, password: str, password_hash: str) -> bool:
        """Verify password against hash"""
        return self.hash_password(password) == password_hash
    
    def get_user_orders(self, user_id: int) -> list:
        """Get all orders for a user (cross-reference with OrderService)"""
        if self.use_sqlite:
            conn = sqlite3.connect(self.db_file)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            try:
                # Check if orders table exists and has user_id column
                cursor.execute("""
                    SELECT name FROM sqlite_master 
                    WHERE type='table' AND name='orders'
                """)
                
                if not cursor.fetchone():
                    return []
                
                # Try to get orders for this user
                try:
                    cursor.execute("""
                        SELECT order_id, shipment_status, payment_status, 
                               created_at, last_updated, expected_delivery
                        FROM orders 
                        WHERE user_id = ?
                        ORDER BY created_at DESC
                    """, (user_id,))
                    
                    orders = []
                    for row in cursor.fetchall():
                        orders.append({
                            "order_id": row["order_id"],
                            "shipment_status": row["shipment_status"],
                            "payment_status": row["payment_status"],
                            "created_at": row["created_at"],
                            "last_updated": row["last_updated"],
                            "expected_delivery": row["expected_delivery"]
                        })
                    return orders
                except sqlite3.OperationalError:
                    # user_id column doesn't exist in orders table
                    return []
            finally:
                conn.close()
        
        return []
