---
sidebar_position: 6
---

# Real-time Features with SurrealDB

This section demonstrates how to implement real-time features using SurrealDB's live queries combined with FastAPI WebSockets, enabling real-time notifications, live data updates, and collaborative features.

## WebSocket Setup with SurrealDB Live Queries

### WebSocket Manager

```python
# app/websocket/manager.py
from fastapi import WebSocket, WebSocketDisconnect
from typing import Dict, List, Set
import json
import asyncio
from surrealdb import Surreal
from app.database import get_database
from app.auth.auth_handler import AuthHandler

class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self.user_connections: Dict[str, Set[str]] = {}  # user_id -> connection_ids
        self.connection_users: Dict[str, str] = {}  # connection_id -> user_id
        self.live_queries: Dict[str, str] = {}  # connection_id -> live_query_id
        
    async def connect(self, websocket: WebSocket, connection_id: str, user_id: str):
        """Accept WebSocket connection and associate with user"""
        await websocket.accept()
        self.active_connections[connection_id] = websocket
        self.connection_users[connection_id] = user_id
        
        if user_id not in self.user_connections:
            self.user_connections[user_id] = set()
        self.user_connections[user_id].add(connection_id)
        
        print(f"User {user_id} connected with connection {connection_id}")
    
    def disconnect(self, connection_id: str):
        """Remove WebSocket connection"""
        if connection_id in self.active_connections:
            user_id = self.connection_users.get(connection_id)
            
            # Clean up connection mappings
            del self.active_connections[connection_id]
            if connection_id in self.connection_users:
                del self.connection_users[connection_id]
            
            # Clean up user connections
            if user_id and user_id in self.user_connections:
                self.user_connections[user_id].discard(connection_id)
                if not self.user_connections[user_id]:
                    del self.user_connections[user_id]
            
            # Clean up live queries
            if connection_id in self.live_queries:
                del self.live_queries[connection_id]
            
            print(f"Connection {connection_id} disconnected")
    
    async def send_personal_message(self, message: dict, connection_id: str):
        """Send message to specific connection"""
        if connection_id in self.active_connections:
            websocket = self.active_connections[connection_id]
            try:
                await websocket.send_text(json.dumps(message))
            except Exception as e:
                print(f"Error sending message to {connection_id}: {e}")
                self.disconnect(connection_id)
    
    async def send_user_message(self, message: dict, user_id: str):
        """Send message to all connections of a specific user"""
        if user_id in self.user_connections:
            for connection_id in self.user_connections[user_id].copy():
                await self.send_personal_message(message, connection_id)
    
    async def broadcast_to_admins(self, message: dict, db: Surreal):
        """Send message to all admin users"""
        # Get all admin user IDs
        result = await db.query("SELECT id FROM user WHERE is_admin = true AND is_active = true")
        admin_users = result[0]["result"] if result and result[0]["result"] else []
        
        for admin_user in admin_users:
            admin_id = admin_user["id"].split(":")[1]
            await self.send_user_message(message, admin_id)
    
    async def broadcast_message(self, message: dict):
        """Broadcast message to all connected users"""
        for connection_id in list(self.active_connections.keys()):
            await self.send_personal_message(message, connection_id)

# Global connection manager
manager = ConnectionManager()
```

### Real-time Service with Live Queries

