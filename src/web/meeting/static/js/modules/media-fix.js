/**
 * Media Fix Module
 * Specialized tools for diagnosing and fixing WebRTC media issues
 */

import { logger } from './logger.js';
import { showNotification } from './ui.js';

/**
 * Diagnose media stream problems
 * @param {MediaStream} stream - The media stream to check
 * @param {string} clientId - The client ID for logging
 * @returns {Object} Diagnosis results
 */
export const diagnoseMediaStream = (stream, clientId) => {
    const issues = [];
    
    if (!stream) {
        logger.error(`No media stream found for ${clientId}`);
        return { hasIssues: true, issues: ['No media stream available'] };
    }
    
    // Check stream activity
    if (!stream.active) {
        issues.push('Stream is inactive');
    }
    
    // Check audio tracks
    const audioTracks = stream.getAudioTracks();
    if (audioTracks.length === 0) {
        issues.push('No audio tracks in stream');
    } else {
        for (const track of audioTracks) {
            if (!track.enabled) {
                issues.push('Audio track is disabled');
            }
            if (track.muted) {
                issues.push('Audio track is muted');
            }
            if (track.readyState !== 'live') {
                issues.push(`Audio track is not live (${track.readyState})`);
            }
        }
    }
    
    // Check video tracks
    const videoTracks = stream.getVideoTracks();
    if (videoTracks.length === 0) {
        issues.push('No video tracks in stream');
    } else {
        for (const track of videoTracks) {
            if (!track.enabled) {
                issues.push('Video track is disabled');
            }
            if (track.muted) {
                issues.push('Video track is muted');
            }
            if (track.readyState !== 'live') {
                issues.push(`Video track is not live (${track.readyState})`);
            }
        }
    }
    
    return {
        hasIssues: issues.length > 0,
        issues,
        hasAudio: audioTracks.length > 0,
        hasVideo: videoTracks.length > 0
    };
};

/**
 * Create a button to unmute audio for a video element
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
            // Unmute the video element itself
            videoElement.muted = false;
            
            // Also ensure the audio tracks are enabled
            if (videoElement.srcObject) {
                const audioTracks = videoElement.srcObject.getAudioTracks();
                audioTracks.forEach(track => {
                    track.enabled = true;
                });
                logger.info(`Enabled ${audioTracks.length} audio tracks for ${clientId}`);
                
                // Force video tracks to be enabled too
                const videoTracks = videoElement.srcObject.getVideoTracks();
                videoTracks.forEach(track => {
                    track.enabled = true;
                });
                logger.info(`Enabled ${videoTracks.length} video tracks for ${clientId}`);
            }
            
            unmuteButton.style.display = 'none';
            logger.info(`Audio unmuted for ${clientId}`);
            showNotification('Audio unmuted', 'success');
            
            // Force browser to update the display
            videoElement.style.opacity = '0.99';
            setTimeout(() => {
                videoElement.style.opacity = '1';
            }, 100);
        } catch (err) {
            logger.error(`Failed to unmute audio: ${err.message}`);
        }
    };
    
    container.appendChild(unmuteButton);
    return unmuteButton;
};

/**
 * Fix common media issues on a video element
 * @param {HTMLVideoElement} videoElement - The video element to fix
 * @param {string} clientId - The client ID for logging
 */
