let localStream;
let peerConnections = {};  // Store multiple peer connections
let socket;
let clientId; // Add global clientId variable
let remoteAudioEnabled = {}; // Track the audio state of each remote peer

// Use the fixed server address
const serverUrl = 'https://csavn.ddns.net:8000';
const address = 'csavn.ddns.net';
const port = 8000;

let init = async () => {
    try {
        // Get local stream with both video and audio
        localStream = await navigator.mediaDevices.getUserMedia({
            video: true,
            audio: true, // Enable audio capture
        });        document.getElementById("localVideo").srcObject = localStream;
        
        // Add audio controls to local video
        document.getElementById("localVideo").muted = true; // Mute local playback to prevent feedback
        
        // Create controls container
        const controlsContainer = document.createElement('div');
        controlsContainer.id = 'controls-container';
        document.body.appendChild(controlsContainer);
          // Add audio toggle button
        const audioToggleBtn = document.createElement('button');
        audioToggleBtn.innerHTML = '<i class="mic-icon"></i>';
        audioToggleBtn.title = 'Mute';
        audioToggleBtn.className = 'control-button audio-btn';
        audioToggleBtn.onclick = toggleAudio;
        controlsContainer.appendChild(audioToggleBtn);
        
        // Add video toggle button
        const videoToggleBtn = document.createElement('button');
        videoToggleBtn.innerHTML = '<i class="camera-icon"></i>';
        videoToggleBtn.title = 'Turn Off Camera';
        videoToggleBtn.className = 'control-button video-btn';
        videoToggleBtn.onclick = toggleVideo;
        controlsContainer.appendChild(videoToggleBtn);
          // Add chat button
        const chatToggleBtn = document.createElement('button');
        chatToggleBtn.innerHTML = '<i class="chat-icon"></i>';
        chatToggleBtn.title = 'Chat';
        chatToggleBtn.className = 'control-button chat-btn';
        chatToggleBtn.onclick = toggleChat;
        controlsContainer.appendChild(chatToggleBtn);
        
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
        
        // Add event listeners for chat
        document.querySelector('.close-chat').onclick = toggleChat;
        sendBtn.onclick = sendChatMessage;
        chatInput.addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                sendChatMessage();
            }
        });
    } catch (error) {
        console.error("Error accessing media devices:", error);
        alert("Failed to access camera or microphone. Please check your permissions.");
    }

    // Connect WebSocket
    await connect();
};

let connect = async () => {
    let roomName = window.location.pathname.split("/").pop();
    clientId = Math.random().toString(36).substring(2, 15); // Store clientId globally
    
    // Use secure WebSocket for the HTTPS server
    const wsUrl = `wss://${address}:${port}/ws/${roomName}/${clientId}`;
    console.log("Connecting to WebSocket at:", wsUrl);
    
    socket = new WebSocket(wsUrl);
    
    socket.onopen = () => {
        console.log("WebSocket connected!");
        // Announce this user to the room
        socket.send(JSON.stringify({
            type: "JOIN",
            clientId: clientId
        }));
    };
    
    socket.onerror = (error) => {
        console.error("WebSocket error:", error);
    };

    socket.onmessage = handleMessage;
    console.log("Room Name:", roomName);
    console.log("Client ID:", clientId);
};

// Toggle microphone on/off
let toggleAudio = () => {
    const audioTrack = localStream.getAudioTracks()[0];
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
        if (socket && socket.readyState === WebSocket.OPEN) {
            socket.send(JSON.stringify({
                type: "AUDIO_TOGGLE",
                enabled: audioTrack.enabled
            }));
        }
        
        console.log(`Microphone ${audioTrack.enabled ? 'enabled' : 'disabled'}`);
    } else {
        console.warn("No audio track found");
    }
};

// Toggle video on/off
let toggleVideo = () => {
    const videoTrack = localStream.getVideoTracks()[0];
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
        if (socket && socket.readyState === WebSocket.OPEN) {
            socket.send(JSON.stringify({
                type: "VIDEO_TOGGLE",
                enabled: videoTrack.enabled
            }));
        }
        
        console.log(`Camera ${videoTrack.enabled ? 'enabled' : 'disabled'}`);
    } else {
        console.warn("No video track found");
    }
};

