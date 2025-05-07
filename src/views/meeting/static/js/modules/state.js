/**
 * State Module
 * Manages global state shared across modules
 */

export const state = {
    // Stream management
    localStream: null,
    
    // Connection management
    peerConnections: {},  // Store multiple peer connections
    socket: null,
    clientId: null,
    
    // Media state tracking
    remoteAudioEnabled: {}, // Track the audio state of each remote peer
};

/**
 * Updates the state with new values
 * @param {Object} newState - New state values to merge
 */
export const updateState = (newState) => {
    Object.assign(state, newState);
};
