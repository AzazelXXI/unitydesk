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
import { forceTurnUsage, monitorIceCandidates, rotateToNextTurnServer, optimizeSdp } from './webrtc-connection-helper.js';

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
    
    // Handle ICE gathering state changes
    pc.onicegatheringstatechange = () => handleICEGatheringStateChange(pc, remoteClientId, videoElement);
    
    // Handle connection state changes
    pc.onconnectionstatechange = () => handleConnectionStateChange(pc, remoteClientId);
    
    // Handle ICE connection state changes
    pc.oniceconnectionstatechange = () => handleICEConnectionStateChange(pc, remoteClientId);
    
    // Setup monitoring for ICE candidates
    setTimeout(() => {
        monitorIceCandidates(pc, remoteClientId);
    }, 1000);
    
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
    // Kiểm tra khi bắt đầu nhận track
    event.track.onunmute = () => {
        if (event.track.kind === 'audio') {
            logger.debug(`Remote audio track unmuted from ${remoteClientId}`);
            // Kiểm tra xem video element có bị tắt tiếng không
            if (videoElement.muted) {
                logger.info(`Audio track available but video element is muted for ${remoteClientId}`);
                // Hiển thị nút bật âm thanh sau khi xác nhận có audio track
                setTimeout(() => {
                    createUnmuteButton(videoContainer, videoElement, remoteClientId);
                }, 1000);
            }
        } else if (event.track.kind === 'video') {
            logger.debug(`Remote video track unmuted from ${remoteClientId}`);
            videoElement.classList.add('has-video');
        }
    };
    
    // Xử lý khi track bị mute
    event.track.onmute = () => {
        if (event.track.kind === 'audio') {
            logger.debug(`Remote audio track muted from ${remoteClientId}`);
        } else if (event.track.kind === 'video') {
            logger.debug(`Remote video track muted from ${remoteClientId}`);
            
            // Thử khắc phục video bị mute
            setTimeout(async () => {
                logger.info(`Attempted to unmute video track for ${remoteClientId}`);
                try {
                    await fixMediaPlayback(videoElement, remoteClientId);
                } catch (e) {
                    logger.warn(`Track still muted after delay, applying additional fixes for ${remoteClientId}`);
                }
            }, 2000);
        }
    };
    
    // Xử lý khi track kết thúc
    event.track.onended = () => {
        if (event.track.kind === 'audio') {
            logger.warn(`Remote audio track ended from ${remoteClientId}`);
        } else if (event.track.kind === 'video') {
            logger.warn(`Remote video track ended from ${remoteClientId}`);
        }
    };
    
    // Nếu video element không còn trong DOM, không làm gì cả
    if (!document.body.contains(videoElement)) {
        return;
    }
    
    // Luôn cập nhật srcObject để đảm bảo có đủ các tracks mới nhất
    try {
        if (event.track.kind === 'audio') {
            logger.info(`Received audio track from peer: ${remoteClientId}`);
        } else if (event.track.kind === 'video') {
            logger.info(`Received video track from peer: ${remoteClientId}`);
        }
        
        // Đảm bảo không thay đổi srcObject nếu đã được thiết lập
        if (!videoElement.srcObject || videoElement.srcObject.id !== event.streams[0].id) {
            videoElement.srcObject = event.streams[0];
        }
    } catch (err) {
        logger.error(`Error setting srcObject: ${err.message}`);
    }
    
    // Thêm xử lý khi track bị xóa với xử lý lỗi tốt hơn
    event.streams[0].onremovetrack = () => {
        logger.debug(`Track removed from stream for ${remoteClientId}`);
        
        // Kiểm tra xem còn track nào không
        if (event.streams[0].getTracks().length === 0) {
            logger.warn(`No tracks left for ${remoteClientId}, possibly disconnected`);
        }
    };
    
    // Đánh dấu media đã kết nối cho giao diện người dùng
    showConnectionStatus(remoteClientId, 'Media connected', 'rgba(0, 255, 0, 0.7)');
    
    // Chẩn đoán stream media đầu vào
    const diagnosis = diagnoseMediaStream(event.streams[0], remoteClientId);
    if (diagnosis.hasIssues) {
        logger.warn(`Media issues detected for ${remoteClientId}:`, diagnosis.issues);
        showMediaStatus(remoteClientId, 'Media issues - click unmute button below', 'warning');
        
        // Thử khắc phục tự động cho các track bị mute
        setTimeout(async () => {
            try {
                await fixMediaPlayback(videoElement, remoteClientId);
                logger.info(`Applied automatic fix for ${remoteClientId}`);
            } catch (e) {
                logger.error(`Auto fix failed: ${e.message}`);
                // Tạo nút unmute thủ công nếu tự động thất bại
                createUnmuteButton(videoContainer, videoElement, remoteClientId);
            }
        }, 1000);
    }
    
    // CRITICAL FIX: Thiết lập âm lượng phù hợp
    videoElement.volume = 1.0;
    
    // CRITICAL FIX: Nhiều trình duyệt mặc định tắt tiếng để tuân thủ chính sách autoplay
    // Ban đầu tắt tiếng để đảm bảo autoplay hoạt động, sau đó hiện nút bật tiếng
    videoElement.muted = true;
    
    // Ghi nhật ký chi tiết track để gỡ lỗi
    const audioTracks = event.streams[0].getAudioTracks();
    const videoTracks = event.streams[0].getVideoTracks();
    
    logger.info(`Remote stream status for ${remoteClientId}:
        - Audio tracks: ${audioTracks.length} 
        - Video tracks: ${videoTracks.length}
        - Stream active: ${event.streams[0].active}`);
    
    // Thêm chỉ báo trực quan rằng media đang truyền tải
    if (audioTracks.length > 0 || videoTracks.length > 0) {
        videoElement.classList.add('has-remote-media');
    }
    
    // CRITICAL FIX: Thêm CSS style đặc biệt cho khả năng hiển thị video
    videoElement.style.backgroundColor = 'rgba(0, 0, 0, 0.2)'; // Hiển thị ngay cả khi rỗng
    
    // Thêm event listener cho loadedmetadata với chiến lược phát nâng cao
    videoElement.onloadedmetadata = async () => {
        logger.info(`Video metadata loaded for ${remoteClientId}, attempting playback`);
        
        // Chiến lược autoplay nâng cao với nhiều cơ chế dự phòng
        const attemptPlayback = async (retryCount = 0) => {
            try {
                await videoElement.play();
                logger.info(`Video now playing for ${remoteClientId}`);
                
                // Thêm lớp CSS để chỉ ra rằng video đang phát
                videoElement.classList.add('is-playing');
                
                // Hiện thông báo chỉ khi video đang phát thực sự
                if (!videoElement.paused) {
                    logger.info(`Media playing for ${remoteClientId} (initially muted)`);
                    showMediaStatus(remoteClientId, 'Video playing', 'success');
                    
                    // Tạo nút phát và nút bật tiếng sau khi video đang phát
                    createPlayButton(videoContainer, videoElement, remoteClientId);
                    createUnmuteButton(videoContainer, videoElement, remoteClientId);
                    
                    // Thử bật tiếng sau một chút thời gian nếu có audio track
                    setTimeout(() => {
                        if (audioTracks.length > 0) {
                            logger.info(`Media is playing for ${remoteClientId}, attempting to unmute`);
                            
                            // Kiểm tra chính sách autoplay
                            const autoplayAllowed = document.createElement('video').play() !== undefined;
                            if (autoplayAllowed) {
                                videoElement.muted = false;
                            }
                        }
                    }, 2000);
                }
            } catch (e) {
                // Xử lý lỗi phát phương tiện
                logger.warn(`Media playback error for ${remoteClientId}: ${e.message}, retry: ${retryCount}`);
                
                if (retryCount < 3) {  // Thử lại tối đa 3 lần
                    setTimeout(() => attemptPlayback(retryCount + 1), 1000);
                } else {
                    // Tạo nút phát thủ công nếu không phát được tự động
                    logger.warn(`Autoplay failed for ${remoteClientId}, showing manual play button`);
                    createPlayButton(videoContainer, videoElement, remoteClientId);
                }
            }
        };
        
        // Bắt đầu nỗ lực phát
        await attemptPlayback();
    };
    
    // Thêm xử lý cho các sự kiện media
    videoElement.oncanplay = () => {
        logger.info(`Video can play for ${remoteClientId}`);
        videoElement.classList.add('can-play');
    };
    
    // Xử lý media bị tạm dừng
    videoElement.onstalled = async () => {
        logger.warn(`Media playback stalled for ${remoteClientId}, attempting recovery`);
        await fixMediaPlayback(videoElement, remoteClientId);
    };
    
    // Thêm sự kiện đặc biệt để xử lý khi video bắt đầu hiển thị các khung hình
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
        
        // Log ICE candidate information
        logger.debug(`ICE CANDIDATE [${remoteClientId}]:`, {
            type: cand.type,
            protocol: cand.protocol,
            address: cand.address,
            port: cand.port,
            candidate: cand.candidate
        });
        
        try {
            // Đánh dấu nếu tìm thấy RELAY candidate
            if (cand.type === 'relay') {
                state.hasSentRelayCandidate = true;
                logger.info(`✅ RELAY CANDIDATE for ${remoteClientId} - sending (best for cross-network)`);
                
                // Gửi relay candidates ngay lập tức với độ ưu tiên cao
                await waitForWebSocket();
                sendToServer({
                    type: "CANDIDATE",
                    candidate: event.candidate,
                    target: remoteClientId,
                    priority: "high"
                });
            } else {
                // Đối với các non-relay candidates, gửi với độ ưu tiên thấp hơn
                logger.debug(`Sending ${cand.type.toUpperCase()} candidate for ${remoteClientId}`);
                
                // Độ trễ nhỏ cho các non-relay candidates để ưu tiên relay ones
                await new Promise(resolve => setTimeout(resolve, 100));
                
                await waitForWebSocket();
                sendToServer({
                    type: "CANDIDATE",
                    candidate: event.candidate,
                    target: remoteClientId,
                    priority: "normal"
                });
            }
        } catch (error) {
            logger.error(`Error sending ICE candidate: ${error.message}`);
        }
    } else {
        // ICE candidate gathering hoàn thành
        logger.info(`ICE gathering complete for ${remoteClientId}`);
    }
};