```python
# app/services/realtime_service.py
from surrealdb import Surreal
from typing import Dict, Any, Callable
import asyncio
import json
from datetime import datetime

class RealtimeService:
    def __init__(self, db: Surreal, connection_manager):
        self.db = db
        self.manager = connection_manager
        self.live_queries: Dict[str, Any] = {}
        
    async def setup_global_live_queries(self):
        """Set up global live queries for system-wide events"""
        
        try:
            # Live query for user registrations
            user_live_id = await self.db.live("user", callback=self._handle_user_changes)
            self.live_queries["user_changes"] = user_live_id
            
            # Live query for session activity
            session_live_id = await self.db.live("session", callback=self._handle_session_changes)
            self.live_queries["session_changes"] = session_live_id
            
            # Live query for profile updates
            profile_live_id = await self.db.live("profile", callback=self._handle_profile_changes)
            self.live_queries["profile_changes"] = profile_live_id
            
            print("Global live queries set up successfully")
            
        except Exception as e:
            print(f"Error setting up live queries: {e}")
    
    async def _handle_user_changes(self, change: Dict):
        """Handle user table changes"""
        action = change.get("action")
        result = change.get("result", {})
        
        if action == "CREATE":
            # Notify admins of new user registration
            message = {
                "type": "user_registered",
                "data": {
                    "user_id": result.get("id", "").split(":")[-1],
                    "username": result.get("username"),
                    "email": result.get("email"),
                    "timestamp": datetime.utcnow().isoformat()
                }
            }
            await self.manager.broadcast_to_admins(message, self.db)
            
        elif action == "UPDATE":
            # Notify user of their own profile updates
            user_id = result.get("id", "").split(":")[-1]
            message = {
                "type": "profile_updated",
                "data": {
                    "user_id": user_id,
                    "changes": result,
                    "timestamp": datetime.utcnow().isoformat()
                }
            }
            await self.manager.send_user_message(message, user_id)
    
    async def _handle_session_changes(self, change: Dict):
        """Handle session table changes"""
        action = change.get("action")
        result = change.get("result", {})
        
        if action == "CREATE":
            # Notify user of new login
            user_record = result.get("user", "")
            if isinstance(user_record, str) and ":" in user_record:
                user_id = user_record.split(":")[-1]
                message = {
                    "type": "new_session",
                    "data": {
                        "session_id": result.get("id", "").split(":")[-1],
                        "timestamp": datetime.utcnow().isoformat()
                    }
                }
                await self.manager.send_user_message(message, user_id)
        
        elif action == "DELETE":
            # Notify user of session termination
            user_record = result.get("user", "")
            if isinstance(user_record, str) and ":" in user_record:
                user_id = user_record.split(":")[-1]
                message = {
                    "type": "session_ended",
                    "data": {
                        "session_id": result.get("id", "").split(":")[-1],
                        "timestamp": datetime.utcnow().isoformat()
                    }
                }
                await self.manager.send_user_message(message, user_id)
    
    async def _handle_profile_changes(self, change: Dict):
        """Handle profile table changes"""
        action = change.get("action")
        result = change.get("result", {})
        
        if action in ["CREATE", "UPDATE"]:
            # Notify user of profile changes
            user_record = result.get("user", "")
            if isinstance(user_record, str) and ":" in user_record:
                user_id = user_record.split(":")[-1]
                message = {
                    "type": "profile_changed",
                    "data": {
                        "profile_id": result.get("id", "").split(":")[-1],
                        "action": action.lower(),
                        "timestamp": datetime.utcnow().isoformat()
                    }
                }
                await self.manager.send_user_message(message, user_id)
    
    async def setup_user_specific_live_query(self, user_id: str, connection_id: str):
        """Set up user-specific live queries"""
        
        try:
            # Live query for user's own data changes
            user_query = f"SELECT * FROM user:{user_id}"
            user_live_id = await self.db.live(user_query, callback=lambda change: self._handle_user_specific_changes(change, connection_id))
            
            # Live query for user's profile changes
            profile_query = f"SELECT * FROM profile WHERE user = user:{user_id}"
            profile_live_id = await self.db.live(profile_query, callback=lambda change: self._handle_user_profile_changes(change, connection_id))
            
            # Store live query IDs for cleanup
            self.manager.live_queries[connection_id] = {
                "user": user_live_id,
                "profile": profile_live_id
            }
            
            return True
            
        except Exception as e:
            print(f"Error setting up user-specific live queries: {e}")
            return False
    
    async def _handle_user_specific_changes(self, change: Dict, connection_id: str):
        """Handle user-specific changes"""
        message = {
            "type": "user_data_changed",
            "data": {
                "action": change.get("action"),
                "changes": change.get("result", {}),
                "timestamp": datetime.utcnow().isoformat()
            }
        }
        await self.manager.send_personal_message(message, connection_id)
    
    async def _handle_user_profile_changes(self, change: Dict, connection_id: str):
        """Handle user profile-specific changes"""
        message = {
            "type": "user_profile_changed",
            "data": {
                "action": change.get("action"),
                "changes": change.get("result", {}),
                "timestamp": datetime.utcnow().isoformat()
            }
        }
        await self.manager.send_personal_message(message, connection_id)
    
    async def cleanup_live_queries(self, connection_id: str):
        """Clean up live queries for a connection"""
        if connection_id in self.manager.live_queries:
            live_queries = self.manager.live_queries[connection_id]
            for query_type, query_id in live_queries.items():
                try:
                    await self.db.kill(query_id)
                except Exception as e:
                    print(f"Error killing live query {query_type}: {e}")
```

