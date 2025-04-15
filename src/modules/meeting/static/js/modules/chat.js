/**
 * Chat Module
 * Handles chat functionality
 */

import { sendToServer } from './signaling.js';

/**
 * Toggles the chat panel visibility
 */
export const toggleChat = () => {
    const chatContainer = document.getElementById('chat-container');
    chatContainer.classList.toggle('chat-hidden');
    chatContainer.classList.toggle('chat-visible');
    
    // Toggle body class to adjust main content
    document.body.classList.toggle('chat-open');
    
    // Focus on input if chat is visible
    if (chatContainer.classList.contains('chat-visible')) {
        document.getElementById('chat-input').focus();
    }
};

/**
 * Sends a chat message
 */
export const sendChatMessage = () => {
    const input = document.getElementById('chat-input');
    const message = input.value.trim();
    
    if (message) {
        // Add message to local chat
        addMessageToChat(message, true);
        
        // Send message to peers
        sendToServer({
            type: "CHAT_MESSAGE",
            message: message
        });
        
        // Clear input
        input.value = '';
    }
    
    // Keep focus on input
    input.focus();
};

/**
 * Adds a message to the chat container
 * @param {string|Object} message - The message to add
 * @param {boolean} isLocal - Whether the message is from the local user
 */
export const addMessageToChat = (message, isLocal = false) => {
    const chatMessages = document.getElementById('chat-messages');
    const messageElement = document.createElement('div');
    messageElement.className = isLocal ? 'chat-message local' : 'chat-message remote';
    
    // Add sender info if remote message
    if (!isLocal && message.sender) {
        const senderSpan = document.createElement('span');
        senderSpan.className = 'message-sender';
        senderSpan.innerText = message.sender;
        messageElement.appendChild(senderSpan);
        messageElement.innerHTML += ': ' + message.text;
    } else {
        messageElement.innerText = isLocal ? message : message.text || message;
    }
    
    chatMessages.appendChild(messageElement);
    
    // Scroll to bottom
    chatMessages.scrollTop = chatMessages.scrollHeight;
    
    // Flash chat button if chat is hidden
    if (document.getElementById('chat-container').classList.contains('chat-hidden')) {
        document.querySelector('.chat-btn').classList.add('chat-notification');
        setTimeout(() => {
            document.querySelector('.chat-btn').classList.remove('chat-notification');
        }, 2000);
    }
};

/**
 * Initializes chat message handling
 */
export const initChatListeners = () => {
    // Add event listeners for chat UI controls
    document.querySelector('.close-chat').onclick = toggleChat;
    document.getElementById('send-btn').onclick = sendChatMessage;
    document.getElementById('chat-input').addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            sendChatMessage();
        }
    });
    
    // Listen for chat message events from the signaling module
    window.addEventListener('chat-message', (event) => {
        addMessageToChat(event.detail, false);
    });
};
