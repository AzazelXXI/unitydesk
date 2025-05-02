/**
 * Signaling Module
 * Handles WebSocket connections and message sending/receiving
 */

import { state, updateState } from "./state.js";
import { createPeerConnection, removeRemoteStream } from "./webrtc.js";
import { offerOptions } from "./config.js";
import { logger } from "./logger.js";

/**
 * Establishes WebSocket connection to the signaling server
 */
export const connect = async () => {
    let roomName = window.location.pathname.split("/").pop();
    const clientId = Math.random().toString(36).substring(2, 15); // Generate random client ID

    // Store clientId in global state
    updateState({ clientId });
    // Build WebSocket URL relative to the current page
    // This ensures it works regardless of how users access the site
    const wsProtocol = window.location.protocol === "https:" ? "wss:" : "ws:";
    // Use relative path approach to avoid hostname/port issues
    const wsUrl = `${wsProtocol}//${window.location.host}/meeting/ws/${roomName}/${clientId}`;
    logger.info("Connecting to WebSocket at:", wsUrl);

    const socket = new WebSocket(wsUrl);

    socket.onopen = () => {
        logger.info("WebSocket connected!");
        // Announce this user to the room
        sendToServer({
            type: "JOIN",
            clientId: clientId,
        });
    };

    socket.onerror = (error) => {
        logger.error("WebSocket error:", error);
    };

    socket.onmessage = handleMessage;
    // Store socket in global state
    updateState({ socket });

    logger.info("Room Name:", roomName);
    logger.info("Client ID:", clientId);
};

/**
 * Sends a message to the signaling server
 * @param {Object} message - The message to send
 */
export const sendToServer = (message) => {
    if (state.socket && state.socket.readyState === WebSocket.OPEN) {
        state.socket.send(JSON.stringify(message));
    } else {
        console.error("Cannot send message, WebSocket is not open");
    }
};

/**
 * Handles incoming WebSocket messages
 * @param {MessageEvent} event - The message event
 */
const handleMessage = async ({ data }) => {
    try {
        data = JSON.parse(data);
        logger.debug("Received message:", data);

        switch (data.type) {
            case "JOIN":
                if (data.clientId !== state.clientId) {
                    logger.info(
                        `New user joined: ${data.clientId}. Creating peer connection...`
                    );
                    // Create new peer connection for new user
                    state.peerConnections[data.clientId] = createPeerConnection(
                        data.clientId
                    );

                    // Use a timeout to ensure ICE gathering has started before creating offer
                    setTimeout(async () => {
                        try {
                            // Use trickle ICE approach (sending candidates as they arrive)
                            const pc = state.peerConnections[data.clientId];

                            // Set up a collector for early ICE candidates
                            const iceCandidatesCache = [];
                            const originalOnIceCandidate = pc.onicecandidate;
                            pc.onicecandidate = (event) => {
                                if (event.candidate) {
                                    iceCandidatesCache.push(event.candidate);
                                }
                                // Still call original handler
                                if (originalOnIceCandidate)
                                    originalOnIceCandidate(event);
                            };
                            const offer = await pc.createOffer(offerOptions);
                            await pc.setLocalDescription(offer);

                            // Wait briefly to allow some ICE candidates to be gathered
                            logger.debug(
                                "Waiting for ICE candidates before sending offer..."
                            );
                            await new Promise((resolve) =>
                                setTimeout(resolve, 2000)
                            );

                            // Send the offer with any collected candidates
                            sendToServer({
                                type: "OFFER",
                                offer: state.peerConnections[data.clientId]
                                    .localDescription,
                                target: data.clientId,
                            });
                            logger.info(`Offer sent to ${data.clientId}`);
                        } catch (err) {
                            logger.error("Error creating/sending offer:", err);
                        }
                    }, 500);
                }
                break;

            case "OFFER":
                try {
                    logger.info(`Received offer from ${data.source}`);
                    if (!state.peerConnections[data.source]) {
                        logger.info(
                            `Creating peer connection for ${data.source}`
                        );
                        state.peerConnections[data.source] =
                            createPeerConnection(data.source);
                    }
                    await state.peerConnections[
                        data.source
                    ].setRemoteDescription(data.offer);
                    const answer = await state.peerConnections[
                        data.source
                    ].createAnswer();
                    await state.peerConnections[
                        data.source
                    ].setLocalDescription(answer);
                    sendToServer({
                        type: "ANSWER",
                        answer: answer,
                        target: data.source,
                    });
                } catch (err) {
                    logger.error("Error handling offer:", err);
                }
                break;

            case "ANSWER":
                if (state.peerConnections[data.source]) {
                    try {
                        const pc = state.peerConnections[data.source];
                        // Only set remote description if we're in the right state
                        // (have local description and waiting for answer)
                        if (pc.signalingState === "have-local-offer") {
                            await pc.setRemoteDescription(data.answer);
                            logger.info(
                                `Successfully set remote answer from ${data.source}`
                            );
                        } else {
                            logger.warn(
                                `Ignoring answer from ${data.source}: peer connection is in ${pc.signalingState} state, expected 'have-local-offer'`
                            );
                        }
                    } catch (err) {
                        console.error(
                            `Error setting remote answer from ${data.source}:`,
                            err
                        );
                    }
                }
                break;

            case "CANDIDATE":
                if (state.peerConnections[data.source]) {
                    await state.peerConnections[data.source].addIceCandidate(
                        data.candidate
                    );
                }
                break;
            case "ICE_RESTART":
                if (state.peerConnections[data.source]) {
                    try {
                        logger.info(
                            `Attempting ICE restart with ${data.source}`
                        );
                        const offer = await state.peerConnections[
                            data.source
                        ].createOffer({
                            offerToReceiveAudio: true,
                            offerToReceiveVideo: true,
                            iceRestart: true,
                        });
                        await state.peerConnections[
                            data.source
                        ].setLocalDescription(offer);
                        sendToServer({
                            type: "OFFER",
                            offer: offer,
                            target: data.source,
                            isIceRestart: true,
                        });
                    } catch (err) {
                        logger.error("Error during ICE restart:", err);
                    }
                }
                break;

            case "LEAVE":
                removeRemoteStream(data.clientId);
                break;
            case "AUDIO_TOGGLE":
                // Handle remote user's audio state change
                logger.info(
                    `Remote user ${data.source} ${
                        data.enabled ? "unmuted" : "muted"
                    } their microphone`
                );
                // Update UI to show mute status
                import("./ui.js").then(({ updateMediaStatus }) => {
                    updateMediaStatus(data.source, "audio", data.enabled);
                });
                break;

            case "VIDEO_TOGGLE":
                // Handle remote user's video state change
                logger.info(
                    `Remote user ${data.source} ${
                        data.enabled ? "turned on" : "turned off"
                    } their camera`
                );
                // Update UI to show camera status
                import("./ui.js").then(({ updateMediaStatus }) => {
                    updateMediaStatus(data.source, "video", data.enabled);
                });
                break;

            case "CHAT_MESSAGE":
                // This will be handled by the chat module
                window.dispatchEvent(
                    new CustomEvent("chat-message", {
                        detail: {
                            sender: `User ${data.source.substring(0, 5)}...`,
                            text: data.message,
                        },
                    })
                );
                break;
        }
    } catch (err) {
        console.error("Error handling message:", err);
    }
};