## WebSocket Endpoints

### Main WebSocket Endpoint

```python
# app/routers/websocket.py
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, HTTPException, Query
from surrealdb import Surreal
import json
import uuid
from app.database import get_database
from app.auth.auth_handler import AuthHandler
from app.websocket.manager import manager
from app.services.realtime_service import RealtimeService

router = APIRouter()

async def get_realtime_service(db: Surreal = Depends(get_database)) -> RealtimeService:
    """Dependency to get realtime service"""
    return RealtimeService(db, manager)

@router.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket,
    token: str = Query(..., description="JWT authentication token"),
    db: Surreal = Depends(get_database),
    realtime_service: RealtimeService = Depends(get_realtime_service)
):
    """
    Main WebSocket endpoint for real-time communication
    Requires JWT token for authentication
    """
    
    connection_id = str(uuid.uuid4())
    
    try:
        # Authenticate user
        auth_handler = AuthHandler(db)
        token_data = await auth_handler.verify_token(token)
        
        if not token_data:
            await websocket.close(code=4001, reason="Invalid token")
            return
        
        user_id = token_data["user_id"]
        
        # Accept connection
        await manager.connect(websocket, connection_id, user_id)
        
        # Set up user-specific live queries
        await realtime_service.setup_user_specific_live_query(user_id, connection_id)
        
        # Send welcome message
        welcome_message = {
            "type": "connected",
            "data": {
                "connection_id": connection_id,
                "user_id": user_id,
                "timestamp": datetime.utcnow().isoformat()
            }
        }
        await manager.send_personal_message(welcome_message, connection_id)
        
        # Handle incoming messages
        while True:
            try:
                data = await websocket.receive_text()
                message = json.loads(data)
                await handle_websocket_message(message, connection_id, user_id, db, realtime_service)
                
            except WebSocketDisconnect:
                break
            except json.JSONDecodeError:
                error_message = {
                    "type": "error",
                    "data": {"message": "Invalid JSON format"}
                }
                await manager.send_personal_message(error_message, connection_id)
            except Exception as e:
                error_message = {
                    "type": "error",
                    "data": {"message": f"Error processing message: {str(e)}"}
                }
                await manager.send_personal_message(error_message, connection_id)
                
    except Exception as e:
        print(f"WebSocket connection error: {e}")
        await websocket.close(code=4000, reason="Connection error")
    
    finally:
        # Clean up
        await realtime_service.cleanup_live_queries(connection_id)
        manager.disconnect(connection_id)

async def handle_websocket_message(message: dict, connection_id: str, user_id: str, db: Surreal, realtime_service: RealtimeService):
    """Handle incoming WebSocket messages"""
    
    message_type = message.get("type")
    data = message.get("data", {})
    
    if message_type == "ping":
        # Respond to ping with pong
        response = {
            "type": "pong",
            "data": {"timestamp": datetime.utcnow().isoformat()}
        }
        await manager.send_personal_message(response, connection_id)
    
    elif message_type == "subscribe_user_activity":
        # Subscribe to specific user activity (admin only)
        target_user_id = data.get("user_id")
        
        # Check if current user is admin
        user = await db.select(f"user:{user_id}")
        if not user or not user.get("is_admin", False):
            error_response = {
                "type": "error",
                "data": {"message": "Admin access required"}
            }
            await manager.send_personal_message(error_response, connection_id)
            return
        
        # Set up live query for target user
        await realtime_service.setup_user_specific_live_query(target_user_id, connection_id)
        
        response = {
            "type": "subscribed",
            "data": {
                "subscription": "user_activity",
                "target_user_id": target_user_id
            }
        }
        await manager.send_personal_message(response, connection_id)
    
    elif message_type == "get_online_users":
        # Get list of currently online users
        online_users = []
        for uid, connections in manager.user_connections.items():
            if connections:  # User has active connections
                user_data = await db.select(f"user:{uid}")
                if user_data:
                    online_users.append({
                        "user_id": uid,
                        "username": user_data.get("username"),
                        "connection_count": len(connections)
                    })
        
        response = {
            "type": "online_users",
            "data": {
                "users": online_users,
                "total_online": len(online_users)
            }
        }
        await manager.send_personal_message(response, connection_id)
    
    elif message_type == "send_admin_message":
        # Send message to all admins (admin only)
        user = await db.select(f"user:{user_id}")
        if not user or not user.get("is_admin", False):
            error_response = {
                "type": "error",
                "data": {"message": "Admin access required"}
            }
            await manager.send_personal_message(error_response, connection_id)
            return
        
        admin_message = {
            "type": "admin_broadcast",
            "data": {
                "message": data.get("message"),
                "from_user": user.get("username"),
                "timestamp": datetime.utcnow().isoformat()
            }
        }
        await manager.broadcast_to_admins(admin_message, db)
    
    else:
        # Unknown message type
        error_response = {
            "type": "error",
            "data": {"message": f"Unknown message type: {message_type}"}
        }
        await manager.send_personal_message(error_response, connection_id)
```

