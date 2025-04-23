/**
 * Media Module
 * Handles media capture, audio/video controls
 */

import { state, updateState } from './state.js';
import { sendToServer } from './signaling.js';

/**
 * Initializes media capture
 * @returns {Promise<MediaStream>} The local media stream
 */
export const initializeMedia = async () => {
    try {
        // Get local stream with both video and audio
        const stream = await navigator.mediaDevices.getUserMedia({
            video: true,
            audio: true, // Enable audio capture
        });
        
        // Store the stream in global state
        updateState({ localStream: stream });
        
        // Set up local video
        document.getElementById("localVideo").srcObject = stream;
        document.getElementById("localVideo").muted = true; // Mute local playback to prevent feedback
        
        // Initialize media status indicators based on initial track states
        const audioTrack = stream.getAudioTracks()[0];
        const videoTrack = stream.getVideoTracks()[0];
        
        // Sử dụng setTimeout để đảm bảo UI đã được tạo
        setTimeout(() => {
            import('./ui.js').then(({ updateMediaStatus }) => {
                if (audioTrack) updateMediaStatus('local', 'audio', audioTrack.enabled);
                if (videoTrack) updateMediaStatus('local', 'video', videoTrack.enabled);
            });
        }, 500);
        
        return stream;
    } catch (error) {
        console.error("Error accessing media devices:", error);
        alert("Failed to access camera or microphone. Please check your permissions.");
        throw error;
    }
};

/**
 * Toggles local audio on/off
 */
export const toggleAudio = () => {
    const audioTrack = state.localStream.getAudioTracks()[0];
    if (audioTrack) {
        audioTrack.enabled = !audioTrack.enabled;
        const audioToggleBtn = document.querySelector('.audio-btn');
        
        // Update title/tooltip instead of changing text
        audioToggleBtn.title = audioTrack.enabled ? 'Mute' : 'Unmute';
        
        // Change button appearance based on state
        if (audioTrack.enabled) {
            audioToggleBtn.classList.remove('disabled');
        } else {
            audioToggleBtn.classList.add('disabled');
        }
        
        // Update local user's mic status indicator
        import('./ui.js').then(({ updateMediaStatus }) => {
            // Sử dụng 'local' làm ID cho người dùng hiện tại
            updateMediaStatus('local', 'audio', audioTrack.enabled);
        });
        
        // Send audio state to all peers
        sendToServer({
            type: "AUDIO_TOGGLE",
            enabled: audioTrack.enabled
        });
        
        console.log(`Microphone ${audioTrack.enabled ? 'enabled' : 'disabled'}`);
    }else {
        console.warn("No audio track found");
    }
};

/**
 * Toggles local video on/off
 */
export const toggleVideo = () => {
    const videoTrack = state.localStream.getVideoTracks()[0];
    if (videoTrack) {
        videoTrack.enabled = !videoTrack.enabled;
        const videoToggleBtn = document.querySelector('.video-btn');
        
        // Update title/tooltip instead of changing text
        videoToggleBtn.title = videoTrack.enabled ? 'Turn Off Camera' : 'Turn On Camera';
        
        // Change button appearance based on state
        if (videoTrack.enabled) {
            videoToggleBtn.classList.remove('disabled');
        } else {
            videoToggleBtn.classList.add('disabled');
        }
        
        // Update local user's camera status indicator
        import('./ui.js').then(({ updateMediaStatus }) => {
            // Sử dụng 'local' làm ID cho người dùng hiện tại
            updateMediaStatus('local', 'video', videoTrack.enabled);
        });
        
        // Send video state to all peers
        sendToServer({
            type: "VIDEO_TOGGLE",
            enabled: videoTrack.enabled
        });
        
        console.log(`Camera ${videoTrack.enabled ? 'enabled' : 'disabled'}`);
    } else {
        console.warn("No video track found");
    }
};

/**
 * Starts screen sharing
 * @returns {Promise<MediaStream>} The screen share stream
 */
