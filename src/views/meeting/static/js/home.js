let createRoom = () => {
    let roomID = Math.random().toString(36).substring(2, 15);
    // window.location.href = `/meeting/room/${roomID}`
    window.open(`/meeting/room/${roomID}`, "_blank");
};
