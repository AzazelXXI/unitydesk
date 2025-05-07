/**
 * Main Module
 * Orchestrates the video conferencing application
 */

import { state } from './modules/state.js';
import { setupUI, updateParticipantLayout } from './modules/ui.js';
import { connect } from './modules/signaling.js';
import { initializeMedia, toggleAudio, toggleVideo, toggleScreenShare } from './modules/media.js';
import { toggleChat, sendChatMessage, initChatListeners } from './modules/chat.js';
import { removeRemoteStream } from './modules/webrtc.js';
import { leaveCall } from './modules/call-controls.js';

/**
 * Initialize the application
 */
const init = async () => {
    try {
        // Setup UI elements
        setupUI();
        
        // Initialize media capture
        await initializeMedia();
        
        // Set up event listeners for UI controls
        setupEventListeners();
        
        // Initialize chat functionality
        initChatListeners();
        
        // Connect to signaling server
        await connect();
    } catch (error) {
        console.error("Error initializing application:", error);
    }
};

/**
 * Setup event listeners for UI interactions
 */
const setupEventListeners = () => {
    // Add media control button listeners
    document.querySelector('.audio-btn').addEventListener('click', toggleAudio);
    document.querySelector('.video-btn').addEventListener('click', toggleVideo);
    document.querySelector('.chat-btn').addEventListener('click', toggleChat);
    
    // Thêm event listener cho nút chia sẻ màn hình
    const screenShareBtn = document.querySelector('.screen-share-btn');
    if (screenShareBtn) {
        screenShareBtn.addEventListener('click', toggleScreenShare);
    }
    
    // Thêm event listener cho nút thoát cuộc gọi
    const leaveCallBtn = document.querySelector('.leave-call-btn');
    if (leaveCallBtn) {
        leaveCallBtn.addEventListener('click', () => {
            // Xác nhận trước khi thoát cuộc gọi
            if (confirm('Bạn có chắc chắn muốn rời khỏi cuộc gọi?')) {
                leaveCall(true); // true để chuyển hướng về trang chủ
            }
        });
    }
    
    // Handle page unload
    window.addEventListener('beforeunload', () => {
        if (state.socket) {
            state.socket.send(JSON.stringify({
                type: "LEAVE",
                clientId: state.clientId
            }));
        }
    });
};

// Initialize the application when the DOM is loaded
document.addEventListener('DOMContentLoaded', init);
