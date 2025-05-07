/**
 * Call Controls Module
 * Cung cấp các chức năng điều khiển cuộc gọi như thoát, tạm dừng, v.v.
 */

import { state } from './state.js';
import { sendToServer } from './signaling.js';
import { logger } from './logger.js';
import { removeRemoteStream } from './webrtc.js';

/**
 * Rời khỏi cuộc gọi hiện tại
 * @param {boolean} redirectToHome - Có chuyển hướng về trang chủ sau khi thoát không
 */
export const leaveCall = async (redirectToHome = true) => {
    logger.info("Đang thoát khỏi cuộc gọi...");
    
    try {
        // Gửi thông báo LEAVE đến máy chủ trước khi đóng kết nối
        if (state.socket && state.socket.readyState === WebSocket.OPEN) {
            sendToServer({
                type: "LEAVE",
                clientId: state.clientId,
                message: "User left the meeting"
            });
            
            // Đợi một chút để tin nhắn được gửi đi
            await new Promise(resolve => setTimeout(resolve, 200));
            
            // Đóng kết nối WebSocket
            state.socket.close();
            logger.info("Kết nối WebSocket đã đóng");
        }
        
        // Dọn dẹp các peer connections
        Object.keys(state.peerConnections).forEach(clientId => {
            if (state.peerConnections[clientId]) {
                state.peerConnections[clientId].close();
                removeRemoteStream(clientId);
            }
        });
        
        // Dọn dẹp luồng media local
        if (state.localStream) {
            state.localStream.getTracks().forEach(track => {
                track.stop();
            });
            logger.info("Đã dừng tất cả các track media local");
        }
        
        // Hiển thị thông báo thoát
        showLeaveNotification();
        
        // Chuyển hướng về trang chủ sau 1 giây
        if (redirectToHome) {
            setTimeout(() => {
                window.location.href = '/';  // Chuyển về trang chủ
            }, 1000);
        }
    } catch (error) {
        logger.error("Lỗi khi thoát khỏi cuộc gọi:", error);
    }
};

/**
 * Hiển thị thông báo khi thoát cuộc gọi
 */
const showLeaveNotification = () => {
    const notification = document.createElement('div');
    notification.className = 'leave-notification';
    notification.textContent = 'Bạn đã rời khỏi cuộc gọi!';
    
    // Thêm style cho thông báo
    notification.style.position = 'fixed';
    notification.style.top = '50%';
    notification.style.left = '50%';
    notification.style.transform = 'translate(-50%, -50%)';
    notification.style.backgroundColor = 'rgba(0, 0, 0, 0.8)';
    notification.style.color = 'white';
    notification.style.padding = '20px 30px';
    notification.style.borderRadius = '8px';
    notification.style.fontSize = '18px';
    notification.style.zIndex = '9999';
    
    document.body.appendChild(notification);
};

/**
 * Phương thức xử lý người dùng khác thoát khỏi cuộc gọi
 * @param {string} clientId - ID của client đã thoát
 */
export const handleRemoteLeave = (clientId) => {
    // Hiển thị thông báo người dùng đã rời đi
    const notification = document.createElement('div');
    notification.className = 'remote-leave-notification';
    notification.textContent = `Người dùng khác đã rời khỏi cuộc gọi`;
    notification.style.position = 'fixed';
    notification.style.bottom = '20px';
    notification.style.right = '20px';
    notification.style.backgroundColor = 'rgba(0, 0, 0, 0.7)';
    notification.style.color = 'white';
    notification.style.padding = '10px 20px';
    notification.style.borderRadius = '4px';
    notification.style.zIndex = '9998';
    
    document.body.appendChild(notification);
    
    // Xóa thông báo sau 3 giây
    setTimeout(() => {
        if (document.body.contains(notification)) {
            document.body.removeChild(notification);
        }
    }, 3000);
    
    // Ghi log thông tin
    logger.info(`Người dùng ${clientId} đã rời khỏi cuộc gọi`);
    notification.style.padding = '10px 20px';
    notification.style.borderRadius = '4px';
    notification.style.zIndex = '9998';
    
    document.body.appendChild(notification);
    
    // Xóa thông báo sau 3 giây
    setTimeout(() => {
        if (document.body.contains(notification)) {
            document.body.removeChild(notification);
        }
    }, 3000);
};
