import pytest
from unittest.mock import MagicMock, AsyncMock, patch
import json

from src.controllers.notification_controller import NotificationController

class TestNotificationController:
    """Tests for the notification controller"""
    
    def setup_method(self):
        """Setup before each test"""
        self.controller = NotificationController()
    
    def test_get_notifications(self):
        """Test getting all notifications for a user"""
        # Act
        notifications = self.controller.get_notifications()
        
        # Assert
        assert isinstance(notifications, list)
        assert len(notifications) == 2
        assert notifications[0]['id'] == 1
        assert notifications[0]['message'] == 'New task assigned'
        assert notifications[0]['read'] is False
        assert notifications[1]['id'] == 2
        assert notifications[1]['read'] is True
    
    def test_create_notification(self):
        """Test creating a new notification"""
        # Arrange
        notification_data = {
            'message': 'Test notification',
            'user_id': 1,
            'priority': 'high'
        }
        
        # Act
        result = self.controller.create_notification(notification_data)
        
        # Assert
        assert result['id'] == 3
        assert result['message'] == 'Test notification'
        assert result['user_id'] == 1
        assert result['priority'] == 'high'
        assert 'created_at' in result
    
    def test_get_notification(self):
        """Test getting a notification by ID"""
        # Act
        notification = self.controller.get_notification(5)
        
        # Assert
        assert notification['id'] == 5
        assert notification['message'] == 'Notification details'
        assert notification['read'] is False
    
    def test_mark_as_read(self):
        """Test marking a notification as read"""
        # Act
        result = self.controller.mark_as_read(7)
        
        # Assert
        assert result['id'] == 7
        assert result['read'] is True

    @pytest.mark.asyncio
    async def test_handle_websocket_receive_message(self):
        """Test websocket receiving a message"""
        # Arrange
        mock_websocket = AsyncMock()
        
        # Act & Assert
        # Need to handle the infinite loop
        with pytest.raises(StopAsyncIteration):
            # Make receive_text raise StopAsyncIteration after first call to break the loop
            mock_websocket.receive_text.side_effect = [json.dumps({"type": "test"}), StopAsyncIteration]
            await self.controller.handle_websocket(mock_websocket)
        
        # Assert
        mock_websocket.accept.assert_called_once()
        # It's called twice - once to get the message and once when it tries to continue the loop
        assert mock_websocket.receive_text.call_count == 2
        mock_websocket.send_json.assert_called_once()
        sent_data = mock_websocket.send_json.call_args[0][0]
        assert sent_data["message"] == "Notification received"
        assert "data" in sent_data
    
    @pytest.mark.asyncio
    async def test_handle_websocket_disconnect(self):
        """Test handling websocket disconnection"""
        # Arrange
        mock_websocket = AsyncMock()
        mock_websocket.receive_text.side_effect = WebSocketDisconnect()
        
        # Act
        await self.controller.handle_websocket(mock_websocket)
        
        # Assert
        mock_websocket.accept.assert_called_once()
        mock_websocket.receive_text.assert_called_once()
        # No assertions needed for disconnect handling as it's a no-op in the controller

# Import for the WebSocketDisconnect test
from fastapi import WebSocketDisconnect

class TestNotificationIntegration:
    """Integration-style tests for notification flow"""
    
    def setup_method(self):
        self.controller = NotificationController()
    
    def test_notification_lifecycle(self):
        """Test the full lifecycle of a notification"""
        # Create a notification
        notification_data = {"message": "Lifecycle test", "user_id": 42}
        created = self.controller.create_notification(notification_data)
        notification_id = created['id']
        
        # Get the notification by ID
        fetched = self.controller.get_notification(notification_id)
        assert fetched['id'] == notification_id
        assert fetched['read'] is False
        
        # Mark as read
        updated = self.controller.mark_as_read(notification_id)
        assert updated['id'] == notification_id
        assert updated['read'] is True

class TestWebSocketNotifications:
    """Tests for WebSocket-based real-time notifications between users"""
    
    @pytest.fixture
    def notification_controller(self):
        return NotificationController()
    
    @pytest.mark.xfail(reason="Advanced WebSocket features not implemented yet")
    @pytest.mark.asyncio
    async def test_broadcast_notification_to_multiple_users(self, notification_controller):
        """Test that notifications are broadcast to all connected clients"""
        # This test assumes the controller has been updated with broadcast capability
        # Skip implementation until controller is updated with this feature
        pytest.skip("NotificationController doesn't have broadcast capability yet")
        
        # The rest of the test will be skipped
        # Arrange
        connected_websockets = []
        for i in range(3):  # Create 3 mock clients
            mock_client = AsyncMock()
            connected_websockets.append(mock_client)
        
        # We need to patch the controller to maintain a list of connected clients
        with patch.object(notification_controller, '_active_connections', connected_websockets):
            # Act - broadcast a notification
            notification = {"id": 1, "message": "Broadcast test", "type": "announcement"}
            await notification_controller.broadcast(notification)
            
            # Assert - all clients received the same notification
            for client in connected_websockets:
                client.send_json.assert_called_once_with(notification)
    
    @pytest.mark.xfail(reason="Advanced WebSocket features not implemented yet")
    @pytest.mark.asyncio
    async def test_direct_message_between_users(self, notification_controller):
        """Test sending notification from one user directly to another"""
        # This test assumes the controller has been updated with direct messaging capability
        # Skip implementation until controller is updated with this feature
        pytest.skip("NotificationController doesn't have direct messaging capability yet")
        
        # The rest of the test will be skipped
        # Arrange - create sender and recipient websocket connections
        mock_sender = AsyncMock()
        mock_recipient = AsyncMock()
        
        # We need a way to identify connections by user_id
        user_connections = {
            "user_123": mock_sender,
            "user_456": mock_recipient
        }
        
        with patch.object(notification_controller, '_user_connections', user_connections):
            # Act - send direct message
            message = {
                "from_user_id": "user_123", 
                "to_user_id": "user_456",
                "content": "Hello there!"
            }
            
            # Simulate the controller receiving and routing the message
            await notification_controller.send_direct_message(message)
            
            # Assert - only intended recipient received the notification
            mock_recipient.send_json.assert_called_once()
            mock_sender.send_json.assert_not_called()  # Sender doesn't receive their own message
            
            # Verify the message content
            sent_data = mock_recipient.send_json.call_args[0][0]
            assert sent_data["from_user_id"] == "user_123"
            assert sent_data["content"] == "Hello there!"

# Additional tests we should add for database persistence:
class TestNotificationPersistence:
    """Tests for notification database operations - currently not implemented"""
    
    @pytest.mark.skip(reason="Database persistence not implemented yet")
    def test_notification_persistence_to_database(self):
        """Test that created notifications are saved to database"""
        # This would test that when create_notification is called,
        # the notification is properly saved to the database
        pass
        
    @pytest.mark.skip(reason="Database persistence not implemented yet")
    def test_retrieve_user_notifications_from_database(self):
        """Test retrieving all notifications for a specific user from database"""
        # This would test get_notifications actually queries the database
        # and filters by user_id
        pass
        
    @pytest.mark.skip(reason="Database persistence not implemented yet")
    def test_update_notification_status_in_database(self):
        """Test that marking as read updates the database record"""
        # This would verify the database is updated when mark_as_read is called
        pass