/**
 * Ensures WebSocket is open before sending
 * @returns {Promise<boolean>} Kết nối có sẵn hay không
 */
const waitForWebSocket = async () => {
    if (state.socket.readyState === WebSocket.OPEN) {
        return true; // WebSocket đã sẵn sàng
    }
    
    logger.warn("WebSocket is not open. Waiting for connection...");
    
    // Thêm timeout để tránh chờ đợi vô hạn
    return new Promise((resolve) => {
        const maxWaitTime = 5000; // 5 giây
        const checkInterval = 100; // kiểm tra mỗi 100ms
        let elapsedTime = 0;
        
        const interval = setInterval(() => {
            if (state.socket.readyState === WebSocket.OPEN) {
                clearInterval(interval);
                resolve(true);
                return;
            }
            
            elapsedTime += checkInterval;
            if (elapsedTime >= maxWaitTime) {
                clearInterval(interval);
                logger.error("WebSocket connection timeout");
                resolve(false);
            }
        }, checkInterval);
    });
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

            // Kiểm tra nếu kết nối vẫn 'new' sau một khoảng thời gian, 
            // đây có thể là dấu hiệu của vấn đề nghiêm trọng
            if (pc.connectionState === 'new' && pc.iceConnectionState === 'new') {
                logger.warn(`Connection still in 'new' state for ${remoteClientId} after gathering - potential issue`);
                forceTurnUsage(pc, remoteClientId);
            }
        }, 2000);
    }
};

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

