# 🔔 Real-Time Notification System with WebSockets

## 📖 **System Overview**

This project implements a comprehensive real-time notification system using **WebSockets** to instantly notify project members when tasks are updated. The system combines both database-stored notifications and real-time WebSocket communication for the best user experience.

## 🔌 **WebSocket Concept Explained**

### **What are WebSockets?**

WebSockets provide **persistent, bidirectional communication** between client and server:

- **Traditional HTTP**: Client requests → Server responds → Connection closes
- **WebSockets**: Client connects → Persistent connection → Real-time messages both ways

### **Why WebSockets for Notifications?**

1. **Instant Delivery**: No waiting for page refresh or polling
2. **Efficient**: One connection, multiple messages
3. **Real-time**: Users see changes as they happen
4. **Interactive**: Two-way communication for acknowledgments

## 🏗️ **System Architecture**

```
┌─────────────────┐    WebSocket     ┌─────────────────┐
│   Frontend      │ ←─────────────→  │   WebSocket     │
│   (Browser)     │     Real-time    │   Manager       │
└─────────────────┘    Messages      └─────────────────┘
                                              │
                                              ▼
┌─────────────────┐    API Call      ┌─────────────────┐
│   Task Update   │ ─────────────→   │   Task API      │
│   (User Action) │                  │   Controller    │
└─────────────────┘                  └─────────────────┘
                                              │
                                              ▼
                                     ┌─────────────────┐
                                     │   Database      │
                                     │   + Notify      │
                                     │   Service       │
                                     └─────────────────┘
```

## 📁 **File Structure**

```
src/
├── services/
│   ├── websocket_manager.py      # WebSocket connection management
│   └── notification_service.py   # Database notifications
├── apis/
│   ├── websocket_api.py          # WebSocket endpoints
│   ├── task_api.py               # Task API with notifications
│   └── notification_api.py       # REST notification API
└── views/core/templates/
    └── base.html                 # Frontend WebSocket client
```

## 🔧 **Implementation Details**

### **1. WebSocket Manager (`websocket_manager.py`)**

**Key Features:**

- **Connection Management**: Tracks active user connections
- **Room Subscriptions**: Users join project "rooms"
- **Message Broadcasting**: Send to all project members
- **Auto-reconnection**: Handles connection drops

**Core Methods:**

```python
async def connect(websocket, user_id)              # Accept new connection
async def subscribe_to_projects(user_id, projects) # Join project rooms
async def broadcast_to_project(project_id, message) # Send to all members
async def notify_task_status_change(...)           # Task update notifications
```

### **2. WebSocket API (`websocket_api.py`)**

**Endpoint:** `/ws/notifications/{user_id}`

**Connection Flow:**

1. User opens WebSocket connection
2. System auto-subscribes to user's projects
3. Sends welcome message with project list
4. Maintains connection for real-time updates

**Message Types:**

```javascript
// Connection established
{
  "type": "connection_established",
  "data": {
    "message": "Connected to real-time notifications",
    "subscribed_projects": [1, 2, 3]
  }
}

// Task status update
{
  "type": "task_status_update",
  "data": {
    "task_id": 123,
    "task_title": "Design UI mockups",
    "old_status": "In Progress",
    "new_status": "Completed",
    "updated_by": "John Doe",
    "project_name": "Website Redesign",
    "message": "John Doe changed task 'Design UI mockups' from 'In Progress' to 'Completed'"
  }
}
```

### **3. Task API Integration (`task_api.py`)**

**When task status changes:**

1. Update task in database
2. Send database notification (for persistence)
3. **Send WebSocket notification (for real-time)**
4. Return updated task to client

```python
# Send real-time WebSocket notification
await websocket_manager.notify_task_status_change(
    db=db,
    task_id=task_id,
    old_status=old_status.value,
    new_status=new_status.value,
    updated_by_user_id=current_user.id
)
```

### **4. Frontend WebSocket Client (base.html)**