export const startScreenShare = async () => {
    try {
        // Check if browser supports getDisplayMedia
        if (!navigator.mediaDevices || !navigator.mediaDevices.getDisplayMedia) {
            throw new Error('Screen sharing is not supported in your browser');
        }

        // Get the screen sharing stream
        const screenStream = await navigator.mediaDevices.getDisplayMedia({
            video: {
                cursor: "always"
            },
            audio: false
        });

        // Store the original video stream to restore later
        updateState({ 
            screenShareActive: true,
            originalVideoStream: state.localStream
        });

        // Replace video track in all peer connections
        const screenVideoTrack = screenStream.getVideoTracks()[0];
        const connections = state.peerConnections || {};

        // Add a handler for when user stops screen sharing via the browser UI
        screenVideoTrack.onended = () => {
            stopScreenShare();
        };

        // Replace track in all peer connections
        Object.values(connections).forEach((pc) => {
            const senders = pc.getSenders();
            const videoSender = senders.find(sender => 
                sender.track && sender.track.kind === 'video'
            );
            if (videoSender) {
                videoSender.replaceTrack(screenVideoTrack);
            }
        });

        // Update the local video display to show screen instead of camera
        const localVideo = document.getElementById("localVideo");
        if (localVideo.srcObject) {
            // Create a new stream with audio from original stream and video from screen share
            const audioTracks = state.localStream.getAudioTracks();
            const newStream = new MediaStream([screenVideoTrack, ...audioTracks]);
            
            // Update the local video element
            localVideo.srcObject = newStream;
            
            // Also update the localStream in state so it's used for new connections
            updateState({ localStream: newStream });
        }

        // Update screen share button appearance
        const screenShareBtn = document.querySelector('.screen-share-btn');
        if (screenShareBtn) {
            screenShareBtn.classList.add('active');
            screenShareBtn.title = 'Stop Sharing';
        }

        // Notify the server about screen sharing
        sendToServer({
            type: "SCREEN_SHARE_STARTED"
        });

        return screenStream;
    } catch (error) {
        console.error("Error starting screen share:", error);
        alert(`Failed to start screen sharing: ${error.message}`);
        throw error;
    }
};

/**
 * Stops screen sharing and restores camera video
 */
export const stopScreenShare = async () => {
    try {
        // Only proceed if screen sharing is active and we have the original stream
        if (!state.screenShareActive || !state.originalVideoStream) {
            return;
        }

        // Get original video track
        const originalVideoTrack = state.originalVideoStream.getVideoTracks()[0];
        if (!originalVideoTrack) {
            throw new Error("Original video track not found");
        }

        // Replace the screen share track with the original video track in all peer connections
        const connections = state.peerConnections || {};
        Object.values(connections).forEach((pc) => {
            const senders = pc.getSenders();
            const videoSender = senders.find(sender => 
                sender.track && sender.track.kind === 'video'
            );
            if (videoSender) {
                videoSender.replaceTrack(originalVideoTrack);
            }
        });

        // Restore the original video stream to local video element
        const localVideo = document.getElementById("localVideo");
        localVideo.srcObject = state.originalVideoStream;

        // Update state
        updateState({
            screenShareActive: false,
            localStream: state.originalVideoStream,
            originalVideoStream: null
        });

        // Update screen share button appearance
        const screenShareBtn = document.querySelector('.screen-share-btn');
        if (screenShareBtn) {
            screenShareBtn.classList.remove('active');
            screenShareBtn.title = 'Share Screen';
        }

        // Notify the server about screen sharing stopped
        sendToServer({
            type: "SCREEN_SHARE_STOPPED"
        });

        console.log("Screen sharing stopped");
    } catch (error) {
        console.error("Error stopping screen share:", error);
        alert(`Failed to stop screen sharing: ${error.message}`);
    }
};

/**
 * Toggle screen sharing on/off
 */
export const toggleScreenShare = async () => {
    try {
        if (state.screenShareActive) {
            await stopScreenShare();
        } else {
            await startScreenShare();
        }
    } catch (error) {
        console.error("Error toggling screen share:", error);
    }
};
