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
    await connect(createAndSendOffer);
}

let connect = async (callback) => {
    let roomName = decodeURIComponent(window.location.pathname.split("/")[1]);
    let clientId = Math.random().toString(36).substring(2, 15); // Tạo client_id ngẫu nhiên
    socket = new WebSocket(`ws://localhost:8000/ws/${roomName}/${clientId}`);
    socket.onopen = async (_) => {
        await callback();
    };

    socket.onmessage = handleMessage;
    console.log("Room Name:", roomName);
};

let handleMessage = async ({ data }) => {
    data = JSON.parse(data);
    if (data["type"] === "USER_JOIN") {
        polite = true;
        createAndSendOffer();
    }
    if (data["type"] === "OFFER") {
        console.log("Received offer");
        await createAndSendAnswer(data["message"]);
    }
    if (data["type"] === "ANSWER") {
        console.log("Received answer");
        await peerConnection.setRemoteDescription(data["message"]);
    }
    if (data["type"] === "candidate") {
        console.log("Received ICE candidate");
        await handleIceCandidate(data["candidate"]);
    }
};

let createAndSendAnswer = async (message) => {
    await createStreams();
    await peerConnection.setRemoteDescription(message);
    let answer = await peerConnection.createAnswer();
    await peerConnection.setLocalDescription(answer);
    socket.send(
        JSON.stringify({
            type: "ANSWER",
            message: peerConnection.localDescription,
        })
    );
};

let handleOffers = async ({ message }) => {
    await createAndSendAnswer(message);
};

let handleAnswers = async ({ message }) => {
    await peerConnection.setRemoteDescription(message);
};

let handleIceCandidate = async ({ candidate }) => {
    if (peerConnection && peerConnection.remoteDescription) {
        await peerConnection.addIceCandidate(candidate);
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
                "stun:stun1.l.google.com:19302",
                "stun:stun2.l.google.com:19302",
            ],
        },
    ],
};

let createStreams = async () => {
    peerConnection = new RTCPeerConnection(config);
    remoteStream = new MediaStream();

    localStream.getTracks().forEach((track) => {
        peerConnection.addTrack(track, localStream);
    });

    // This function is called each time a peer connects.
    peerConnection.ontrack = (event) => {
        console.log("adding track");
        event.streams[0]
            .getTracks()
            .forEach((track) => remoteStream.addTrack(track));
    };

    peerConnection.onicecandidate = async (event) => {
        if (event.candidate) {
            socket.send(
                JSON.stringify({ type: "candidate", candidate: event.candidate })
            );
        }
    };
    peerConnection.onnegotiationneeded = async () => {
        try {
            makingOffer = true;
            await peerConnection.setLocalDescription();
            // signaler.send({ description: pc.localDescription });
            socket.send(
                JSON.stringify({
                    type: "OFFER",
                    message: peerConnection.localDescription,
                })
            );
        } catch (err) {
            console.error(err);
        } finally {
            makingOffer = false;
        }
    };

    document.getElementById("user-2").srcObject = remoteStream;
};

let createAndSendOffer = async () => {
    await createStreams();
    let offer = await peerConnection.createOffer();
    await peerConnection.setLocalDescription(offer);
    socket.send(
        JSON.stringify({
            type: "OFFER",
            message: peerConnection.localDescription,
        })
    );
};

// let createAndSendAnswer = async (message) => {
//   await createStreams();
//   await peerConnection.setRemoteDescription(message);
//   let answer = await peerConnection.createAnswer();
//   await peerConnection.setLocalDescription(answer);
//   socket.send(JSON.stringify({ type: "ANSWER", message: answer }));
// };

document.addEventListener(
    "DOMContentLoaded",
    async function () {
        await init();
    },
    false
);
