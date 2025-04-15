/**
 * UI Module
 * Handles UI-related functionality including video layout and participant display
 */

import { state } from './state.js';

/**
 * Creates and adds UI controls to the page
 */
export const setupUI = () => {
    createControlsContainer();
    createChatInterface();
    setupEventListeners();
};

/**
 * Creates the controls container with buttons
 */
const createControlsContainer = () => {
    // Create controls container
    const controlsContainer = document.createElement('div');
    controlsContainer.id = 'controls-container';
    document.body.appendChild(controlsContainer);
    
    // Add audio toggle button
    const audioToggleBtn = document.createElement('button');
    audioToggleBtn.innerHTML = '<i class="mic-icon"></i>';
    audioToggleBtn.title = 'Mute';
    audioToggleBtn.className = 'control-button audio-btn';
    controlsContainer.appendChild(audioToggleBtn);
    
    // Add video toggle button
    const videoToggleBtn = document.createElement('button');
    videoToggleBtn.innerHTML = '<i class="camera-icon"></i>';
    videoToggleBtn.title = 'Turn Off Camera';
    videoToggleBtn.className = 'control-button video-btn';
    controlsContainer.appendChild(videoToggleBtn);
    
    // Add chat button
    const chatToggleBtn = document.createElement('button');
    chatToggleBtn.innerHTML = '<i class="chat-icon"></i>';
    chatToggleBtn.title = 'Chat';
    chatToggleBtn.className = 'control-button chat-btn';
    controlsContainer.appendChild(chatToggleBtn);
};

/**
 * Creates the chat interface
 */
const createChatInterface = () => {
    // Create chat container (initially hidden)
    const chatContainer = document.createElement('div');
    chatContainer.id = 'chat-container';
    chatContainer.className = 'chat-hidden';
    
    const chatHeader = document.createElement('div');
    chatHeader.id = 'chat-header';
    chatHeader.innerHTML = '<h3>Chat</h3><button class="close-chat">×</button>';
    chatContainer.appendChild(chatHeader);
    
    const chatMessages = document.createElement('div');
    chatMessages.id = 'chat-messages';
    chatContainer.appendChild(chatMessages);
    
    const chatInputArea = document.createElement('div');
    chatInputArea.id = 'chat-input-area';
    
    const chatInput = document.createElement('input');
    chatInput.type = 'text';
    chatInput.id = 'chat-input';
    chatInput.placeholder = 'Type a message...';
    chatInputArea.appendChild(chatInput);
    
    const sendBtn = document.createElement('button');
    sendBtn.id = 'send-btn';
    sendBtn.innerHTML = '<i class="send-icon"></i>';
    sendBtn.title = 'Send message';
    chatInputArea.appendChild(sendBtn);
    
    chatContainer.appendChild(chatInputArea);
    document.body.appendChild(chatContainer);
};

/**
 * Sets up event listeners for UI elements
 */
const setupEventListeners = () => {
    // These will be connected to the actual handlers in main.js
    // By separating them here, we keep UI concerns separate from business logic
};

/**
 * Creates a video element for a remote peer
 * @param {string} remoteClientId - The ID of the remote client
 * @returns {HTMLElement} The created video container
 */
export const createVideoElement = (remoteClientId) => {
    const videoContainer = document.createElement('div');
    videoContainer.className = 'video-container';
    videoContainer.id = `container-${remoteClientId}`;

    const videoElement = document.createElement('video');
    videoElement.className = 'video-player';
    videoElement.id = `video-${remoteClientId}`;
    videoElement.autoplay = true;
    videoElement.playsinline = true;
    videoElement.muted = false; // Make sure remote videos are NOT muted

    videoContainer.appendChild(videoElement);
    document.getElementById('videos').appendChild(videoContainer);
    
    return videoContainer;
};

/**
 * Creates a play button for videos that can't autoplay
 * @param {string} remoteClientId - The ID of the remote client
 * @param {HTMLElement} videoContainer - The container element for the video
 * @param {HTMLVideoElement} videoElement - The video element
 */
export const createPlayButton = (remoteClientId, videoContainer, videoElement) => {
    const playButton = document.createElement('button');
    playButton.innerText = 'Click to Unmute/Play';
    playButton.id = `play-button-${remoteClientId}`;
    playButton.className = 'play-button';
    playButton.onclick = () => {
        videoElement.play();
        playButton.style.display = 'none';
    };
    videoContainer.appendChild(playButton);
};

/**
 * Updates the video layout based on participant count
 */
export const updateParticipantLayout = () => {
    const videosContainer = document.getElementById('videos');
    const participantCount = Object.keys(state.peerConnections).length + 1; // +1 for local user
    
    if (participantCount <= 1) {
        // Single participant mode (just the local user)
        videosContainer.classList.add('single-participant');
    } else {
        // Multiple participants mode
        videosContainer.classList.remove('single-participant');
    }
    
    console.log(`Layout updated for ${participantCount} participants`);
};

/**
 * Removes a remote participant's video element
 * @param {string} clientId - The ID of the client to remove
 */
export const removeRemoteVideoElement = (clientId) => {
    const container = document.getElementById(`container-${clientId}`);
    if (container) {
        container.remove();
    }
    
    // Update layout based on number of participants
    updateParticipantLayout();
};
