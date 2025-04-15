/**
 * WebRTC Module
 * Handles WebRTC peer connections and ice candidates
 */

import { state } from './state.js';
import { getRTCConfig, offerOptions } from './config.js';
import { createVideoElement, createPlayButton, updateParticipantLayout } from './ui.js';
import { sendToServer } from './signaling.js';

/**
 * Global debugging function for WebRTC events
 * @param {string} event - The event name
 * @param {string} peer - The peer ID
 * @param {Object} details - Additional details
 */
export const logRTCEvent = (event, peer, details = {}) => {
    console.log(`[WebRTC] ${event} - Peer: ${peer}`, details);
};

/**
 * Creates a peer connection for a remote client
 * @param {string} remoteClientId - The ID of the remote client
 * @returns {RTCPeerConnection} The created peer connection
 */
export const createPeerConnection = (remoteClientId) => {
    // WebRTC configuration with ICE servers for NAT traversal
    console.log("Creating new RTCPeerConnection with ICE/TURN configuration");
    console.warn("🔄 Configuring connection with adaptive traversal strategy");
    
    const config = getRTCConfig();
    const pc = new RTCPeerConnection(config);
    console.log(pc);

    // Add local tracks to peer connection
    state.localStream.getTracks().forEach(track => {
        pc.addTrack(track, state.localStream);
    });
    
    // Create video element for remote stream
    const videoContainer = createVideoElement(remoteClientId);
    const videoElement = document.getElementById(`video-${remoteClientId}`);

    // Handle remote tracks
    pc.ontrack = (event) => handleRemoteTrack(event, remoteClientId, videoElement, videoContainer);
    
    // Handle ICE candidates
    pc.onicecandidate = (event) => handleICECandidate(event, remoteClientId, pc);
    
    // Monitor ICE gathering state
    pc.onicegatheringstatechange = () => handleICEGatheringStateChange(pc, remoteClientId, videoElement);
    
    // Monitor connection state
    pc.onconnectionstatechange = () => handleConnectionStateChange(pc, remoteClientId);
    
    // Add specific ICE connection state monitoring
    pc.oniceconnectionstatechange = () => handleICEConnectionStateChange(pc, remoteClientId);

    return pc;
};

/**
 * Handles remote media tracks
 * @param {RTCTrackEvent} event - The track event
 * @param {string} remoteClientId - The ID of the remote client
 * @param {HTMLVideoElement} videoElement - The video element
 * @param {HTMLElement} videoContainer - The video container element
 */
const handleRemoteTrack = (event, remoteClientId, videoElement, videoContainer) => {
    console.log("Received remote track from:", remoteClientId, event.track.kind);
    
    // Wait for both audio and video tracks before setting srcObject
    // This helps avoid the "play() request was interrupted" errors
    if (!videoElement.srcObject) {
        videoElement.srcObject = event.streams[0];
    }
    
    // Ensure audio is enabled
    videoElement.volume = 1.0;
    videoElement.muted = false;
    
    // Log audio tracks to help with debugging
    const audioTracks = event.streams[0].getAudioTracks();
    console.log(`Remote stream has ${audioTracks.length} audio tracks`);
    if (audioTracks.length > 0) {
        console.log(`Audio track enabled: ${audioTracks[0].enabled}`);
    }
    
    // Add event listener for loadedmetadata before trying to play
    videoElement.onloadedmetadata = () => {
        console.log("Video metadata loaded, attempting to play");
        // Add user interaction requirement notice if needed
        const playPromise = videoElement.play();
        if (playPromise !== undefined) {
            playPromise.catch(e => {
                console.warn("Autoplay prevented:", e);
                // Create play button for browsers that block autoplay
                if (!document.getElementById(`play-button-${remoteClientId}`)) {
                    createPlayButton(remoteClientId, videoContainer, videoElement);
                }
            });
        }
    };
};

/**
 * Handles ICE candidates
 * @param {RTCPeerConnectionIceEvent} event - The ICE candidate event
 * @param {string} remoteClientId - The ID of the remote client
 * @param {RTCPeerConnection} pc - The peer connection
 */