export const fixMediaPlayback = async (videoElement, clientId) => {
    if (!videoElement) {
        logger.error(`Cannot fix media for ${clientId}: Video element not found`);
        return false;
    }
    
    const stream = videoElement.srcObject;
    if (!stream) {
        logger.error(`Cannot fix media for ${clientId}: No stream in video element`);
        return false;
    }
    
    let fixesApplied = false;
    
    // First, ensure all tracks are enabled
    const allTracks = stream.getTracks();
    for (const track of allTracks) {
        if (!track.enabled) {
            track.enabled = true;
            logger.info(`Enabled ${track.kind} track for ${clientId}`);
            fixesApplied = true;
        }
    }
    
    // Try to force unmuting of muted tracks
    allTracks.forEach(track => {
        if (track.muted) {
            // This is a browser constraint, but we'll try a workaround
            track.enabled = true;
            logger.info(`Attempted to unmute ${track.kind} track for ${clientId}`);
        }
    });
    
    // Force stream to play
    try {
        // First ensure it's muted to allow autoplay
        videoElement.muted = true;
        
        // For Chrome's benefit, create a user gesture simulation
        const userGesture = () => {
            document.body.removeEventListener('click', userGesture);
            videoElement.play().catch(e => {
                logger.warn(`Could not play after user gesture: ${e.message}`);
            });
        };
        document.body.addEventListener('click', userGesture, { once: true });
        
        // Try to play the video
        await videoElement.play();
        logger.info(`Successfully started video playback for ${clientId}`);
        fixesApplied = true;
        
        // Ensure video is visible
        videoElement.classList.add('has-remote-media');
        videoElement.classList.remove('video-muted');
        
        // Force browser to refresh rendering
        videoElement.style.opacity = '0.99';
        setTimeout(() => {
            videoElement.style.opacity = '1';
        }, 100);
        
        // Check if audioContext is needed to kick-start audio
        const audioTracks = stream.getAudioTracks();
        if (audioTracks.length > 0) {
            try {
                // Create a dummy audio context to kick-start audio processing
                const audioContext = new (window.AudioContext || window.webkitAudioContext)();
                const source = audioContext.createMediaStreamSource(stream);
                const dest = audioContext.createMediaStreamDestination();
                source.connect(dest);
                
                // Try to activate audio context with user gesture simulation
                audioContext.resume().then(() => {
                    logger.info(`AudioContext resumed for ${clientId}`);
                }).catch(e => {
                    logger.warn(`Could not resume AudioContext: ${e.message}`);
                });
                
                // Disconnect after a moment to avoid feedback loops
                setTimeout(() => {
                    try {
                        source.disconnect();
                    } catch (e) {
                        // Ignore disconnect errors
                    }
                }, 1000);
                
                logger.info(`Audio processing initialized for ${clientId}`);
            } catch (err) {
                logger.warn(`Could not initialize audio processing: ${err.message}`);
            }
        }
        
        // Add unmute button to let user unmute
        const container = videoElement.parentElement;
        if (container) {
            createUnmuteButton(clientId, container, videoElement);
        }
    } catch (err) {
        logger.error(`Failed to fix media playback: ${err.message}`);
        return false;
    }
    
    return fixesApplied;
};

/**
 * Add status overlay to a video
 * @param {string} clientId - The client ID
 * @param {string} message - The status message
 * @param {string} type - The status type (error, warning, success)
 */
export const showMediaStatus = (clientId, message, type = 'warning') => {
    const container = document.getElementById(`container-${clientId}`);
    if (!container) return null;
    
    // Remove any existing status
    const existingStatus = container.querySelector('.media-status');
    if (existingStatus) {
        existingStatus.remove();
    }
    
    const statusDiv = document.createElement('div');
    statusDiv.className = `media-status ${type}`;
    statusDiv.textContent = message;
    statusDiv.style.position = 'absolute';
    statusDiv.style.top = '35px'; // Below connection status
    statusDiv.style.right = '5px';
    statusDiv.style.padding = '3px 8px';
    statusDiv.style.borderRadius = '5px';
    statusDiv.style.fontSize = '12px';
    statusDiv.style.zIndex = '10';
    
    // Set color based on type
    if (type === 'error') {
        statusDiv.style.backgroundColor = 'rgba(255, 0, 0, 0.7)';
    } else if (type === 'warning') {
        statusDiv.style.backgroundColor = 'rgba(255, 165, 0, 0.7)';
    } else if (type === 'success') {
        statusDiv.style.backgroundColor = 'rgba(0, 255, 0, 0.7)';
    }
    statusDiv.style.color = 'white';
    
    container.appendChild(statusDiv);
    
    // Make temporary if success
    if (type === 'success') {
        setTimeout(() => {
            if (statusDiv.parentNode) {
                statusDiv.remove();
            }
        }, 5000);
    }
    
    return statusDiv;
};
