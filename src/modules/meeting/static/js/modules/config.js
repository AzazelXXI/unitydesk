/**
 * WebRTC Configuration Module
 * Contains configuration settings for WebRTC connections and ICE servers
 */

// WebRTC configuration with ICE servers for NAT traversal
export const getRTCConfig = () => {
    return {
        // For cross-network connections, use 'relay' to force TURN usage and ensure connectivity
        // This ensures connectivity even through complex NAT and firewalls
        iceTransportPolicy: 'relay',
        
        // List potential STUN/TURN servers for the ICE agent to use if needed
        iceServers: [
            // STUN servers for basic NAT traversal
            { urls: 'stun:stun.l.google.com:19302' },
            { urls: 'stun:stun1.l.google.com:19302' },
            { urls: 'stun:stun.stunprotocol.org:3478' },
            
            // TURN server for relaying through NAT/firewalls
            // Uses TLS on port 443 to bypass firewall restrictions
            {
                urls: 'turns:global.turn.twilio.com:443',
                username: '9e9794d921e1be3e773d84a9d810a4f51a2a80f2949e3b7b113abe27fb4d048e',
                credential: 'S/17VCcuxpJSQV50YpH0NXai5qELoKNJJ2l2yF8HM+A='
            }
        ],
        
        // Standard WebRTC options
        sdpSemantics: 'unified-plan',
        bundlePolicy: 'max-bundle',
        rtcpMuxPolicy: 'require'
    };
};

// Always use the DDNS domain for consistent connectivity across networks
export const serverUrl = window.location.protocol + '//csavn.ddns.net:8000/';
export const address = 'csavn.ddns.net';
export const port = '8000';

// Offer options for creating WebRTC offers
export const offerOptions = {
    offerToReceiveAudio: true,
    offerToReceiveVideo: true,
    voiceActivityDetection: false,
    iceRestart: true
};