const handleICECandidate = async (event, remoteClientId, pc) => {
    if (event.candidate) {
        const cand = event.candidate;
        // Log detailed ICE candidate information for debugging - using console.warn for visibility
        console.warn(`🔍 ICE CANDIDATE [${remoteClientId}]:`, {
            type: cand.type,
            protocol: cand.protocol,
            address: cand.address,
            port: cand.port,
            candidate: cand.candidate,
            relatedAddress: cand.relatedAddress,
            relatedPort: cand.relatedPort,
            foundation: cand.foundation,
            priority: cand.priority,
            component: cand.component
        });
        
        // Critical: Only send relay candidates when crossing networks
        if (cand.type === 'relay') {
            console.warn(`✅ SENDING RELAY CANDIDATE for ${remoteClientId} - This should work across networks`);
        } else {
            console.warn(`⚠️ SENDING ${cand.type.toUpperCase()} CANDIDATE for ${remoteClientId} - May not work across networks`);
        }
        
        // Force small delay to ensure proper candidate handling
        await new Promise(resolve => setTimeout(resolve, 100));
        
        await waitForWebSocket();
        sendToServer({
            type: "CANDIDATE",
            candidate: event.candidate,
            target: remoteClientId
        });
    } else {
        // ICE candidate gathering complete
        console.warn(`🏁 ICE gathering COMPLETE for ${remoteClientId}`);
    }
};

/**
 * Ensures WebSocket is open before sending
 */
const waitForWebSocket = async () => {
    if (state.socket.readyState !== WebSocket.OPEN) {
        console.warn("WebSocket is not open. Waiting...");
        await new Promise((resolve) => {
            const interval = setInterval(() => {
                if (state.socket.readyState === WebSocket.OPEN) {
                    clearInterval(interval);
                    resolve();
                }
            }, 100);
        });
    }
};

/**
 * Handles ICE gathering state changes
 * @param {RTCPeerConnection} pc - The peer connection
 * @param {string} remoteClientId - The ID of the remote client
 * @param {HTMLVideoElement} videoEl - The video element
 */
const handleICEGatheringStateChange = (pc, remoteClientId, videoEl) => {
    console.warn(`🧊 ICE GATHERING STATE for ${remoteClientId}: ${pc.iceGatheringState}`);
    
    // When complete, log all candidates collected
    if (pc.iceGatheringState === 'complete') {
        console.warn(`⚠️ ICE GATHERING COMPLETE FOR ${remoteClientId} - DUMPING ALL INFO`);
        
        // Force display of all connection info to help debugging
        setTimeout(() => {
            console.warn(`📊 CONNECTION STATUS CHECK FOR ${remoteClientId}`);
            console.warn(`- ICE Connection State: ${pc.iceConnectionState}`);
            console.warn(`- Connection State: ${pc.connectionState}`);
            console.warn(`- Signaling State: ${pc.signalingState}`);
            
            // Check if we have any active tracks
            const receivers = pc.getReceivers();
            console.warn(`- Active receivers: ${receivers.length}`);
            receivers.forEach((receiver, i) => {
                const track = receiver.track;
                if (track) {
                    console.warn(`  Receiver ${i}: ${track.kind} track (${track.readyState})`);
                }
            });
            
            // Force connection establishment if still in 'new' state
            if (pc.connectionState === 'new' && pc.iceConnectionState === 'new') {
                console.warn(`🔄 CONNECTION STILL NEW - FORCING CONNECTION ESTABLISHMENT FOR ${remoteClientId}`);
                
                // Force media display attempt
                if (videoEl && videoEl.srcObject) {
                    // Force media connection with a play attempt
                    videoEl.play().catch(e => {
                        console.warn("Play attempt failed, showing play button:", e);
                        
                        // Create play button if it doesn't exist
                        if (!document.getElementById(`play-button-${remoteClientId}`)) {
                            const playButton = document.createElement('button');
                            playButton.innerText = '▶️ Click to Start Video';
                            playButton.id = `play-button-${remoteClientId}`;
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
                            playButton.onclick = () => {
                                videoEl.play();
                                playButton.style.display = 'none';
                                
                                // Force ICE connection restart
                                console.warn(`🔥 FORCING ICE RESTART FOR ${remoteClientId}`);
                                pc.restartIce();
                                
                                // Send ICE restart signal to peer
                                sendToServer({
                                    type: "ICE_RESTART",
                                    target: remoteClientId
                                });
                            };
                            videoEl.parentNode.appendChild(playButton);
                        }
                    });
                }
                
                // Force ICE connection restart
                pc.restartIce();
                
                // Send restart signal to the other peer
                sendToServer({
                    type: "ICE_RESTART",
                    target: remoteClientId
                });
            }
        }, 2000);
    }
};

/**
 * Handles connection state changes
 * @param {RTCPeerConnection} pc - The peer connection
 * @param {string} remoteClientId - The ID of the remote client
 */
