/**
 * WebRTC Configuration Module
 * Contains configuration settings for WebRTC connections and ICE servers
 */

// WebRTC configuration with ICE servers for NAT traversal
export const getRTCConfig = () => {
    return {
        // Start with 'all' to try direct connections first, only use relay if necessary
        // In severe network conditions, can be changed to 'relay' to force TURN usage
        iceTransportPolicy: 'all',
        
        // List potential STUN/TURN servers for the ICE agent to use if needed
        iceServers: [
            // STUN servers for basic NAT traversal (tried first)
            { urls: 'stun:stun.l.google.com:19302' },
            { urls: 'stun:stun1.l.google.com:19302' },
            
            // TURN server as fallback for symmetrical NATs or strict firewalls
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

// Use dynamic server address based on the current location
export const serverUrl = window.location.protocol + '//' + window.location.host;
export const address = window.location.hostname;
export const port = window.location.port || (window.location.protocol === 'https:' ? '443' : '80');

// Offer options for creating WebRTC offers
export const offerOptions = {
    offerToReceiveAudio: true,
    offerToReceiveVideo: true,
    voiceActivityDetection: false,
    iceRestart: true
};
