let localStream;
let peerConnections = {};  // Store multiple peer connections
let socket;
let clientId; // Add global clientId variable

const address = '192.168.1.15';

let init = async () => {
    // Get local stream and set it to localVideo
    localStream = await navigator.mediaDevices.getUserMedia({
        video: true,
        audio: false,
    });
    document.getElementById("localVideo").srcObject = localStream;

    // Connect WebSocket
    await connect();
};

let connect = async () => {
    let roomName = window.location.pathname.split("/").pop();
    clientId = Math.random().toString(36).substring(2, 15); // Store clientId globally
    socket = new WebSocket(`wss://${address}:8000/ws/${roomName}/${clientId}`);

    socket.onopen = () => {
        console.log("WebSocket connected!");
        // Announce this user to the room
        socket.send(JSON.stringify({
            type: "JOIN",
            clientId: clientId
        }));
    };

    socket.onmessage = handleMessage;
    console.log("Room Name:", roomName);
    console.log("Client ID:", clientId);
};

let createPeerConnection = (remoteClientId) => {
    const config = {
        iceServers: [
            {
                urls: [
                    'stun:stun1.l.google.com:19302',
                    'stun:stun2.l.google.com:19302',
                ]
            }
        ],
        iceCandidatePoolSize: 10,
    };

    const pc = new RTCPeerConnection(config);

    // Add local tracks to peer connection
    localStream.getTracks().forEach(track => {
        pc.addTrack(track, localStream);
    });

    // Create video element for remote stream
    const videoContainer = document.createElement('div');
    videoContainer.className = 'video-container';
    videoContainer.id = `container-${remoteClientId}`;

    const videoElement = document.createElement('video');
    videoElement.className = 'video-player';
    videoElement.id = `video-${remoteClientId}`;
    videoElement.autoplay = true;
    videoElement.playsinline = true;

    videoContainer.appendChild(videoElement);
    document.getElementById('videos').appendChild(videoContainer);

    // Handle remote tracks
    pc.ontrack = (event) => {
        console.log("Received remote track from:", remoteClientId);
        videoElement.srcObject = event.streams[0];
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
    };

    // Connection state monitoring
    pc.onconnectionstatechange = () => {
        console.log(`Connection state with ${remoteClientId}:`, pc.connectionState);
        if (pc.connectionState === 'disconnected' || pc.connectionState === 'failed') {
            removeRemoteStream(remoteClientId);
        }
    };

    return pc;
};

let handleMessage = async ({ data }) => {
    try {
        data = JSON.parse(data);
        console.log("Received message:", data);

        switch (data.type) {
            case "JOIN":
                if (data.clientId !== clientId) {
                    // Create new peer connection for new user
                    peerConnections[data.clientId] = createPeerConnection(data.clientId);
                    // Create and send offer
                    const offer = await peerConnections[data.clientId].createOffer();
                    await peerConnections[data.clientId].setLocalDescription(offer);
                    socket.send(JSON.stringify({
                        type: "OFFER",
                        offer: offer,
                        target: data.clientId
                    }));
                }
                break;

            case "OFFER":
                if (!peerConnections[data.source]) {
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
                break;

            case "ANSWER":
                if (peerConnections[data.source]) {
                    await peerConnections[data.source].setRemoteDescription(data.answer);
                }
                break;

            case "CANDIDATE":
                if (peerConnections[data.source]) {
                    await peerConnections[data.source].addIceCandidate(data.candidate);
                }
                break;

            case "LEAVE":
                removeRemoteStream(data.clientId);
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