**Features:**

- **Auto-connection**: Connects when page loads
- **User Authentication**: Uses current user ID
- **Message Handling**: Processes different notification types
- **Browser Notifications**: Shows system notifications
- **Toast Messages**: In-app notification popups
- **Auto-reconnection**: Handles connection failures

**Key JavaScript Methods:**

```javascript
initWebSocket(); // Establish connection
handleWebSocketMessage(data); // Process incoming messages
showRealTimeNotification(data); // Display notifications
scheduleReconnect(); // Handle disconnections
```

## 🚀 **How to Test the System**

### **1. Start the Application**

```bash
# Run your FastAPI application
python main.py
```

### **2. Open the Projects Page**

- Navigate to `/projects`
- You'll see the "Quick Task Status Update" widget
- WebSocket connection auto-establishes in the background

### **3. Test Real-time Notifications**

**Single User Test:**

1. Open browser console to see WebSocket messages
2. Update a task status using the widget
3. Watch for real-time notifications in the bell icon

**Multi-User Test:**

1. Open the app in **two different browser tabs/windows**
2. Log in as different users (if you have multiple accounts)
3. Both users should be members of the same project
4. Update task status in one tab
5. **Instantly see notification in the other tab!**

### **4. Monitoring WebSocket Activity**

**Browser Console Messages:**

```
WebSocket connected for real-time notifications
Received WebSocket message: {type: "task_status_update", data: {...}}
```

**Network Tab:**

- Look for WebSocket connection to `/ws/notifications/{user_id}`
- See real-time message exchange

## 🔍 **Debugging Guide**

### **Common Issues & Solutions**

**1. WebSocket Connection Failed**

```
Error: WebSocket connection failed
```

**Solution:** Check if user ID is properly set in template:

```html
<body data-user-id="{% if user %}{{ user.id }}{% endif %}"></body>
```

**2. No Notifications Received**

```
Task updated but no notification appears
```

**Solution:** Verify:

- User is subscribed to the project
- WebSocket connection is active
- User has proper project permissions

**3. WebSocket Auto-reconnection**

```
WebSocket disconnected, attempting reconnection...
```

**Solution:** This is normal behavior. The system auto-reconnects with exponential backoff.

### **Debug Commands**

**Check WebSocket Stats:**

```
GET /ws/stats
```

Returns:

```json
{
  "active_connections": 5,
  "subscribed_users": 3,
  "projects_with_subscribers": 2,
  "total_subscriptions": 8
}
```

## 📊 **System Flow Example**

**Scenario:** John updates a task status from "In Progress" to "Completed"

1. **Frontend**: John clicks "Update Status" button
2. **API Call**: `PUT /api/tasks/123` with new status
3. **Database**: Task status updated in database
4. **Database Notification**: Notification record created for team members
5. **WebSocket Broadcast**: Real-time message sent to all project members
6. **Frontend (Other Users)**: Instant notification appears in bell icon
7. **Browser Notification**: System notification if permission granted
8. **Toast Message**: In-app popup with update details

## 🎯 **Benefits of This Implementation**

1. **Dual Persistence**: Database + Real-time ensures no lost notifications
2. **Scalable**: WebSocket manager can handle multiple projects/users
3. **Fallback**: Polling system works if WebSocket fails
4. **User-Friendly**: Visual indicators, browser notifications, and toasts
5. **Efficient**: Only project members get relevant notifications
6. **Robust**: Auto-reconnection and error handling

## 🔄 **Future Enhancements**

1. **Redis Integration**: Scale WebSocket connections across servers
2. **Push Notifications**: Mobile app notifications
3. **Email Notifications**: Configurable email alerts
4. **Notification Settings**: User preferences for notification types
5. **Message History**: Store WebSocket message history
6. **Typing Indicators**: Show when users are editing tasks
7. **Presence System**: Show online/offline status

This WebSocket notification system provides a modern, real-time experience that keeps team members instantly informed of project changes!
