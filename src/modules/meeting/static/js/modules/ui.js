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
    
    // Add screen share button
    const screenShareBtn = document.createElement('button');
    screenShareBtn.innerHTML = '<i class="fa-solid fa-desktop"></i>';
    screenShareBtn.title = 'Share Screen';
    screenShareBtn.className = 'control-button screen-share-btn';
    controlsContainer.appendChild(screenShareBtn);
    
    // Add chat button
    const chatToggleBtn = document.createElement('button');
    chatToggleBtn.innerHTML = '<i class="chat-icon"></i>';
    chatToggleBtn.title = 'Chat';
    chatToggleBtn.className = 'control-button chat-btn';
    controlsContainer.appendChild(chatToggleBtn);// Add leave call button
    const leaveCallBtn = document.createElement('button');
    leaveCallBtn.innerHTML = '<i class="fa-solid fa-phone"></i>';
    leaveCallBtn.title = 'Disconnect';
    leaveCallBtn.className = 'control-button leave-call-btn';
    leaveCallBtn.style.backgroundColor = '#FF3B30';
    leaveCallBtn.style.display = 'flex';
    leaveCallBtn.style.alignItems = 'center';
    leaveCallBtn.style.justifyContent = 'center';
    leaveCallBtn.style.padding = '12px'; // Thêm padding phù hợp cho nút
    controlsContainer.appendChild(leaveCallBtn); // Add disconnect button
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

    // Add screen share button event listener
    const screenShareBtn = document.querySelector('.screen-share-btn');
    if (screenShareBtn) {
        screenShareBtn.addEventListener('click', () => {
            // We'll import this function in main.js and connect it
            const event = new CustomEvent('toggleScreenShare');
            document.dispatchEvent(event);
        });
    }
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
 * Display a notification message to the user
 * @param {string} message - The message to display
 * @param {string} type - The type of notification (success, warning, error)
 */
export const showNotification = (message, type = 'info') => {
    // Create notification element if it doesn't exist
    let notification = document.getElementById('notification');
    if (!notification) {
        notification = document.createElement('div');
        notification.id = 'notification';
        notification.style.position = 'fixed';
        notification.style.bottom = '20px';
        notification.style.left = '50%';
        notification.style.transform = 'translateX(-50%)';
        notification.style.padding = '10px 20px';
        notification.style.borderRadius = '5px';
        notification.style.color = 'white';
        notification.style.fontWeight = 'bold';
        notification.style.zIndex = '9999';
        notification.style.opacity = '0';
        notification.style.transition = 'opacity 0.3s';
        document.body.appendChild(notification);
    }
    
    // Set style based on type
    if (type === 'success') {
        notification.style.backgroundColor = 'rgba(0, 128, 0, 0.9)';
    } else if (type === 'warning') {
        notification.style.backgroundColor = 'rgba(255, 165, 0, 0.9)';
    } else if (type === 'error') {
        notification.style.backgroundColor = 'rgba(255, 0, 0, 0.9)';
    } else {
        notification.style.backgroundColor = 'rgba(0, 0, 255, 0.9)';
    }
    
    // Set message and show
    notification.textContent = message;
    notification.style.opacity = '1';
    
    // Hide after delay
    setTimeout(() => {
        notification.style.opacity = '0';
    }, 3000);
};

/**
 * Creates a play button for a video that requires user interaction to play
 * @param {string} clientId - The client ID
 * @param {HTMLElement} container - The container for the video
 * @param {HTMLVideoElement} videoElement - The video element
 */
export const createPlayButton = (clientId, container, videoElement) => {
    const playButton = document.createElement('button');
    playButton.innerText = '▶️ Click to Play Video';
    playButton.id = `play-button-${clientId}`;
    playButton.className = 'play-button';
    playButton.style.position = 'absolute';
    playButton.style.top = '50%';
    playButton.style.left = '50%';
    playButton.style.transform = 'translate(-50%, -50%)';
    playButton.style.padding = '10px 20px';
    playButton.style.backgroundColor = 'rgba(0,0,0,0.7)';
    playButton.style.color = 'white';
    playButton.style.border = 'none';
    playButton.style.borderRadius = '5px';
    playButton.style.cursor = 'pointer';
    playButton.style.zIndex = '100';
    
    // Add click handler to play the video
    playButton.onclick = () => {
        videoElement.play().then(() => {
            playButton.style.display = 'none';
            showNotification('Video playback started', 'success');
        }).catch(error => {
            console.error('Error playing video:', error);
            showNotification('Failed to play video. Please try again.', 'error');
        });
    };
    
    container.appendChild(playButton);
    return playButton;
};

/**
 * Creates a button to unmute audio for a video element
 * @param {string} clientId - The client ID
 * @param {HTMLElement} container - The video container
 * @param {HTMLVideoElement} videoElement - The video element
 */
export const createUnmuteButton = (clientId, container, videoElement) => {
    // Don't create if it already exists
    if (document.getElementById(`unmute-button-${clientId}`)) {
        return;
    }
    
    const unmuteButton = document.createElement('button');
    unmuteButton.id = `unmute-button-${clientId}`;
    unmuteButton.className = 'unmute-button';
    unmuteButton.innerHTML = '🔊 Click to Unmute';
    unmuteButton.style.position = 'absolute';
    unmuteButton.style.bottom = '10px';
    unmuteButton.style.left = '50%';
    unmuteButton.style.transform = 'translateX(-50%)';
    unmuteButton.style.backgroundColor = 'rgba(0, 0, 0, 0.7)';
    unmuteButton.style.color = 'white';
    unmuteButton.style.border = 'none';
    unmuteButton.style.borderRadius = '5px';
    unmuteButton.style.padding = '8px 16px';
    unmuteButton.style.cursor = 'pointer';
    unmuteButton.style.zIndex = '100';
    
    unmuteButton.onclick = () => {
        try {
            // Unmute the video
            videoElement.muted = false;
            unmuteButton.style.display = 'none';
            showNotification('Audio unmuted', 'success');
        } catch (err) {
            console.error('Failed to unmute audio:', err);
            showNotification('Failed to unmute audio', 'error');
        }
    };
    
    container.appendChild(unmuteButton);
    return unmuteButton;
};

/**
 * Updates the video layout based on participant count
 */
export const updateParticipantLayout = () => {
    const videosContainer = document.getElementById('videos');
    const participantCount = Object.keys(state.peerConnections).length + 1; // +1 for local user
    
    // Xóa tất cả các class liên quan đến số người tham gia trước đó
    videosContainer.classList.remove('single-participant', 'participants-1', 'participants-2', 
        'participants-3-4', 'participants-5-9', 'participants-10-16', 
        'participants-17-25', 'participants-26-30', 'compact-mode');
    
    if (participantCount <= 1) {
        // Single participant mode (just the local user)
        // Thêm cả hai class để đảm bảo CSS được áp dụng đúng
        videosContainer.classList.add('single-participant');
        videosContainer.classList.add('participants-1');
    } else if (participantCount === 2) {
        videosContainer.classList.add('participants-2');
    } else if (participantCount <= 4) {
        videosContainer.classList.add('participants-3-4');
    } else if (participantCount <= 9) {
        videosContainer.classList.add('participants-5-9');
    } else if (participantCount <= 16) {
        videosContainer.classList.add('participants-10-16');
    } else if (participantCount <= 25) {
        videosContainer.classList.add('participants-17-25');
    } else if (participantCount <= 30) {
        videosContainer.classList.add('participants-26-30');
    } else {
        // Trên 30 người thì chuyển sang chế độ compact
        videosContainer.classList.add('compact-mode');
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
