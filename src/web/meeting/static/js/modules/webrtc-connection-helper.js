/**
 * WebRTC Connection Helper
 * Cải thiện kết nối WebRTC giữa các mạng khác nhau
 */

import { logger } from './logger.js';
import { state } from './state.js';
import { sendToServer } from './signaling.js';
import { getRTCConfig } from './config.js';

/**
 * Buộc sử dụng TURN Server để tạo kết nối relay
 * @param {RTCPeerConnection} pc - Kết nối cần cập nhật
 * @param {string} remoteClientId - ID của người dùng đầu bên kia
 */
export const forceTurnUsage = async (pc, remoteClientId) => {
    // Đánh dấu đã kích hoạt chế độ TURN
    state.forcedTurnUsage = true;
    
    try {
        // Lưu số lần thất bại để dùng relay cho lần sau
        const failCount = parseInt(localStorage.getItem('rtc_connection_failures') || '0');
        localStorage.setItem('rtc_connection_failures', (failCount + 1).toString());
        
        // Cập nhật cấu hình để sử dụng chỉ TURN
        const currentConfig = pc.getConfiguration();
        logger.info(`Kích hoạt chế độ TURN-only để cải thiện kết nối với ${remoteClientId}`);
        
        pc.setConfiguration({
            ...currentConfig,
            iceTransportPolicy: 'relay'
        });
        
        // Khởi động lại ICE để bắt đầu thu thập các candidates mới
        pc.restartIce();
        
        // Thông báo cho bên kia rằng chúng ta đang thử lại với TURN
        sendToServer({
            type: "ICE_RESTART",
            target: remoteClientId,
            forceRelay: true
        });
        
        return true;
    } catch (err) {
        logger.error(`Không thể kích hoạt chế độ TURN: ${err.message}`);
        return false;
    }
};

/**
 * Theo dõi việc thu thập ICE candidates
 * @param {RTCPeerConnection} pc - Kết nối WebRTC
 * @param {string} remoteClientId - ID của người dùng đầu bên kia
 */
export const monitorIceCandidates = (pc, remoteClientId) => {
    // Đặt timeout để kiểm tra nếu không có relay candidates sau một khoảng thời gian
    if (!state.turnCheckTimeout) {
        state.turnCheckTimeout = setTimeout(async () => {
            // Nếu chưa nhận được relay candidate sau 3 giây (giảm xuống từ 5s để phản ứng nhanh hơn)
            if (!state.hasSentRelayCandidate) {
                logger.warn(`Không tìm thấy RELAY candidates cho ${remoteClientId}, đang buộc sử dụng TURN`);
                await forceTurnUsage(pc, remoteClientId);
            }
        }, 3000);
    }
    
    // Kiểm tra trạng thái kết nối sớm hơn - sau 5 giây
    setTimeout(() => {
        if (pc.connectionState !== 'connected' && pc.iceConnectionState !== 'connected') {
            logger.warn(`Kết nối với ${remoteClientId} chưa thành công sau 5 giây, đang thử dùng TURN server khác`);
            
            // Thử sử dụng máy chủ TURN khác
            rotateToNextTurnServer(pc, remoteClientId);
        }
    }, 5000);
    
    // Kiểm tra lại sau 15 giây nếu vẫn không có kết nối - áp dụng biện pháp khẩn cấp
    setTimeout(() => {
        if (pc.connectionState !== 'connected' && pc.iceConnectionState !== 'connected') {
            logger.error(`Kết nối với ${remoteClientId} vẫn thất bại sau 15 giây, áp dụng biện pháp khẩn cấp`);
            
            // Giải pháp khẩn cấp: Buộc sử dụng chỉ một TURN server đáng tin cậy nhất
            emergencyTurnConnection(pc, remoteClientId);
            
            // Tăng số lần thất bại để lần sau tự động dùng chế độ khẩn cấp
            const failCount = parseInt(localStorage.getItem('rtc_connection_failures') || '0');
            localStorage.setItem('rtc_connection_failures', (failCount + 2).toString());
        }
    }, 15000);
};

