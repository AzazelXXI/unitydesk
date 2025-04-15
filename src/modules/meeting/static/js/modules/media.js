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
        
        // Send audio state to all peers
        sendToServer({
            type: "AUDIO_TOGGLE",
            enabled: audioTrack.enabled
        });
        
        console.log(`Microphone ${audioTrack.enabled ? 'enabled' : 'disabled'}`);
    } else {
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
