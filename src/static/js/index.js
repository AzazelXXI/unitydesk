let localStream;
let remoteStream;
let peerConnection;
let socket;
let makingOffer = false;
let polite = false

const address = "192.168.1.15"

let init = async () => {
    // Get local stream and set it to user-1
    localStream = await navigator.mediaDevices.getUserMedia({
        video: true,
        audio: false,
    });
    document.getElementById("user-1").srcObject = localStream;

    // Initialize PeerConnection and streams
    await createStreams();

    // Connect WebSocket
    await connect(createAndSendOffer);
};

let connect = async (callback) => {
    let roomName = decodeURIComponent(window.location.pathname.split("/")[1]);
    let clientId = Math.random().toString(36).substring(2, 15); // Tạo client_id ngẫu nhiên
    socket = new WebSocket(`wss://${address}:8000/ws/${roomName}/${clientId}`);

    socket.onopen = async (_) => {
        console.log("WebSocket connected!");
        await callback();
    };

    socket.onmessage = handleMessage;

    console.log("Room Name:", roomName);
    console.log("Client ID:", clientId);
};

let handleMessage = async ({ data }) => {
    try {
        data = JSON.parse(data);
        console.log("Received message:", data);

        if (data["type"] === "USER_JOIN") {
            polite = true;
            if (!peerConnection) {
                await createStreams();
            }
            await createAndSendOffer();
        } else if (data["type"] === "OFFER") {
            console.log("Received offer");
            if (!peerConnection) {
                await createStreams();
            }

            const offerCollision = data.message.type === "offer" &&
                (makingOffer || peerConnection.signalingState !== "stable");

            ignoreOffer = !polite && offerCollision;
            if (ignoreOffer) {
                console.log("Ignoring offer due to collision");
                return;
            }

            try {
                await peerConnection.setRemoteDescription(data.message);
                const answer = await peerConnection.createAnswer();
                await peerConnection.setLocalDescription(answer);
                socket.send(JSON.stringify({
                    type: "ANSWER",
                    message: peerConnection.localDescription
                }));
            } catch (err) {
                console.error("Error handling offer:", err);
            }
        } else if (data["type"] === "ANSWER") {
            console.log("Received answer");
            if (peerConnection.signalingState === "have-local-offer") {
                try {
                    await peerConnection.setRemoteDescription(data.message);
                } catch (e) {
                    console.error("Error setting remote description:", e);
                }
            } else {
                console.log("Ignoring answer - wrong signaling state:", peerConnection.signalingState);
            }
        } else if (data["type"] === "candidate") {
            console.log("Received ICE candidate");
            try {
                if (data.candidate) {
                    await peerConnection.addIceCandidate(data.candidate);
                }
            } catch (e) {
                if (!ignoreOffer) {
                    console.error("Error adding received ice candidate:", e);
                }
            }
        }
    } catch (err) {
        console.error("Error handling message:", err);
    }
};

let createStreams = async () => {
    console.log("Initializing PeerConnection and streams...");

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

    peerConnection = new RTCPeerConnection(config);
    remoteStream = new MediaStream();

    // Set up local stream if not already set
    if (!localStream) {
        try {
            localStream = await navigator.mediaDevices.getUserMedia({
                video: true,
                audio: false
            });
            document.getElementById("user-1").srcObject = localStream;
        } catch (e) {
            console.error("Error getting user media:", e);
            return;
        }
    }

    // Add local tracks to peer connection
    localStream.getTracks().forEach(track => {
        peerConnection.addTrack(track, localStream);
    });

    // Set up remote video element
    const remoteVideo = document.getElementById("user-2");
    remoteVideo.srcObject = remoteStream;

    // Handle remote tracks
    peerConnection.ontrack = (event) => {
        console.log("Received remote track:", event.track.kind);
        event.streams[0].getTracks().forEach(track => {
            console.log("Adding track to remote stream:", track.kind);
            remoteVideo.srcObject = event.streams[0];
        });
    };

    // Monitor connection states
    peerConnection.onconnectionstatechange = () => {
        console.log("Connection state:", peerConnection.connectionState);
        if (peerConnection.connectionState === 'connected') {
            console.log("Peers connected successfully!");
        }
    };

    peerConnection.oniceconnectionstatechange = () => {
        console.log("ICE connection state:", peerConnection.iceConnectionState);
    };

    peerConnection.onicegatheringstatechange = () => {
        console.log("ICE gathering state:", peerConnection.iceGatheringState);
    };

    peerConnection.onsignalingstatechange = () => {
        console.log("Signaling state:", peerConnection.signalingState);
    };

    // Handle ICE candidates
    peerConnection.onicecandidate = async (event) => {
        if (event.candidate) {
            await waitForWebSocket();
            socket.send(JSON.stringify({
                type: "candidate",
                candidate: event.candidate
            }));
        }
    };

    // Handle negotiation
    peerConnection.onnegotiationneeded = async () => {
        try {
            if (makingOffer) return;
            makingOffer = true;

            await peerConnection.setLocalDescription(await peerConnection.createOffer());
            await waitForWebSocket();
            socket.send(JSON.stringify({
                type: "OFFER",
                message: peerConnection.localDescription
            }));
        } catch (err) {
            console.error("Error during negotiation:", err);
        } finally {
            makingOffer = false;
        }
    };
};

let createAndSendOffer = async () => {
    if (!peerConnection) {
        console.warn("PeerConnection is not initialized. Initializing now...");
        await createStreams();
    }

    if (makingOffer) return; // Ngăn chặn việc tạo offer mới khi đang trong quá trình
    makingOffer = true;
    try {
        let offer = await peerConnection.createOffer();
        await peerConnection.setLocalDescription(offer);
        socket.send(
            JSON.stringify({
                type: "OFFER",
                message: peerConnection.localDescription,
            })
        );
    } catch (err) {
        console.error("Error creating offer:", err);
    } finally {
        makingOffer = false;
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
            }, 100); // Kiểm tra mỗi 100ms
        });
    }
};

document.addEventListener(
    "DOMContentLoaded",
    async function () {
        await init();

        // Kiểm tra kết nối WebSocket
        let testSocket = new WebSocket(`wss://${address}:8000/ws/room/test-client`);
        testSocket.onopen = () => console.log("WebSocket connected!");
        testSocket.onerror = (error) => console.error("WebSocket error:", error);
    },
    false
);