/**
 * Thay đổi sang máy chủ TURN khác nếu không kết nối được
 * @param {RTCPeerConnection} pc - Kết nối WebRTC
 * @param {string} remoteClientId - ID của người dùng đầu bên kia
 */
export const rotateToNextTurnServer = async (pc, remoteClientId) => {
    try {
        if (!state.currentTurnServerIndex) {
            state.currentTurnServerIndex = 0;
        }
        
        // Lấy cấu hình ICE servers từ config
        const config = getRTCConfig();
        const turnServers = config.iceServers.filter(server => {
            const urls = Array.isArray(server.urls) ? server.urls : [server.urls];
            return urls.some(url => url.startsWith('turn:') || url.startsWith('turns:'));
        });
        
        if (turnServers.length === 0) {
            logger.error('Không tìm thấy TURN servers để sử dụng');
            return false;
        }
        
        // Chuyển sang server tiếp theo
        state.currentTurnServerIndex = (state.currentTurnServerIndex + 1) % turnServers.length;
        const selectedTurnServer = turnServers[state.currentTurnServerIndex];
        
        logger.info(`Đang thử với TURN server khác: ${Array.isArray(selectedTurnServer.urls) 
            ? selectedTurnServer.urls[0] 
            : selectedTurnServer.urls}`);
        
        // Cập nhật cấu hình với TURN server mới
        const currentConfig = pc.getConfiguration();
        pc.setConfiguration({
            ...currentConfig,
            iceServers: [selectedTurnServer],
            iceTransportPolicy: 'relay'
        });
        
        // Khởi động lại quá trình ICE
        pc.restartIce();
        
        return true;
    } catch (err) {
        logger.error(`Lỗi khi thay đổi TURN server: ${err.message}`);
        return false;
    }
};

/**
 * Giải pháp kết nối khẩn cấp - sử dụng một TURN server đã được xác nhận hoạt động tốt
 * @param {RTCPeerConnection} pc - Kết nối WebRTC
 * @param {string} remoteClientId - ID của người dùng đầu bên kia
 */
export const emergencyTurnConnection = async (pc, remoteClientId) => {
    try {
        logger.warn(`🚨 Kích hoạt kết nối khẩn cấp với ${remoteClientId}`);
        
        // Sử dụng các TURN server đáng tin cậy nhất cho kết nối khẩn cấp
        const emergencyTurnServers = [
            {
                urls: [
                    'turn:numb.viagenie.ca:3478?transport=udp',
                    'turn:numb.viagenie.ca:3478?transport=tcp',
                ],
                username: 'vietnam.webrtc@gmail.com',
                credential: 'muadong2022'
            },
            {
                urls: [
                    'turn:sandbox-turn.stunserver.com:3478',
                ],
                username: 'guest',
                credential: 'guest'
            }
        ];
        
        // Cập nhật cấu hình để chỉ sử dụng các TURN server khẩn cấp
        pc.setConfiguration({
            iceServers: emergencyTurnServers,
            iceTransportPolicy: 'relay',   // Chỉ dùng relay candidates
            bundlePolicy: 'max-bundle',
            rtcpMuxPolicy: 'require',
            iceCandidatePoolSize: 1       // Giảm xuống để tập trung vào các candidates tốt nhất
        });
        
        // Thông báo cho bên kia
        sendToServer({
            type: "EMERGENCY_RELAY",
            target: remoteClientId
        });
        
        // Buộc khởi động lại quá trình ICE
        pc.restartIce();
        
        // Nếu kết nối vẫn ở trạng thái failed, thử tạo offer mới
        if (pc.connectionState === 'failed') {
            const offer = await pc.createOffer({iceRestart: true});
            await pc.setLocalDescription(offer);
            
            // Gửi offer mới tới người dùng bên kia
            sendToServer({
                type: "OFFER",
                offer: pc.localDescription,
                target: remoteClientId,
                forceRelay: true
            });
        }
        
        return true;
    } catch (err) {
        logger.error(`Không thể kích hoạt kết nối khẩn cấp: ${err.message}`);
        return false;
    }
};