const handleConnectionStateChange = (pc, remoteClientId) => {
    console.warn(`🔌 CONNECTION STATE with ${remoteClientId}: ${pc.connectionState}`);
    
    if (pc.connectionState === 'connected') {
        console.warn(`✅✅✅ SUCCESS! Connection with ${remoteClientId} is ESTABLISHED`);
        // Show successful connection alert to help user understand status
        const videoElement = document.getElementById(`video-${remoteClientId}`);
        if (videoElement) {
            const alertDiv = document.createElement('div');
            alertDiv.textContent = 'Connected';
            alertDiv.className = 'connection-alert success';
            alertDiv.style.position = 'absolute';
            alertDiv.style.top = '5px';
            alertDiv.style.right = '5px';
            alertDiv.style.backgroundColor = 'rgba(0, 255, 0, 0.7)';
            alertDiv.style.color = 'white';
            alertDiv.style.padding = '2px 8px';
            alertDiv.style.borderRadius = '5px';
            alertDiv.style.fontSize = '12px';
            alertDiv.style.zIndex = '10';
            videoElement.parentNode.appendChild(alertDiv);
            setTimeout(() => alertDiv.remove(), 5000);
        }
    } else if (pc.connectionState === 'disconnected') {
        console.warn(`⚠️ Connection with ${remoteClientId} is unstable, waiting to see if it recovers...`);
        
        // Create a recovery function that will try multiple times
        const attemptRecovery = (attempts = 0, maxAttempts = 3) => {
            if (attempts >= maxAttempts) {
                console.log(`Failed to recover connection with ${remoteClientId} after ${maxAttempts} attempts`);
                // Don't remove the stream yet, give the ICE connection state handler a chance to try
                return;
            }
            
            // Check current state
            if (pc.connectionState === 'connected') {
                console.log(`Connection with ${remoteClientId} recovered successfully`);
                return;
            }
            
            console.log(`Recovery attempt ${attempts + 1} for connection with ${remoteClientId}`);
            
            // Try ICE restart
            sendToServer({
                type: "ICE_RESTART",
                target: remoteClientId
            });
            
            // Schedule another attempt after increasing delay (exponential backoff)
            setTimeout(() => attemptRecovery(attempts + 1, maxAttempts), 3000 * (attempts + 1));
        };
        
        // Start recovery attempts after a short delay
        setTimeout(() => attemptRecovery(), 2000);
    } else if (pc.connectionState === 'failed') {
        // If completely failed after possible restart attempts, try one last aggressive restart
        console.log(`Connection with ${remoteClientId} has failed, attempting aggressive recovery...`);
        
        try {
            // Try creating a new peer connection as a last resort
            const newPC = createPeerConnection(remoteClientId);
            state.peerConnections[remoteClientId] = newPC;
            
            // Create a new offer with ice restart
            setTimeout(async () => {
                try {
                    const offer = await newPC.createOffer(offerOptions);
                    await newPC.setLocalDescription(offer);
                    
                    // Send the offer
                    sendToServer({
                        type: "OFFER",
                        offer: offer,
                        target: remoteClientId,
                        isReconnect: true
                    });
                    console.log(`Last resort reconnect offer sent to ${remoteClientId}`);
                } catch (err) {
                    console.error("Error in last resort recovery:", err);
                    removeRemoteStream(remoteClientId);
                }
            }, 500);
        } catch (err) {
            console.error("Failed aggressive recovery attempt:", err);
            removeRemoteStream(remoteClientId);
        }
    }
};

/**
 * Handles ICE connection state changes
 * @param {RTCPeerConnection} pc - The peer connection
 * @param {string} remoteClientId - The ID of the remote client
 */
const handleICEConnectionStateChange = (pc, remoteClientId) => {
    console.log(`ICE connection state with ${remoteClientId}: ${pc.iceConnectionState}`);
    
    // Handle specific ICE connection states
    if (pc.iceConnectionState === 'disconnected') {
        console.log(`ICE connection with ${remoteClientId} is disconnected, waiting...`);
    } else if (pc.iceConnectionState === 'failed') {
        console.log(`ICE connection with ${remoteClientId} failed, will attempt restart`);
        sendToServer({
            type: "ICE_RESTART",
            target: remoteClientId
        });
    }
};

/**
 * Removes a remote stream and cleans up resources
 * @param {string} clientId - The ID of the client to remove
 */
export const removeRemoteStream = (clientId) => {
    if (state.peerConnections[clientId]) {
        state.peerConnections[clientId].close();
        delete state.peerConnections[clientId];
    }
    
    const container = document.getElementById(`container-${clientId}`);
    if (container) {
        container.remove();
    }
    
    // Update layout based on number of participants
    updateParticipantLayout();
};