### Admin WebSocket Endpoint

```python
@router.websocket("/ws/admin")
async def admin_websocket_endpoint(
    websocket: WebSocket,
    token: str = Query(..., description="JWT authentication token"),
    db: Surreal = Depends(get_database),
    realtime_service: RealtimeService = Depends(get_realtime_service)
):
    """
    Admin-specific WebSocket endpoint with enhanced monitoring capabilities
    """
    
    connection_id = str(uuid.uuid4())
    
    try:
        # Authenticate and verify admin status
        auth_handler = AuthHandler(db)
        token_data = await auth_handler.verify_token(token)
        
        if not token_data:
            await websocket.close(code=4001, reason="Invalid token")
            return
        
        user_id = token_data["user_id"]
        user = await db.select(f"user:{user_id}")
        
        if not user or not user.get("is_admin", False):
            await websocket.close(code=4003, reason="Admin access required")
            return
        
        # Accept connection
        await manager.connect(websocket, connection_id, user_id)
        
        # Set up admin-specific live queries
        await setup_admin_live_queries(connection_id, db, realtime_service)
        
        # Send admin welcome message with system stats
        system_stats = await get_system_stats(db)
        welcome_message = {
            "type": "admin_connected",
            "data": {
                "connection_id": connection_id,
                "user_id": user_id,
                "system_stats": system_stats,
                "timestamp": datetime.utcnow().isoformat()
            }
        }
        await manager.send_personal_message(welcome_message, connection_id)
        
        # Handle admin messages
        while True:
            try:
                data = await websocket.receive_text()
                message = json.loads(data)
                await handle_admin_websocket_message(message, connection_id, user_id, db, realtime_service)
                
            except WebSocketDisconnect:
                break
            except Exception as e:
                error_message = {
                    "type": "error",
                    "data": {"message": f"Error: {str(e)}"}
                }
                await manager.send_personal_message(error_message, connection_id)
                
    except Exception as e:
        print(f"Admin WebSocket error: {e}")
        await websocket.close(code=4000, reason="Connection error")
    
    finally:
        await realtime_service.cleanup_live_queries(connection_id)
        manager.disconnect(connection_id)

async def setup_admin_live_queries(connection_id: str, db: Surreal, realtime_service: RealtimeService):
    """Set up admin-specific live queries"""
    
    # Live query for all user activities
    all_users_query = "SELECT * FROM user"
    user_live_id = await db.live(all_users_query, callback=lambda change: handle_admin_user_changes(change, connection_id))
    
    # Live query for system-wide session activities
    all_sessions_query = "SELECT * FROM session"
    session_live_id = await db.live(all_sessions_query, callback=lambda change: handle_admin_session_changes(change, connection_id))
    
    # Store live query IDs
    manager.live_queries[connection_id] = {
        "admin_users": user_live_id,
        "admin_sessions": session_live_id
    }

async def handle_admin_user_changes(change: Dict, connection_id: str):
    """Handle user changes for admin monitoring"""
    message = {
        "type": "admin_user_change",
        "data": {
            "action": change.get("action"),
            "user_data": change.get("result", {}),
            "timestamp": datetime.utcnow().isoformat()
        }
    }
    await manager.send_personal_message(message, connection_id)

async def handle_admin_session_changes(change: Dict, connection_id: str):
    """Handle session changes for admin monitoring"""
    message = {
        "type": "admin_session_change",
        "data": {
            "action": change.get("action"),
            "session_data": change.get("result", {}),
            "timestamp": datetime.utcnow().isoformat()
        }
    }
    await manager.send_personal_message(message, connection_id)

async def get_system_stats(db: Surreal) -> Dict:
    """Get current system statistics"""
    
    result = await db.query("""
        SELECT 
            count() AS total_users,
            count(is_active = true) AS active_users,
            count(is_admin = true) AS admin_users
        FROM user;
        
        SELECT count() AS total_sessions FROM session;
        SELECT count() AS active_sessions FROM session WHERE expires_at > time::now();
        SELECT count() AS total_profiles FROM profile;
    """)
    
    return {
        "users": result[0]["result"][0] if result and result[0]["result"] else {},
        "total_sessions": result[1]["result"][0]["total_sessions"] if len(result) > 1 and result[1]["result"] else 0,
        "active_sessions": result[2]["result"][0]["active_sessions"] if len(result) > 2 and result[2]["result"] else 0,
        "total_profiles": result[3]["result"][0]["total_profiles"] if len(result) > 3 and result[3]["result"] else 0
    }

async def handle_admin_websocket_message(message: dict, connection_id: str, user_id: str, db: Surreal, realtime_service: RealtimeService):
    """Handle admin-specific WebSocket messages"""
    
    message_type = message.get("type")
    data = message.get("data", {})
    
    if message_type == "get_system_stats":
        stats = await get_system_stats(db)
        response = {
            "type": "system_stats",
            "data": stats
        }
        await manager.send_personal_message(response, connection_id)
    
    elif message_type == "force_user_logout":
        target_user_id = data.get("user_id")
        
        # Revoke all sessions for the user
        auth_handler = AuthHandler(db)
        success = await auth_handler.revoke_all_user_sessions(target_user_id)
        
        # Notify the target user
        if success:
            logout_message = {
                "type": "forced_logout",
                "data": {
                    "reason": "Admin action",
                    "timestamp": datetime.utcnow().isoformat()
                }
            }
            await manager.send_user_message(logout_message, target_user_id)
        
        response = {
            "type": "user_logout_result",
            "data": {
                "user_id": target_user_id,
                "success": success
            }
        }
        await manager.send_personal_message(response, connection_id)
    
    elif message_type == "broadcast_system_message":
        system_message = {
            "type": "system_announcement",
            "data": {
                "message": data.get("message"),
                "priority": data.get("priority", "normal"),
                "timestamp": datetime.utcnow().isoformat()
            }
        }
        await manager.broadcast_message(system_message)
        
        response = {
            "type": "broadcast_sent",
            "data": {"message": "System message broadcasted successfully"}
        }
        await manager.send_personal_message(response, connection_id)
```