/**
 * Áp dụng giải pháp khắc phục mạng di động (3G/4G) - các nhà mạng thường sử dụng NAT nghiêm ngặt
 * @param {RTCPeerConnection} pc - Kết nối WebRTC 
 * @param {string} remoteClientId - ID của người dùng đầu bên kia
 */
export const mobileCellularFix = async (pc, remoteClientId) => {
    try {
        // Phát hiện kết nối di động dựa trên connection, navigator.connection không khả dụng trên mọi trình duyệt
        const isMobileNetwork = navigator.connection ? 
            (navigator.connection.type === 'cellular' || navigator.connection.effectiveType === '3g' || navigator.connection.effectiveType === '4g') : 
            (window.navigator.userAgent.includes('Mobile') || window.navigator.userAgent.includes('Android'));
        
        if (isMobileNetwork) {
            logger.info(`Phát hiện kết nối di động cho ${remoteClientId}, áp dụng cấu hình đặc biệt`);
            
            // Tăng kết nối TCP cho mạng di động (nhiều nhà mạng chặn UDP)
            const mobileTurnServers = [
                {
                    urls: [
                        'turn:numb.viagenie.ca:3478?transport=tcp',
                        'turns:numb.viagenie.ca:443' // Sử dụng TURNS qua SSL để tránh các tường lửa
                    ],
                    username: 'vietnam.webrtc@gmail.com',
                    credential: 'muadong2022'
                }
            ];
            
            // Cập nhật cấu hình
            const currentConfig = pc.getConfiguration();
            pc.setConfiguration({
                ...currentConfig,
                iceServers: [...currentConfig.iceServers, ...mobileTurnServers],
                iceTransportPolicy: 'relay'
            });
            
            return true;
        }
        
        return false;
    } catch (err) {
        logger.error(`Lỗi khi áp dụng giải pháp cho mạng di động: ${err.message}`);
        return false;
    }
};

/**
 * Tối ưu hóa SDP cho kết nối xuyên mạng
 * @param {string} sdp - SDP offer/answer ban đầu
 * @returns {string} SDP đã được tối ưu hóa
 */
export const optimizeSdp = (sdp) => {
    try {
        // Ưu tiên IPv4 hơn IPv6
        sdp = sdp.replace(/a=candidate:.*foundation .*network-id.*\r\n/g, (match) => {
            if (match.includes(" udp ") && !match.includes("network-cost")) {
                return match + "a=candidate:";
            }
            return match;
        });
        
        // Đặt ưu tiên cao hơn cho các ứng viên relay
        sdp = sdp.replace(/a=candidate:.*relay.*typ relay.*\r\n/g, (match) => {
            // Tăng độ ưu tiên cho các relay candidates
            const parts = match.split(' ');
            if (parts.length > 5) {
                // Thay đổi giá trị ưu tiên (thường ở vị trí thứ 4)
                parts[3] = '2130706431'; // Giá trị ưu tiên cao nhất
                return parts.join(' ') + '\r\n';
            }
            return match;
        });
        
        // Thêm các tham số ICE mới giúp kết nối qua NAT nghiêm ngặt
        if (!sdp.includes('a=ice-options:trickle')) {
            sdp = sdp.replace(/(a=ice-pwd:[^\r\n]*\r\n)/g, '$1a=ice-options:trickle\r\n');
        }
        
        // Tối ưu hóa codec và giảm băng thông khi cần
        sdp = sdp.replace(/(a=rtpmap:\d+ H264\/90000\r\n)/g, 
            '$1a=fmtp:96 level-asymmetry-allowed=1;packetization-mode=1;profile-level-id=42e01f\r\n');
        
        return sdp;
    } catch (e) {
        logger.error(`Lỗi khi tối ưu hóa SDP: ${e.message}`);
        return sdp; // Trả về SDP gốc nếu có lỗi
    }
};