// Toggle chat panel
let toggleChat = () => {
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

// Send chat message
let sendChatMessage = () => {
    const input = document.getElementById('chat-input');
    const message = input.value.trim();
    
    if (message) {
        // Add message to local chat
        addMessageToChat(message, true);
        
        // Send message to peers
        if (socket && socket.readyState === WebSocket.OPEN) {
            socket.send(JSON.stringify({
                type: "CHAT_MESSAGE",
                message: message
            }));
        }
        
        // Clear input
        input.value = '';
    }
    
    // Keep focus on input
    input.focus();
};

// Add message to chat container
let addMessageToChat = (message, isLocal = false) => {
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

let createPeerConnection = (remoteClientId) => {
    const config = {
        iceServers: [
            {
                urls: [
                    'stun:stun1.l.google.com:19302',
                    'stun:stun2.l.google.com:19302',
                ]
            },
            // More reliable TURN servers
            {
                urls: [
                    'turn:relay.metered.ca:80',
                    'turn:relay.metered.ca:443',
                    'turn:relay.metered.ca:443?transport=tcp'
                ],
                username: 'e734a26b1512cce7fe01c6e5',
                credential: 'OgVBgEG5BqDQyXeC'
            }
        ],
        iceTransportPolicy: 'all',
        iceCandidatePoolSize: 10,
        sdpSemantics: 'unified-plan'
    };

    const pc = new RTCPeerConnection(config);
    console.log(pc)

    // Add local tracks to peer connection
    localStream.getTracks().forEach(track => {
        pc.addTrack(track, localStream);
    });    // Create video element for remote stream
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
    document.getElementById('videos').appendChild(videoContainer);    // Handle remote tracks
    pc.ontrack = (event) => {
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
                        const playButton = document.createElement('button');
                        playButton.innerText = 'Click to Unmute/Play';
                        playButton.id = `play-button-${remoteClientId}`;
                        playButton.className = 'play-button';
                        playButton.onclick = () => {
                            videoElement.play();
                            playButton.style.display = 'none';
                        };
                        videoContainer.appendChild(playButton);
                    }
                });
            }
        };
    };

    // Handle ICE candidates
    pc.onicecandidate = async (event) => {
        if (event.candidate) {
            await waitForWebSocket();
            socket.send(JSON.stringify({
                type: "CANDIDATE",
                candidate: event.candidate,
                target: remoteClientId
            }));
        }
    };    // Connection state monitoring
    pc.onconnectionstatechange = () => {
        console.log(`Connection state with ${remoteClientId}:`, pc.connectionState);
        
        if (pc.connectionState === 'disconnected') {
            console.log(`Connection with ${remoteClientId} is unstable, waiting to see if it recovers...`);
            
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
                socket.send(JSON.stringify({
                    type: "ICE_RESTART",
                    target: remoteClientId
                }));
                
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
                peerConnections[remoteClientId] = newPC;
                
                // Create a new offer with ice restart
                setTimeout(async () => {
                    try {
                        const offerOptions = {
                            offerToReceiveAudio: true,
                            offerToReceiveVideo: true,
                            iceRestart: true
                        };
                        const offer = await newPC.createOffer(offerOptions);
                        await newPC.setLocalDescription(offer);
                        
                        // Send the offer
                        socket.send(JSON.stringify({
                            type: "OFFER",
                            offer: offer,
                            target: remoteClientId,
                            isReconnect: true
                        }));
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
    
    // Add specific ICE connection state monitoring
    pc.oniceconnectionstatechange = () => {
        console.log(`ICE connection state with ${remoteClientId}: ${pc.iceConnectionState}`);
        
        // Handle specific ICE connection states
        if (pc.iceConnectionState === 'disconnected') {
            console.log(`ICE connection with ${remoteClientId} is disconnected, waiting...`);
        } else if (pc.iceConnectionState === 'failed') {
            console.log(`ICE connection with ${remoteClientId} failed, will attempt restart`);
            socket.send(JSON.stringify({
                type: "ICE_RESTART",
                target: remoteClientId
            }));
        }
    };

    return pc;
};

let handleMessage = async ({ data }) => {
    try {
        data = JSON.parse(data);
        console.log("Received message:", data);        switch (data.type) {
            case "JOIN":
                if (data.clientId !== clientId) {
                    console.log(`New user joined: ${data.clientId}. Creating peer connection...`);
                    // Create new peer connection for new user
                    peerConnections[data.clientId] = createPeerConnection(data.clientId);                    
                    // Use a timeout to ensure ICE gathering has started before creating offer
                    setTimeout(async () => {
                        try {
                            // Create offer with specific constraints for better compatibility
                            const offerOptions = {
                                offerToReceiveAudio: true,
                                offerToReceiveVideo: true,
                                voiceActivityDetection: false,
                                iceRestart: true
                            };
                            
                            // Use trickle ICE approach (sending candidates as they arrive)
                            const pc = peerConnections[data.clientId];
                            
                            // Set up a collector for early ICE candidates
                            const iceCandidatesCache = [];
                            const originalOnIceCandidate = pc.onicecandidate;
                            pc.onicecandidate = (event) => {
                                if (event.candidate) {
                                    iceCandidatesCache.push(event.candidate);
                                }
                                // Still call original handler
                                if (originalOnIceCandidate) originalOnIceCandidate(event);
                            };
                            
                            const offer = await pc.createOffer(offerOptions);
                            await pc.setLocalDescription(offer);
                            
                            // Wait briefly to allow some ICE candidates to be gathered
                            console.log("Waiting for ICE candidates before sending offer...");
                            await new Promise(resolve => setTimeout(resolve, 2000));
                            
                            // Send the offer with any collected candidates
                            socket.send(JSON.stringify({
                                type: "OFFER",
                                offer: peerConnections[data.clientId].localDescription,
                                target: data.clientId
                            }));
                            console.log(`Offer sent to ${data.clientId}`);
                        } catch (err) {
                            console.error("Error creating/sending offer:", err);
                        }
                    }, 500);
                }
                break;            case "OFFER":
                try {
                    console.log(`Received offer from ${data.source}`);
                    if (!peerConnections[data.source]) {
                        console.log(`Creating peer connection for ${data.source}`);
                        peerConnections[data.source] = createPeerConnection(data.source);
                    }
                    await peerConnections[data.source].setRemoteDescription(data.offer);
                    const answer = await peerConnections[data.source].createAnswer();
                    await peerConnections[data.source].setLocalDescription(answer);
                    socket.send(JSON.stringify({
                        type: "ANSWER",
                        answer: answer,
                        target: data.source
                    }));
                } catch (err) {
                    console.error("Error handling offer:", err);
                }
                break;            case "ANSWER":
                if (peerConnections[data.source]) {
                    await peerConnections[data.source].setRemoteDescription(data.answer);
                }
                break;

            case "CANDIDATE":
                if (peerConnections[data.source]) {
                    await peerConnections[data.source].addIceCandidate(data.candidate);
                }
                break;
                
            case "ICE_RESTART":
                if (peerConnections[data.source]) {
                    try {
                        console.log(`Attempting ICE restart with ${data.source}`);
                        const offerOptions = {
                            offerToReceiveAudio: true,
                            offerToReceiveVideo: true,
                            iceRestart: true
                        };
                        const offer = await peerConnections[data.source].createOffer(offerOptions);
                        await peerConnections[data.source].setLocalDescription(offer);
                        socket.send(JSON.stringify({
                            type: "OFFER",
                            offer: offer,
                            target: data.source,
                            isIceRestart: true
                        }));
                    } catch (err) {
                        console.error("Error during ICE restart:", err);
                    }
                }
                break;
                
            case "LEAVE":
                removeRemoteStream(data.clientId);
                break;
                  case "AUDIO_TOGGLE":
                // Handle remote user's audio state change
                console.log(`Remote user ${data.source} ${data.enabled ? 'unmuted' : 'muted'} their microphone`);
                // You could update UI to show mute status if desired
                break;
                
            case "CHAT_MESSAGE":
                // Handle incoming chat message from another user
                console.log(`Chat message from ${data.source}: ${data.message}`);
                addMessageToChat({
                    sender: `User ${data.source.substring(0, 5)}...`,
                    text: data.message
                }, false);
                break;
        }
    } catch (err) {
        console.error("Error handling message:", err);
    }
};

let removeRemoteStream = (clientId) => {
    if (peerConnections[clientId]) {
        peerConnections[clientId].close();
        delete peerConnections[clientId];
    }
    const container = document.getElementById(`container-${clientId}`);
    if (container) {
        container.remove();
    }
};

let waitForWebSocket = async () => {
    if (socket.readyState !== WebSocket.OPEN) {
        console.warn("WebSocket is not open. Waiting...");
        await new Promise((resolve) => {
            const interval = setInterval(() => {
                if (socket.readyState === WebSocket.OPEN) {
                    clearInterval(interval);
                    resolve();
                }
            }, 100);
        });
    }
};

// Handle page unload
window.onbeforeunload = () => {
    if (socket) {
        socket.send(JSON.stringify({
            type: "LEAVE",
            clientId: clientId
        }));
    }
};

document.addEventListener('DOMContentLoaded', init);
