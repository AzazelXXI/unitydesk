let createRoom = () => {
    let roomID = Math.random().toString(36).substring(2, 15);
    // window.location.href = `/room/${roomID}`
    window.open(`/room/${roomID}`, "_blank");
}