/**
 * WebRTC Module
 * Handles WebRTC peer connections and ice candidates
 */

import { state } from './state.js';
import { getRTCConfig, offerOptions } from './config.js';
import { createVideoElement, createPlayButton, createUnmuteButton, updateParticipantLayout, showNotification } from './ui.js';
import { sendToServer } from './signaling.js';
import { logger } from './logger.js';
import { diagnoseMediaStream, fixMediaPlayback, showMediaStatus } from './media-fix.js';

/**
 * Global debugging function for WebRTC events
 * @param {string} event - The event name
 * @param {string} peer - The peer ID
 * @param {Object} details - Additional details
 */
export const logRTCEvent = (event, peer, details = {}) => {
    logger.debug(`[WebRTC] ${event} - Peer: ${peer}`, details);
};

/**
 * Creates a peer connection for a remote client
 * @param {string} remoteClientId - The ID of the remote client
 * @returns {RTCPeerConnection} The created peer connection
 */
export const createPeerConnection = (remoteClientId) => {
    // WebRTC configuration with ICE servers for NAT traversal
    logger.info(`Creating new peer connection for client: ${remoteClientId}`);
    logger.debug("🔄 Configuring connection with adaptive traversal strategy");
    
    const config = getRTCConfig();
    const pc = new RTCPeerConnection(config);
    logger.trace("RTCPeerConnection created:", pc);

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
    logger.info(`Received ${event.track.kind} track from peer: ${remoteClientId}`);
    
    // Add CSS class to videoElement for proper styling
    videoElement.classList.add('remote-video');
      // Set up track ended handler with enhanced logging
    event.track.onended = () => {
        logger.warn(`Remote ${event.track.kind} track ended from ${remoteClientId}`);
        showConnectionStatus(remoteClientId, 'Media stream interrupted', 'rgba(255, 165, 0, 0.7)');
        videoElement.classList.remove('has-remote-media');
        
        // Attempt to recover the track if possible
        setTimeout(() => {
            if (state.peerConnections[remoteClientId] && 
                state.peerConnections[remoteClientId].connectionState === 'connected') {
                logger.info(`Attempting to recover ${event.track.kind} track for ${remoteClientId}`);
                
                // Signal the remote peer to restart their track
                sendToServer({
                    type: "TRACK_RECOVERY_REQUEST",
                    trackType: event.track.kind,
                    target: remoteClientId
                });
            }
        }, 1000);
    };
    
    // Set up track mute handler with visual indication and auto-recovery
    event.track.onmute = () => {
        logger.debug(`Remote ${event.track.kind} track muted from ${remoteClientId}`);
        if (event.track.kind === 'audio') {
            showConnectionStatus(remoteClientId, 'Audio muted', 'rgba(255, 165, 0, 0.7)');
            // Create unmute button in case this is browser-imposed
            createUnmuteButton(remoteClientId, videoContainer, videoElement);
            
            // Try to force unmute the track
            try {
                event.track.enabled = true;
            } catch (err) {
                logger.debug(`Could not force enable audio track: ${err.message}`);
            }
        } else if (event.track.kind === 'video') {
            videoElement.classList.add('video-muted');
            
            // Try to force unmute the video track
            try {
                event.track.enabled = true;
                // Some browsers need a nudge to display video
                videoElement.style.opacity = '0.99';
                setTimeout(() => {
                    videoElement.style.opacity = '1';
                }, 100);
            } catch (err) {
                logger.debug(`Could not force enable video track: ${err.message}`);
            }
        }
        
        // Additional recovery for persistent mute issues
        setTimeout(async () => {
            if (event.track.muted) {
                logger.warn(`Track still muted after delay, applying additional fixes for ${remoteClientId}`);
                await fixMediaPlayback(videoElement, remoteClientId);
            }
        }, 2000);
    };
    
    // Set up track unmute handler with enhanced media flow verification
    event.track.onunmute = () => {
        logger.debug(`Remote ${event.track.kind} track unmuted from ${remoteClientId}`);
        if (event.track.kind === 'video') {
            videoElement.classList.remove('video-muted');
            
            // Make sure video is actually displayed
            videoElement.style.opacity = '0.99';
            setTimeout(() => {
                videoElement.style.opacity = '1';
            }, 100);
        }
        
        // Verify track is actually working
        if (event.track.kind === 'audio' && videoElement.muted) {
            logger.info(`Audio track available but video element is muted for ${remoteClientId}`);
            showConnectionStatus(remoteClientId, 'Audio available - click unmute', 'rgba(0, 255, 0, 0.7)');
            createUnmuteButton(remoteClientId, videoContainer, videoElement);
        }
    };    // CRITICAL FIX: Check if video element still exists in the DOM before updating
    if (!document.body.contains(videoElement)) {
        logger.warn(`Video element for ${remoteClientId} is no longer in the DOM, creating new element`);
        // Instead of failing, re-create the video element in the container if it exists
        if (document.body.contains(videoContainer)) {
            videoElement = document.createElement('video');
            videoElement.id = `remote-video-${remoteClientId}`;
            videoElement.className = 'remote-video';
            videoElement.autoplay = true;
            videoElement.playsInline = true;
            videoElement.muted = true; // Start muted for autoplay
            videoContainer.appendChild(videoElement);
            
            // Store the new video element reference
            state.remoteVideos[remoteClientId] = videoElement;
        } else {
            logger.error(`Cannot handle track: both video element and container for ${remoteClientId} are gone`);
            return; // Exit early, we can't do anything without the container
        }
    }
    
    // Always set the srcObject to ensure we have the latest tracks
    // Use try/catch to handle any errors when updating srcObject
    try {
        // If we already have a stream, add this track to it instead of replacing
        if (videoElement.srcObject && videoElement.srcObject !== event.streams[0]) {
            const existingStream = videoElement.srcObject;
            const newTrack = event.track;
            
            // Check if we need to replace an existing track of the same kind
            const existingTrackOfSameKind = existingStream.getTracks().find(t => t.kind === newTrack.kind);
            if (existingTrackOfSameKind) {
                logger.info(`Replacing existing ${newTrack.kind} track for ${remoteClientId}`);
                existingStream.removeTrack(existingTrackOfSameKind);
            }
            
            existingStream.addTrack(newTrack);
        } else {
            // Otherwise just set srcObject directly
            videoElement.srcObject = event.streams[0];
        }
    } catch (err) {
        logger.error(`Error setting srcObject: ${err.message}`);
        // Try a recovery approach
        setTimeout(() => {
            try {
                videoElement.srcObject = event.streams[0];
            } catch (err2) {
                logger.error(`Recovery attempt failed: ${err2.message}`);
            }
        }, 500);
    }
    
    // Add stream ended/track removal handler with better error handling
    event.streams[0].onremovetrack = () => {
        logger.warn(`Track removed from stream for ${remoteClientId}`);
        
        try {
            // Check if we still have valid tracks and the video element is still in the DOM
            if (videoElement && document.body.contains(videoElement) && videoElement.srcObject) {
                const diagnosis = diagnoseMediaStream(videoElement.srcObject, remoteClientId);
                if (diagnosis.hasIssues) {
                    logger.warn(`Media issues detected for ${remoteClientId}:`, diagnosis.issues);
                    showMediaStatus(remoteClientId, 'Media stream issues detected', 'warning');
                }
            }
        } catch (err) {
            logger.error(`Error handling track removal: ${err.message}`);
        }
    };
    
    // Mark media as connected for UI purposes
    showConnectionStatus(remoteClientId, 'Media connected', 'rgba(0, 255, 0, 0.7)');
      // Diagnose the incoming media stream
    const diagnosis = diagnoseMediaStream(event.streams[0], remoteClientId);
    if (diagnosis.hasIssues) {
        logger.warn(`Media issues detected for ${remoteClientId}:`, diagnosis.issues);
        showMediaStatus(remoteClientId, 'Media issues - click unmute button below', 'warning');
        
        // Attempt automatic fix for muted tracks
        setTimeout(async () => {
            try {
                // Try to enable all tracks that might be disabled
                event.streams[0].getTracks().forEach(track => {
                    if (!track.enabled) {
                        track.enabled = true;
                        logger.info(`Enabled ${track.kind} track for ${remoteClientId}`);
                    }
                });
                
                // Apply the fix media playback function
                await fixMediaPlayback(videoElement, remoteClientId);
            } catch (err) {
                logger.error(`Auto-fix attempt failed: ${err.message}`);
            }
        }, 1000);
    }
    
    // CRITICAL FIX: Set proper audio settings
    videoElement.volume = 1.0;
    
    // CRITICAL FIX: Many browsers mute by default to comply with autoplay policies
    // Initially mute to ensure autoplay works, then we'll offer unmute button
    videoElement.muted = true;
    
    // Log track details for debugging
    const audioTracks = event.streams[0].getAudioTracks();
    const videoTracks = event.streams[0].getVideoTracks();
    
    logger.info(`Remote stream status for ${remoteClientId}:
        - Audio tracks: ${audioTracks.length} 
        - Video tracks: ${videoTracks.length}
        - Stream active: ${event.streams[0].active}`);
    
    // Add visual indication that media is flowing
    if (audioTracks.length > 0 || videoTracks.length > 0) {
        videoElement.classList.add('has-remote-media');
    }
    
    // CRITICAL FIX: Add special CSS styles for video visibility
    videoElement.style.backgroundColor = 'rgba(0, 0, 0, 0.2)'; // Make it visible even when empty
      // Add event listener for loadedmetadata with enhanced playback strategy
    videoElement.onloadedmetadata = async () => {
        logger.info(`Video metadata loaded for ${remoteClientId}, attempting playback`);
        
        // Enhanced autoplay strategy with multiple fallback mechanisms
        const attemptPlayback = async (retryCount = 0) => {
            try {
                // First try playing with video muted (which most browsers allow automatically)
                videoElement.muted = true;
                await videoElement.play();
                logger.info(`Media playing for ${remoteClientId} (initially muted)`);
                
                // Add unmute button now that we know autoplay succeeded
                createUnmuteButton(remoteClientId, videoContainer, videoElement);
                
                // Verify media is actually flowing after a short delay
                setTimeout(async () => {
                    if (!videoElement.paused) {
                        logger.info(`Media is playing for ${remoteClientId}, attempting to unmute`);
                        showMediaStatus(remoteClientId, 'Click unmute button to hear audio', 'success');
                        
                        // Force track enablement
                        if (videoElement.srcObject) {
                            videoElement.srcObject.getTracks().forEach(track => {
                                if (!track.enabled) {
                                    track.enabled = true;
                                    logger.info(`Enabled ${track.kind} track for ${remoteClientId}`);
                                }
                            });
                        }
                    } else {
                        logger.warn(`Media still paused for ${remoteClientId}, attempting fix`);
                        await fixMediaPlayback(videoElement, remoteClientId);
                    }
                }, 1000);
                
            } catch (e) {
                logger.warn(`Autoplay failed for ${remoteClientId} (attempt ${retryCount + 1}):`, e);
                
                // Try a different approach if we haven't exhausted retries
                if (retryCount < 2) {
                    logger.info(`Trying alternative playback method (attempt ${retryCount + 1})`);
                    
                    // Add a slight delay before retry
                    setTimeout(() => attemptPlayback(retryCount + 1), 500);
                    
                    // Try with different autoplay settings
                    videoElement.muted = true;
                    videoElement.playsInline = true;
                    videoElement.autoplay = true;
                    
                    // Try to trigger playback using user interaction simulation
                    if (document.documentElement.requestFullscreen && retryCount === 1) {
                        try {
                            // Brief fullscreen toggle can help bypass autoplay restrictions
                            await videoElement.requestFullscreen();
                            setTimeout(() => document.exitFullscreen(), 100);
                        } catch (fullscreenErr) {
                            logger.debug(`Fullscreen attempt failed: ${fullscreenErr.message}`);
                        }
                    }
                } else {
                    // We've exhausted retries, fall back to manual interaction
                    logger.warn(`Autoplay failed after multiple attempts, requiring user interaction`);
                    
                    // Create both controls for user interaction
                    if (!document.getElementById(`play-button-${remoteClientId}`)) {
                        createPlayButton(remoteClientId, videoContainer, videoElement);
                    }
                    
                    createUnmuteButton(remoteClientId, videoContainer, videoElement);
                    
                    // Show status directing user to click
                    showConnectionStatus(remoteClientId, 'Click to start media', 'rgba(255, 165, 0, 0.7)', false);
                }
            }
        };
        
        // Start the playback attempt
        await attemptPlayback();
    };
    
    // Add handlers for media events
    videoElement.oncanplay = () => {
        logger.info(`Video can play for ${remoteClientId}`);
        videoElement.classList.add('can-play');
    };
    
    // Handle stalled media
    videoElement.onstalled = async () => {
        logger.warn(`Media playback stalled for ${remoteClientId}, attempting recovery`);
        await fixMediaPlayback(videoElement, remoteClientId);
    };
    
    // Add special event to handle when video actually starts displaying frames
    videoElement.addEventListener('playing', () => {
        logger.info(`Video now playing for ${remoteClientId}`);
        videoElement.classList.add('is-playing');
        showMediaStatus(remoteClientId, 'Video playing', 'success');
    });
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
        
        // Log ICE candidate information with proper logging
        logger.debug(`ICE CANDIDATE [${remoteClientId}]:`, {
            type: cand.type,
            protocol: cand.protocol,
            address: cand.address,
            port: cand.port,
            candidate: cand.candidate,
            relatedAddress: cand.relatedAddress,
            relatedPort: cand.relatedPort
        });
        
        // For cross-network operation, prioritize relay candidates
        // This ensures connections work across different networks
        if (cand.type === 'relay') {
            logger.info(`✅ RELAY CANDIDATE for ${remoteClientId} - sending (best for cross-network)`);
            
            // Send relay candidates immediately with high priority
            await waitForWebSocket();
            sendToServer({
                type: "CANDIDATE",
                candidate: event.candidate,
                target: remoteClientId,
                priority: "high"
            });
        } else {
            // For non-relay candidates, send them but with lower priority
            logger.debug(`Sending ${cand.type.toUpperCase()} candidate for ${remoteClientId}`);
            
            // Small delay for non-relay candidates to prioritize relay ones
            await new Promise(resolve => setTimeout(resolve, 100));
            
            await waitForWebSocket();
            sendToServer({
                type: "CANDIDATE",
                candidate: event.candidate,
                target: remoteClientId,
                priority: "normal"
            });
        }
    } else {
        // ICE candidate gathering complete
        logger.info(`ICE gathering complete for ${remoteClientId}`);
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
// Track reconnection attempts per peer
const reconnectionAttempts = new Map();
const MAX_RECONNECTION_ATTEMPTS = 5;
const BASE_RECONNECT_DELAY = 1000; // 1 second base delay

/**
 * Shows a connection status message to the user
 * @param {string} remoteClientId - The ID of the remote client
 * @param {string} status - The connection status
 * @param {string} color - The color for the status indicator
 * @param {boolean} isTemporary - Whether to automatically remove the status after some time
 */
const showConnectionStatus = (remoteClientId, status, color, isTemporary = true) => {
    const videoContainer = document.getElementById(`container-${remoteClientId}`);
    if (!videoContainer) return;
    
    // Remove any existing status indicator
    const existingStatus = videoContainer.querySelector('.connection-status');
    if (existingStatus) {
        existingStatus.remove();
    }
    
    // Create status indicator
    const statusDiv = document.createElement('div');
    statusDiv.className = 'connection-status';
    statusDiv.textContent = status;
    statusDiv.style.position = 'absolute';
    statusDiv.style.top = '5px';
    statusDiv.style.right = '5px';
    statusDiv.style.backgroundColor = color;
    statusDiv.style.color = 'white';
    statusDiv.style.padding = '3px 8px';
    statusDiv.style.borderRadius = '5px';
    statusDiv.style.fontSize = '12px';
    statusDiv.style.zIndex = '10';
    statusDiv.style.transition = 'opacity 0.3s';
    
    videoContainer.appendChild(statusDiv);
    
    // Automatically remove temporary statuses
    if (isTemporary) {
        setTimeout(() => {
            if (statusDiv.parentNode) {
                statusDiv.style.opacity = '0';
                setTimeout(() => {
                    if (statusDiv.parentNode) {
                        statusDiv.remove();
                    }
                }, 300);
            }
        }, 5000);
    }
    
    return statusDiv;
};

const handleConnectionStateChange = (pc, remoteClientId) => {
    logger.info(`Connection state with ${remoteClientId}: ${pc.connectionState}`);
    
    if (pc.connectionState === 'connected') {
        logger.info(`✅ Connection with ${remoteClientId} is ESTABLISHED`);
        
        // Reset reconnection attempts when successfully connected
        reconnectionAttempts.delete(remoteClientId);
        
        // Show successful connection status
        showConnectionStatus(remoteClientId, 'Connected', 'rgba(0, 255, 0, 0.7)');
        
    } else if (pc.connectionState === 'connecting') {
        showConnectionStatus(remoteClientId, 'Connecting...', 'rgba(255, 165, 0, 0.7)', false);
        
    } else if (pc.connectionState === 'disconnected') {
        logger.warn(`Connection with ${remoteClientId} is unstable, attempting recovery...`);
        
        // Show reconnecting status
        const statusDiv = showConnectionStatus(remoteClientId, 'Reconnecting...', 'rgba(255, 165, 0, 0.7)', false);
        
        // Initialize attempts counter if not exists
        if (!reconnectionAttempts.has(remoteClientId)) {
            reconnectionAttempts.set(remoteClientId, 0);
        }
        
        // Get current attempts count
        const attempts = reconnectionAttempts.get(remoteClientId);
        
        // Create recovery function with exponential backoff
        const attemptRecovery = () => {
            // Get updated attempts count
            const currentAttempts = reconnectionAttempts.get(remoteClientId);
            
            // Check if we've reached max attempts
            if (currentAttempts >= MAX_RECONNECTION_ATTEMPTS) {
                logger.warn(`Failed to recover connection with ${remoteClientId} after ${MAX_RECONNECTION_ATTEMPTS} attempts`);
                if (statusDiv) {
                    statusDiv.textContent = 'Connection failed';
                    statusDiv.style.backgroundColor = 'rgba(255, 0, 0, 0.7)';
                }
                return;
            }
            
            // Check if already reconnected
            if (pc.connectionState === 'connected') {
                logger.info(`Connection with ${remoteClientId} recovered successfully`);
                if (statusDiv) {
                    statusDiv.textContent = 'Connected';
                    statusDiv.style.backgroundColor = 'rgba(0, 255, 0, 0.7)';
                    setTimeout(() => {
                        if (statusDiv.parentNode) statusDiv.remove();
                    }, 3000);
                }
                return;
            }
            
            logger.info(`Recovery attempt ${currentAttempts + 1}/${MAX_RECONNECTION_ATTEMPTS} for ${remoteClientId}`);
            if (statusDiv) {
                statusDiv.textContent = `Reconnecting (${currentAttempts + 1}/${MAX_RECONNECTION_ATTEMPTS})`;
            }
            
            // Try ICE restart
            sendToServer({
                type: "ICE_RESTART",
                target: remoteClientId,
                attempt: currentAttempts + 1
            });
            
            // Increment attempts counter
            reconnectionAttempts.set(remoteClientId, currentAttempts + 1);
            
            // Calculate exponential backoff delay: base * 2^attempt (capped at 30 seconds)
            const delay = Math.min(BASE_RECONNECT_DELAY * Math.pow(2, currentAttempts), 30000);
            
            // Schedule next attempt with exponential backoff
            setTimeout(attemptRecovery, delay);
        };
        
        // Start recovery attempts after a short delay (if this is the first attempt)
        if (attempts === 0) {
            setTimeout(attemptRecovery, 1000);
        }
        
    } else if (pc.connectionState === 'failed') {
        logger.warn(`Connection with ${remoteClientId} has failed, attempting aggressive recovery...`);
        
        // Show failed status with option to retry
        const statusDiv = showConnectionStatus(remoteClientId, 'Connection failed', 'rgba(255, 0, 0, 0.7)', false);
        
        // Add retry button
        const retryButton = document.createElement('button');
        retryButton.textContent = 'Retry';
        retryButton.style.marginLeft = '5px';
        retryButton.style.padding = '2px 5px';
        retryButton.style.border = 'none';
        retryButton.style.borderRadius = '3px';
        retryButton.style.cursor = 'pointer';
        retryButton.onclick = () => performAggressiveRecovery();
        
        if (statusDiv) {
            statusDiv.appendChild(retryButton);
        }
          const performAggressiveRecovery = async () => {
            if (statusDiv) {
                statusDiv.textContent = 'Attempting reconnection...';
                statusDiv.style.backgroundColor = 'rgba(255, 165, 0, 0.7)';
            }
            
            try {
                // First, properly close the existing connection
                if (state.peerConnections[remoteClientId]) {
                    logger.info(`Properly closing existing connection with ${remoteClientId} before recovery`);
                    try {
                        // Only close - don't remove from state yet
                        state.peerConnections[remoteClientId].close();
                    } catch (err) {
                        logger.warn(`Error while closing old connection: ${err.message}`);
                    }
                }
                
                // Short delay to ensure proper cleanup
                await new Promise(resolve => setTimeout(resolve, 300));
                
                // Try creating a new peer connection as a last resort
                logger.info(`Creating new peer connection for aggressive recovery with ${remoteClientId}`);
                const newPC = createPeerConnection(remoteClientId);
                state.peerConnections[remoteClientId] = newPC;
                
                // Create a new offer with ice restart - use proper state checking
                setTimeout(async () => {
                    try {
                        // Check if we're in a valid state to create an offer
                        if (newPC.signalingState === 'stable') {
                            logger.info(`Creating aggressive recovery offer in signaling state: ${newPC.signalingState}`);
                            
                            const offer = await newPC.createOffer({
                                ...offerOptions,
                                iceRestart: true
                            });
                            
                            await newPC.setLocalDescription(offer);
                            
                            // Send the offer
                            sendToServer({
                                type: "OFFER",
                                offer: newPC.localDescription,
                                target: remoteClientId,
                                isReconnect: true,
                                isAggressiveRecovery: true
                            });
                            logger.info(`Aggressive reconnect offer sent to ${remoteClientId}`);
                        } else {
                            logger.warn(`Cannot create offer in current signaling state: ${newPC.signalingState}`);
                            if (statusDiv) {
                                statusDiv.textContent = `Recovery failed - invalid state: ${newPC.signalingState}`;
                                statusDiv.style.backgroundColor = 'rgba(255, 0, 0, 0.7)';
                            }
                        }
                    } catch (err) {
                        logger.error("Error in aggressive recovery:", err);
                        // Don't remove the stream immediately, give it a chance
                        if (statusDiv) {
                            statusDiv.textContent = 'Recovery failed - retrying in 5s';
                            
                            // Add a retry button
                            const retryButton = document.createElement('button');
                            retryButton.textContent = 'Retry Now';
                            retryButton.style.marginLeft = '5px';
                            retryButton.style.padding = '2px 5px';
                            retryButton.style.border = 'none';
                            retryButton.style.borderRadius = '3px';
                            retryButton.style.cursor = 'pointer';
                            retryButton.onclick = () => performAggressiveRecovery();
                            statusDiv.appendChild(retryButton);
                            
                            // Schedule another retry
                            setTimeout(() => performAggressiveRecovery(), 5000);
                        }
                    }
                }, 500);
            } catch (err) {
                logger.error("Failed aggressive recovery attempt:", err);
                // Don't remove immediately, show error and retry button
                if (statusDiv) {
                    statusDiv.textContent = 'Recovery failed';
                    statusDiv.style.backgroundColor = 'rgba(255, 0, 0, 0.7)';
                    
                    // Add retry button
                    const retryButton = document.createElement('button');
                    retryButton.textContent = 'Retry';
                    retryButton.style.marginLeft = '5px';
                    retryButton.style.padding = '2px 5px';
                    retryButton.style.border = 'none';
                    retryButton.style.borderRadius = '3px';
                    retryButton.style.cursor = 'pointer';
                    retryButton.onclick = () => performAggressiveRecovery();
                    statusDiv.appendChild(retryButton);
                }
            }
        };
        
        // Execute the recovery immediately
        performAggressiveRecovery();
    }
};

/**
 * Handles ICE connection state changes
 * @param {RTCPeerConnection} pc - The peer connection
 * @param {string} remoteClientId - The ID of the remote client
 */
const handleICEConnectionStateChange = (pc, remoteClientId) => {
    logger.info(`ICE connection state with ${remoteClientId}: ${pc.iceConnectionState}`);
    
    // Handle specific ICE connection states
    if (pc.iceConnectionState === 'checking') {
        // Connection is being established, update UI
        showConnectionStatus(remoteClientId, 'Establishing connection...', 'rgba(255, 165, 0, 0.7)', false);
        
    } else if (pc.iceConnectionState === 'connected') {
        // Connection successful
        logger.info(`ICE connection with ${remoteClientId} established successfully`);
        showConnectionStatus(remoteClientId, 'Connected', 'rgba(0, 255, 0, 0.7)');
        
    } else if (pc.iceConnectionState === 'completed') {
        // ICE has found the best candidates
        logger.info(`ICE connection with ${remoteClientId} completed (optimal route established)`);
        
    } else if (pc.iceConnectionState === 'disconnected') {
        logger.warn(`ICE connection with ${remoteClientId} is disconnected, waiting...`);
        showConnectionStatus(remoteClientId, 'Connection interrupted', 'rgba(255, 165, 0, 0.7)', false);
        
        // Force TURN relay usage on reconnection attempts
        try {
            // Modify the existing configuration to force relay-only
            const currentConfig = pc.getConfiguration();
            pc.setConfiguration({
                ...currentConfig,
                iceTransportPolicy: 'relay'
            });
            logger.info(`Forced relay-only mode for ${remoteClientId} reconnection`);
        } catch (err) {
            logger.warn(`Couldn't update ICE transport policy: ${err.message}`);
        }
        
    } else if (pc.iceConnectionState === 'failed') {
        logger.warn(`ICE connection with ${remoteClientId} failed, attempting restart`);
        showConnectionStatus(remoteClientId, 'Connection failed - restarting', 'rgba(255, 0, 0, 0.7)', false);
        
        // Try immediate ICE restart
        try {
            pc.restartIce();
            
            // Also signal to the other peer
            sendToServer({
                type: "ICE_RESTART",
                target: remoteClientId,
                forceRelay: true
            });
        } catch (err) {
            logger.error(`Error during ICE restart: ${err.message}`);
        }
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