## Real-time Notifications

### Notification Service

```python
# app/services/notification_service.py
from typing import Dict, List
from datetime import datetime
from surrealdb import Surreal
from app.websocket.manager import manager

class NotificationService:
    def __init__(self, db: Surreal):
        self.db = db
    
    async def send_user_notification(self, user_id: str, notification: Dict):
        """Send notification to specific user"""
        
        # Store notification in database
        notification_data = {
            "user": f"user:{user_id}",
            "type": notification.get("type"),
            "title": notification.get("title"),
            "message": notification.get("message"),
            "data": notification.get("data", {}),
            "read": False,
            "created_at": datetime.utcnow().isoformat()
        }
        
        # Save to database
        await self.db.create("notification", notification_data)
        
        # Send real-time notification if user is online
        realtime_message = {
            "type": "notification",
            "data": notification_data
        }
        await manager.send_user_message(realtime_message, user_id)
    
    async def send_bulk_notifications(self, user_ids: List[str], notification: Dict):
        """Send notification to multiple users"""
        
        for user_id in user_ids:
            await self.send_user_notification(user_id, notification)
    
    async def send_admin_alert(self, alert: Dict):
        """Send alert to all admin users"""
        
        # Get all admin users
        result = await self.db.query("SELECT id FROM user WHERE is_admin = true AND is_active = true")
        admin_users = result[0]["result"] if result and result[0]["result"] else []
        
        for admin_user in admin_users:
            admin_id = admin_user["id"].split(":")[1]
            await self.send_user_notification(admin_id, {
                "type": "admin_alert",
                "title": alert.get("title", "Admin Alert"),
                "message": alert.get("message"),
                "data": alert.get("data", {}),
                "priority": "high"
            })
    
    async def get_user_notifications(self, user_id: str, unread_only: bool = False) -> List[Dict]:
        """Get user notifications"""
        
        condition = "user = $user_record"
        if unread_only:
            condition += " AND read = false"
        
        result = await self.db.query(f"""
            SELECT * FROM notification 
            WHERE {condition}
            ORDER BY created_at DESC
            LIMIT 50
        """, {"user_record": f"user:{user_id}"})
        
        return result[0]["result"] if result and result[0]["result"] else []
    
    async def mark_notification_read(self, notification_id: str, user_id: str) -> bool:
        """Mark notification as read"""
        
        result = await self.db.query("""
            UPDATE notification SET read = true, read_at = time::now()
            WHERE id = $notification_id AND user = $user_record
        """, {
            "notification_id": f"notification:{notification_id}",
            "user_record": f"user:{user_id}"
        })
        
        return bool(result and result[0]["result"])
    
    async def mark_all_notifications_read(self, user_id: str) -> int:
        """Mark all user notifications as read"""
        
        result = await self.db.query("""
            UPDATE notification SET read = true, read_at = time::now()
            WHERE user = $user_record AND read = false
        """, {"user_record": f"user:{user_id}"})
        
        return len(result[0]["result"]) if result and result[0]["result"] else 0
```

