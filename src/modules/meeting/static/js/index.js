let localStream;
let peerConnections = {};  // Store multiple peer connections
let socket;
let clientId; // Add global clientId variable
let remoteAudioEnabled = {}; // Track the audio state of each remote peer

// Use dynamic server address based on the current location
const serverUrl = window.location.protocol + '//' + window.location.host;
const address = window.location.hostname;
const port = window.location.port || (window.location.protocol === 'https:' ? '443' : '80');

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
    
    // Build WebSocket URL relative to the current page
    // This ensures it works regardless of how users access the site
    const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    
    // Use relative path approach to avoid hostname/port issues
    const wsUrl = `${wsProtocol}//${window.location.host}/ws/${roomName}/${clientId}`;
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

// Global debugging function for WebRTC events
const logRTCEvent = (event, peer, details = {}) => {
    console.log(`[WebRTC] ${event} - Peer: ${peer}`, details);
};

let createPeerConnection = (remoteClientId) => {
    // WebRTC configuration with ICE servers for NAT traversal
    console.log("Creating new RTCPeerConnection with ICE/TURN configuration");
    console.warn("🔄 Configuring connection with adaptive traversal strategy");
    
    // ICE server configuration - The RTCPeerConnection doesn't "connect to" these servers directly
    // They are used as part of the ICE protocol for NAT traversal when direct P2P fails
    const config = {
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
    };    // Handle ICE candidates with extreme debugging capabilities
    pc.onicecandidate = async (event) => {
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
            socket.send(JSON.stringify({
                type: "CANDIDATE",
                candidate: event.candidate,
                target: remoteClientId
            }));
        } else {
            // ICE candidate gathering complete
            console.warn(`🏁 ICE gathering COMPLETE for ${remoteClientId}`);
        }
    };    // Monitor ICE gathering state with enhanced visibility and connection forcing
    pc.onicegatheringstatechange = () => {
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
                    const videoEl = document.getElementById(`video-${remoteClientId}`);
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
                                    socket.send(JSON.stringify({
                                        type: "ICE_RESTART",
                                        target: remoteClientId
                                    }));
                                };
                                videoEl.parentNode.appendChild(playButton);
                            }
                        });
                    }
                    
                    // Force ICE connection restart
                    pc.restartIce();
                    
                    // Send restart signal to the other peer
                    socket.send(JSON.stringify({
                        type: "ICE_RESTART",
                        target: remoteClientId
                    }));
                }
            }, 2000);
        }
    };// Connection state monitoring with enhanced visibility
    pc.onconnectionstatechange = () => {
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
    
    // Update layout based on number of participants
    updateParticipantLayout();
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

// Function to update layout based on number of participants
let updateParticipantLayout = () => {
    const videosContainer = document.getElementById('videos');
    const participantCount = Object.keys(peerConnections).length + 1; // +1 for local user
    
    if (participantCount <= 1) {
        // Single participant mode (just the local user)
        videosContainer.classList.add('single-participant');
    } else {
        // Multiple participants mode
        videosContainer.classList.remove('single-participant');
    }
    
    console.log(`Layout updated for ${participantCount} participants`);
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
