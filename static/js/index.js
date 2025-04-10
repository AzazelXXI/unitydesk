let localStream;
let remoteStream;
let peerConnection;
let socket;
let makingOffer = false;
let polite = false

let init = async () => {
    localStream = await navigator.mediaDevices.getUserMedia({
        video: true,
        audio: false,
    });
    document.getElementById("user-1").srcObject = localStream;

    // Khởi tạo PeerConnection và các stream
    await createStreams();

    // Kết nối WebSocket
    await connect(createAndSendOffer);
};

let connect = async (callback) => {
    let roomName = decodeURIComponent(window.location.pathname.split("/")[1]);
    let clientId = Math.random().toString(36).substring(2, 15); // Tạo client_id ngẫu nhiên
    socket = new WebSocket(`wss://192.168.1.34:8000/ws/${roomName}/${clientId}`);

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
                console.warn("PeerConnection is not initialized. Initializing now...");
                await createStreams();
            }
            createAndSendOffer();
        } else if (data["type"] === "OFFER") {
            console.log("Received offer");
            await createAndSendAnswer(data["message"]);
        } else if (data["type"] === "ANSWER") {
            console.log("Received answer");
            await peerConnection.setRemoteDescription(data["message"]);
        } else if (data["type"] === "candidate") {
            console.log("Received ICE candidate");
            await handleIceCandidate(data["candidate"]);
        } else {
            console.warn("Unknown message type:", data["type"]);
        }
    } catch (err) {
        console.error("Error handling message:", err);
    }
};

let createAndSendAnswer = async (message) => {
    try {
        if (!peerConnection) {
            console.warn("PeerConnection is not initialized. Initializing now...");
            await createStreams();
        }

        await peerConnection.setRemoteDescription(message);
        const answer = await peerConnection.createAnswer();
        await peerConnection.setLocalDescription(answer);
        socket.send(
            JSON.stringify({
                type: "ANSWER",
                message: peerConnection.localDescription,
            })
        );
        console.log("Sent SDP answer:", peerConnection.localDescription);
    } catch (err) {
        console.error("Error creating answer:", err);
    }
};

let handleOffers = async ({ message }) => {
    await createAndSendAnswer(message);
};

let handleAnswers = async ({ message }) => {
    try {
        console.log("Received SDP answer:", message.sdp);

        // Thêm dòng `s=` nếu bị thiếu
        if (!message.sdp.includes("\ns=")) {
            message.sdp = message.sdp.replace("v=0", "v=0\ns=-");
        }

        await peerConnection.setRemoteDescription(message);
        console.log("SDP answer set successfully.");
    } catch (err) {
        console.error("Error setting SDP answer:", err);
    }
};

let handleIceCandidate = async (candidate) => {
    try {
        if (candidate && candidate.candidate) {
            console.log("Adding ICE candidate:", candidate);
            await peerConnection.addIceCandidate(candidate);
        } else {
            console.warn("Invalid ICE candidate:", candidate);
        }
    } catch (err) {
        console.error("Error adding ICE candidate:", err);
    }
};

let handlePerfectNegotiation = async ({ message }) => {
    try {
        if (message) {
            const offerCollision =
                message.type === "offer" &&
                (makingOffer || peerConnection.signalingState !== "stable");

            ignoreOffer = !polite && offerCollision;
            if (ignoreOffer) {
                return;
            }

            await peerConnection.setRemoteDescription(message);
            if (message.type === "offer") {
                await peerConnection.setLocalDescription();
                socket.send(JSON.stringify({
                    type: "ANSWER",
                    message: peerConnection.localDescription,
                }));
            }
        }
    } catch (err) {
        console.error(err);
    }
};

const config = {
    iceServers: [
        {
            urls: [
                "stun:stun1.l.google.com:19302",
                "stun:stun2.l.google.com:19302",
            ],
        },
        {
            urls: "turn:your-turn-server",
            username: "user",
            credential: "pass",
        },
    ],
};

let createStreams = async () => {
    console.log("Initializing PeerConnection and streams...");
    peerConnection = new RTCPeerConnection(config);
    remoteStream = new MediaStream();

    localStream.getTracks().forEach((track) => {
        peerConnection.addTrack(track, localStream);
    });

    peerConnection.ontrack = (event) => {
        console.log("Adding track to remote stream");
        event.streams[0]
            .getTracks()
            .forEach((track) => remoteStream.addTrack(track));
    };

    peerConnection.onicecandidate = async (event) => {
        if (event.candidate) {
            console.log("Sending ICE candidate:", event.candidate);

            // Đợi WebSocket sẵn sàng
            await waitForWebSocket();

            socket.send(
                JSON.stringify({ type: "candidate", candidate: event.candidate })
            );
        }
    };

    peerConnection.onnegotiationneeded = async () => {
        try {
            makingOffer = true;
            console.log("Starting negotiation...");

            // Đợi WebSocket sẵn sàng
            await waitForWebSocket();

            await peerConnection.setLocalDescription();
            socket.send(
                JSON.stringify({
                    type: "OFFER",
                    message: peerConnection.localDescription,
                })
            );
            console.log("Sent SDP offer:", peerConnection.localDescription);
        } catch (err) {
            console.error("Error during negotiation:", err);
        } finally {
            makingOffer = false;
        }
    };

    // Chèn sự kiện onconnectionstatechange tại đây
    peerConnection.onconnectionstatechange = () => {
        console.log("Connection state:", peerConnection.connectionState);
        if (peerConnection.connectionState === "connected") {
            console.log("WebRTC connection established!");
        } else if (peerConnection.connectionState === "disconnected" || peerConnection.connectionState === "failed") {
            console.warn("WebRTC connection failed or disconnected.");
        }
    };

    document.getElementById("user-2").srcObject = remoteStream;
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
        let testSocket = new WebSocket("wss://192.168.1.34:8000/ws/room/test-client");
        testSocket.onopen = () => console.log("WebSocket connected!");
        testSocket.onerror = (error) => console.error("WebSocket error:", error);
    },
    false
);
