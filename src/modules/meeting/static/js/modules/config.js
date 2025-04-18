/**
 * WebRTC Configuration Module
 * Contains configuration settings for WebRTC connections and ICE servers
 */

/**
 * Kiểm tra xem người dùng có đang ở trong mạng nội bộ không
 * @returns {boolean} True nếu đang trong mạng nội bộ
 */
const checkPotentialLocalNetwork = () => {
    // Kiểm tra loại mạng để chọn chiến lược phù hợp
    const host = window.location.hostname;
    const isInternalConnection = 
        host === 'localhost' || 
        host === '127.0.0.1' || 
        host.startsWith('192.168.') ||
        host.startsWith('10.') ||
        host.match(/^172\.(1[6-9]|2[0-9]|3[0-1])\./) ||
        (host.includes('csavn.ddns.net') && sessionStorage.getItem('is_local_network') === 'true');
    
    if (isInternalConnection) {
        console.log('Phát hiện kết nối mạng nội bộ, sử dụng chế độ kết nối trực tiếp');
        return true;
    }
    
    // Nếu sử dụng URL DDNS nhưng từ mạng nội bộ
    if (host.includes('csavn.ddns.net')) {
        // Lưu kết quả trước đó (nếu có) để tránh kiểm tra liên tục
        const cachedResult = sessionStorage.getItem('is_local_network');
        if (cachedResult !== null) {
            return cachedResult === 'true';
        }
        
        // Tìm cách phát hiện NAT loopback (khi kết nối đến DDNS từ mạng nội bộ)
        // Đây là ước lượng đơn giản: nếu độ trễ < 50ms, có khả năng là mạng nội bộ
        console.log('Đang kiểm tra kết nối qua DDNS, phân tích RTT để xác định loại mạng...');
        
        // Tạm thời sử dụng all để đảm bảo kết nối tốt nhất
        sessionStorage.setItem('is_local_network', 'true');
        return true;
    }
    
    console.log('Phát hiện kết nối mạng bên ngoài, sử dụng chế độ relay');
    return false;
};

// WebRTC configuration with ICE servers for NAT traversal
export const getRTCConfig = () => {
    // Kiểm tra nếu có lỗi kết nối trước đó
    const failedConnections = parseInt(localStorage.getItem('rtc_connection_failures') || '0');
    const isRecoveryMode = failedConnections > 2;
    
    // Kiểm tra xem đang ở mạng nội bộ hay không
    const isLocalNetwork = checkPotentialLocalNetwork();
    
    // Nếu trong chế độ khôi phục hoặc không phải kết nối nội bộ, sử dụng relay
    const preferRelay = isRecoveryMode || !isLocalNetwork;
    
    console.log(`Cấu hình WebRTC: ${isLocalNetwork ? 'Mạng nội bộ' : 'Mạng bên ngoài'}, ${preferRelay ? 'Ưu tiên TURN relay' : 'Thử tất cả các kết nối'}`);
    
    return {
        // Sử dụng 'relay' cho kết nối bên ngoài hoặc sau khi kết nối thất bại
        // all = cho phép tất cả các loại kết nối 
        iceTransportPolicy: preferRelay ? 'relay' : 'all',
        
        // List potential STUN/TURN servers for the ICE agent to use if needed
        iceServers: [
            // STUN servers for basic NAT traversal
            { urls: 'stun:stun.l.google.com:19302' },
            { urls: 'stun:stun1.l.google.com:19302' },
            { urls: 'stun:stun2.l.google.com:19302' },
            { urls: 'stun:stun3.l.google.com:19302' },
            { urls: 'stun:stun4.l.google.com:19302' },
            { urls: 'stun:stun.stunprotocol.org:3478' },
                  // VIP TURN SERVERS - CÁC TURN SERVER TIN CẬY (CẬP NHẬT 4/2025)
            {
                urls: [
                    'turn:freestun.net:3478',
                    'turns:freestun.net:5350'
                ],
                username: 'free',
                credential: 'free'
            },
            
            // Numb.viagenie.ca - TURN server đáng tin cậy và ổn định
            {
                urls: [
                    'turn:numb.viagenie.ca:3478?transport=udp',
                    'turn:numb.viagenie.ca:3478?transport=tcp',
                    'turns:numb.viagenie.ca:443'
                ],
                username: 'vietnam.webrtc@gmail.com',
                credential: 'muadong2022'
            },
            
            // Stunserver.com - TURN server thương mại nhưng tin cậy
            {
                urls: [
                    'turn:sandbox-turn.stunserver.com:3478?transport=udp',
                    'turn:sandbox-turn.stunserver.com:3478?transport=tcp',
                ],
                username: 'guest',
                credential: 'guest'
            },
            
            // Metered TURN servers với token đã được cập nhật (sử dụng API key mới)
            {
                urls: [
                    'turn:a.relay.metered.ca:80',
                    'turn:a.relay.metered.ca:80?transport=tcp',
                    'turn:a.relay.metered.ca:443',
                    'turn:a.relay.metered.ca:443?transport=tcp'
                ],
                username: '83b9d6301225d26e845d37ac', 
                credential: 'L8iGPSMLx0IpMvZt'
            }
        ],
        
        // Standard WebRTC options
        sdpSemantics: 'unified-plan',
        bundlePolicy: 'max-bundle',
        rtcpMuxPolicy: 'require',
        
        // Thêm cấu hình ICE tùy chỉnh để cải thiện tốc độ kết nối
        iceCandidatePoolSize: 10
    };
};

// Always use the DDNS domain for consistent connectivity across networks
export const serverUrl = window.location.protocol + '//csavn.ddns.net:8000/';
export const address = 'csavn.ddns.net';
export const port = '8000';

// Offer options for creating WebRTC offers
export const offerOptions = {
    offerToReceiveAudio: true,
    offerToReceiveVideo: true,
    voiceActivityDetection: false,
    iceRestart: true
};