## Client-Side Integration Examples

### JavaScript WebSocket Client

```javascript
// client/websocket-client.js
class RealtimeClient {
    constructor(token, isAdmin = false) {
        this.token = token;
        this.isAdmin = isAdmin;
        this.ws = null;
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 5;
        this.reconnectDelay = 1000;
        this.eventHandlers = {};
    }
    
    connect() {
        const wsUrl = this.isAdmin 
            ? `ws://localhost:8000/ws/admin?token=${this.token}`
            : `ws://localhost:8000/ws?token=${this.token}`;
        
        this.ws = new WebSocket(wsUrl);
        
        this.ws.onopen = () => {
            console.log('WebSocket connected');
            this.reconnectAttempts = 0;
            this.emit('connected');
        };
        
        this.ws.onmessage = (event) => {
            try {
                const message = JSON.parse(event.data);
                this.handleMessage(message);
            } catch (error) {
                console.error('Error parsing WebSocket message:', error);
            }
        };
        
        this.ws.onclose = (event) => {
            console.log('WebSocket disconnected:', event.code, event.reason);
            this.emit('disconnected', { code: event.code, reason: event.reason });
            
            if (event.code !== 1000 && this.reconnectAttempts < this.maxReconnectAttempts) {
                this.reconnect();
            }
        };
        
        this.ws.onerror = (error) => {
            console.error('WebSocket error:', error);
            this.emit('error', error);
        };
    }
    
    reconnect() {
        this.reconnectAttempts++;
        console.log(`Attempting to reconnect (${this.reconnectAttempts}/${this.maxReconnectAttempts})`);
        
        setTimeout(() => {
            this.connect();