/**
 * Handles connection state changes
 * @param {RTCPeerConnection} pc - The peer connection
 * @param {string} remoteClientId - The ID of the remote client
 */
// Track reconnection attempts per peer
const reconnectionAttempts = new Map();
const MAX_RECONNECTION_ATTEMPTS = 5;
const BASE_RECONNECT_DELAY = 1000; // 1 second base delay

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
            // Increment attempt counter
            reconnectionAttempts.set(remoteClientId, attempts + 1);
            
            // Calculate exponential backoff delay
            const delay = BASE_RECONNECT_DELAY * Math.pow(2, attempts);
            
            logger.info(`Connection recovery attempt ${attempts + 1}/${MAX_RECONNECTION_ATTEMPTS} for ${remoteClientId} in ${delay}ms`);
            
            // Update status
            if (statusDiv) {
                statusDiv.textContent = `Reconnecting (${attempts + 1}/${MAX_RECONNECTION_ATTEMPTS})...`;
            }
            
            // After delay, attempt to restart ICE
            setTimeout(() => {
                // Check if we've reached max attempts
                if (reconnectionAttempts.get(remoteClientId) >= MAX_RECONNECTION_ATTEMPTS) {
                    logger.error(`Maximum reconnection attempts (${MAX_RECONNECTION_ATTEMPTS}) reached for ${remoteClientId}`);
                    
                    if (statusDiv) {
                        statusDiv.textContent = 'Connection failed';
                        statusDiv.style.backgroundColor = 'rgba(255, 0, 0, 0.7)';
                    }
                    
                    // Give up and let the user manually refresh
                    return;
                }
                
                // If connection state is still problematic, try to restart ICE
                if (pc.connectionState !== 'connected') {
                    logger.info(`Attempting ICE restart for ${remoteClientId}`);
                    
                    try {
                        // Try to force TURN after a certain number of attempts
                        if (attempts > 1) {
                            rotateToNextTurnServer(pc, remoteClientId);
                        } else {
                            pc.restartIce();
                        }
                        
                        // Send ICE restart request to remote peer
                        sendToServer({
                            type: "ICE_RESTART",
                            target: remoteClientId,
                            forceRelay: (attempts > 1) // Force relay mode after repeat attempts
                        });
                    } catch (err) {
                        logger.error(`Error during ICE restart: ${err.message}`);
                    }
                }
            }, delay);
        };
        
        // Start recovery attempts after a short delay (if this is the first attempt)
        if (attempts === 0) {
            setTimeout(attemptRecovery, 1000);
        }
        
    } else if (pc.connectionState === 'failed') {
        logger.error(`Connection with ${remoteClientId} has FAILED`);
        
        // Show failure status
        const statusDiv = showConnectionStatus(remoteClientId, 'Connection failed - trying recovery', 'rgba(255, 0, 0, 0.7)', false);
        
        if (statusDiv) {
            statusDiv.style.fontWeight = 'bold';
        }
        
        // Define an aggressive recovery function
        const performAggressiveRecovery = async () => {
            logger.warn(`Starting aggressive recovery for connection with ${remoteClientId}`);
            
            try {
                // Try changing to a completely different TURN server
                const success = await rotateToNextTurnServer(pc, remoteClientId);
                
                if (success) {
                    // Send restart signal to remote peer
                    sendToServer({
                        type: "ICE_RESTART",
                        target: remoteClientId,
                        forceRelay: true,
                        aggressive: true
                    });
                    
                    logger.info(`Aggressive recovery measures initiated for ${remoteClientId}`);
                    
                    if (statusDiv) {
                        statusDiv.textContent = 'Attempting emergency recovery...';
                        statusDiv.style.backgroundColor = 'rgba(255, 0, 0, 0.9)';
                    }
                } else {
                    logger.error(`Failed to apply aggressive recovery for ${remoteClientId}`);
                    
                    if (statusDiv) {
                        statusDiv.textContent = 'Connection recovery failed';
                        statusDiv.style.backgroundColor = 'rgba(255, 0, 0, 0.7)';
                    }
                }
            } catch (err) {
                logger.error(`Error during ICE restart: ${err.message}`);
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
