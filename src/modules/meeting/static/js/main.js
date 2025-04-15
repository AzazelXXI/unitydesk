/**
 * Main Module
 * Orchestrates the video conferencing application
 */

import { state } from './modules/state.js';
import { setupUI, updateParticipantLayout } from './modules/ui.js';
import { connect } from './modules/signaling.js';
import { initializeMedia, toggleAudio, toggleVideo } from './modules/media.js';
import { toggleChat, sendChatMessage, initChatListeners } from './modules/chat.js';
import { removeRemoteStream } from './modules/webrtc.js';

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
