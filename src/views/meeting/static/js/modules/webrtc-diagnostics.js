/**
 * Tiện ích kiểm tra kết nối WebRTC
 * Giúp phát hiện và khắc phục vấn đề kết nối
 */

import { state } from './state.js';
import { logger } from './logger.js';

/**
 * Kiểm tra kết nối với máy chủ TURN
 * @param {Array} iceServers - Danh sách các máy chủ ICE để kiểm tra
 * @returns {Promise<Object>} Kết quả kiểm tra
 */
export const testTurnConnection = async (iceServers) => {
    return new Promise((resolve, reject) => {
        logger.info("Đang kiểm tra kết nối đến TURN servers...");
        
        const config = {
            iceServers,
            iceTransportPolicy: 'relay',
            iceCandidatePoolSize: 1
        };
        
        try {
            // Tạo kết nối kiểm tra
            const pc1 = new RTCPeerConnection(config);
            const pc2 = new RTCPeerConnection(config);
            
            // Biến để theo dõi kết quả
            const results = {
                success: false,
                relayCandidates: 0,
                elapsedTime: 0
            };
            
            const startTime = Date.now();
            const timeout = setTimeout(() => {
                cleanup();
                results.timedOut = true;
                resolve(results);
            }, 10000); // 10 giây timeout
            
            // Hàm dọn dẹp
            const cleanup = () => {
                clearTimeout(timeout);
                pc1.close();
                pc2.close();
                results.elapsedTime = Date.now() - startTime;
            };
            
            // Khi nhận được ICE candidate
            pc1.onicecandidate = (e) => {
                if (e.candidate) {
                    if (e.candidate.type === 'relay') {
                        results.relayCandidates++;
                    }
                    pc2.addIceCandidate(e.candidate);
                }
            };
            
            pc2.onicecandidate = (e) => {
                if (e.candidate) {
                    pc1.addIceCandidate(e.candidate);
                }
            };
            
            // Khi kết nối ICE thay đổi
            pc1.oniceconnectionstatechange = () => {
                if (pc1.iceConnectionState === 'connected' || pc1.iceConnectionState === 'completed') {
                    logger.info(`✅ Kết nối TURN thành công sau ${Date.now() - startTime}ms`);
                    results.success = true;
                    cleanup();
                    resolve(results);
                } else if (pc1.iceConnectionState === 'failed') {
                    logger.warn("❌ Kết nối TURN thất bại");
                    cleanup();
                    resolve(results);
                }
            };
            
            // Tạo kênh dữ liệu để kích hoạt quá trình ICE
            const dc = pc1.createDataChannel("testChannel");
            
            // Bắt đầu quá trình kết nối
            pc1.createOffer()
                .then(offer => pc1.setLocalDescription(offer))
                .then(() => pc2.setRemoteDescription(pc1.localDescription))
                .then(() => pc2.createAnswer())
                .then(answer => pc2.setLocalDescription(answer))
                .then(() => pc1.setRemoteDescription(pc2.localDescription))
                .catch(err => {
                    logger.error("Lỗi kiểm tra kết nối TURN:", err);
                    cleanup();
                    reject(err);
                });
        } catch (err) {
            logger.error("Không thể khởi tạo kết nối kiểm tra:", err);
            reject(err);
        }
    });
};

/**
 * Kiểm tra xem máy chủ TURN có hoạt động không
 * @param {Object} turnServer - Thông tin máy chủ TURN cần kiểm tra
 * @returns {Promise<boolean>} Kết quả kiểm tra
 */
export const testSingleTurnServer = async (turnServer) => {
    return testTurnConnection([turnServer])
        .then(result => {
            if (result.success) {
                logger.info(`Máy chủ TURN ${turnServer.urls[0]} hoạt động tốt!`);
                return true;
            } else {
                logger.warn(`Máy chủ TURN ${turnServer.urls[0]} không phản hồi hoặc không hoạt động.`);
                return false;
            }
        })
        .catch(() => {
            logger.warn(`Không thể kết nối đến máy chủ TURN ${turnServer.urls[0]}`);
            return false;
        });
};

/**
 * Ghi lại thông tin về kết nối để giúp gỡ lỗi
 * @param {RTCPeerConnection} pc - Kết nối WebRTC cần kiểm tra
 */
export const logConnectionStats = async (pc) => {
    if (!pc) return;
    
    try {
        const stats = await pc.getStats();
        let connectionInfo = {
            candidates: {
                local: { host: 0, srflx: 0, relay: 0 },
                remote: { host: 0, srflx: 0, relay: 0 }
            },
            selected: null,
            networkType: 'unknown',
            roundTripTime: null,
            bandwidth: null
        };
        
        stats.forEach(report => {
            // Thông tin về ICE candidate
            if (report.type === 'local-candidate') {
                connectionInfo.candidates.local[report.candidateType] = 
                    (connectionInfo.candidates.local[report.candidateType] || 0) + 1;
                
                if (report.networkType) {
                    connectionInfo.networkType = report.networkType;
                }
                
                // Lưu lại candidate được chọn
                if (report.selected) {
                    connectionInfo.selected = {
                        type: report.candidateType,
                        protocol: report.protocol,
                        address: report.address,
                        port: report.port
                    };
                }
            } 
            
            // Thông tin về roundtrip time
            if (report.type === 'candidate-pair' && report.selected) {
                connectionInfo.roundTripTime = report.currentRoundTripTime;
                connectionInfo.bytesReceived = report.bytesReceived;
                connectionInfo.bytesSent = report.bytesSent;
            }
        });
        
        logger.info("📊 Thông tin kết nối WebRTC:", connectionInfo);
        
        // Lưu thông tin để sử dụng sau này
        state.connectionStats = connectionInfo;
        
        return connectionInfo;
    } catch (err) {
        logger.error("Không thể lấy thông tin kết nối:", err);
    }
};
