<!-- filepath: d:\projects\CSA\csa-hello\.docs\modules\meeting\module_diagram_extended.md -->
# Meeting Module Extended Diagrams

## WebRTC Architecture

```mermaid
graph TD
    subgraph Client-Side
        UI["User Interface<br>Video/Audio Controls"]
        MediaAPI["Media API<br>getUserMedia"]
        PeerConn["RTCPeerConnection<br>WebRTC Connection"]
        DataChannel["RTCDataChannel<br>Chat & Controls"]
        LocalMedia["Local Media<br>Camera/Microphone"]
    end
    
    subgraph Server-Side
        SignalServer["Signaling Server<br>Connection Management"]
        RoomManager["Room Manager<br>Meeting Lifecycle"]
        Analytics["Analytics Service<br>Quality Metrics"]
        AuthService["Authentication<br>Access Control"]
    end
    
    subgraph External-Services
        STUNServers["STUN Servers<br>NAT Traversal"]
        TURNServers["TURN Servers<br>Relay Fallback"]
        RecordingService["Recording Service<br>Meeting Archives"]
    end
    
    UI --> MediaAPI
    MediaAPI --> LocalMedia
    MediaAPI --> PeerConn
    PeerConn --> DataChannel
    UI --> DataChannel
    
    PeerConn <--> SignalServer
    SignalServer --> RoomManager
    SignalServer --> AuthService
    PeerConn --> Analytics
    
    PeerConn <--> STUNServers
    PeerConn <--> TURNServers
    RoomManager --> RecordingService
```

## WebRTC Negotiation Sequence

```mermaid
sequenceDiagram
    participant Client1 as Caller
    participant Signal as Signaling Server
    participant STUN as STUN/TURN Servers
    participant Client2 as Callee
    
    Client1->>Signal: Connect to WebSocket
    Client2->>Signal: Connect to WebSocket
    
    Client1->>Client1: Get user media streams
    Client1->>STUN: ICE candidate gathering
    STUN-->>Client1: ICE candidates
    
    Client1->>Client1: Create offer
    Client1->>Client1: Set local description
    Client1->>Signal: Send offer
    Signal->>RoomManager: Log connection attempt
    Signal->>Client2: Forward offer
    
    Client2->>Client2: Get user media streams
    Client2->>STUN: ICE candidate gathering
    STUN-->>Client2: ICE candidates
    
    Client2->>Client2: Set remote description (offer)
    Client2->>Client2: Create answer
    Client2->>Client2: Set local description
    Client2->>Signal: Send answer
    Signal->>Client1: Forward answer
    
    Client1->>Client1: Set remote description (answer)
    
    loop ICE Candidate Exchange
        Client1->>Signal: Send ICE candidate
        Signal->>Client2: Forward ICE candidate
        Client2->>Client2: Add ICE candidate
        
        Client2->>Signal: Send ICE candidate
        Signal->>Client1: Forward ICE candidate
        Client1->>Client1: Add ICE candidate
    end
    
    Note over Client1,Client2: Connection established
    
    Client1->>Analytics: Report connection quality
    Client2->>Analytics: Report connection quality
```

## Meeting Room Management Flow

```mermaid
flowchart TD
    User([User])
    CreateRoom[Create Meeting Room]
    JoinRoom[Join Meeting Room]
    CheckPermissions{Has Permission?}
    ConfigRoom[Configure Room Settings]
    WaitingRoom{Use Waiting Room?}
    DirectJoin[Direct Join]
    WaitingArea[Waiting Area]
    HostApproval{Host Approves?}
    JoinMeeting[Join Active Meeting]
    RecordOption{Record Meeting?}
    StartRecording[Start Recording]
    EndMeeting[End Meeting]
    SaveRecording[Save Recording]
    
    User --> CreateRoom
    User --> JoinRoom
    
    CreateRoom --> ConfigRoom
    ConfigRoom --> WaitingRoom
    
    JoinRoom --> CheckPermissions
    CheckPermissions -->|Yes| WaitingRoom
    CheckPermissions -->|No| Rejected[Access Denied]
    
    WaitingRoom -->|Yes| WaitingArea
    WaitingRoom -->|No| DirectJoin
    
    WaitingArea --> HostApproval
    HostApproval -->|Yes| JoinMeeting
    HostApproval -->|No| Rejected
    
    DirectJoin --> JoinMeeting
    
    JoinMeeting --> RecordOption
    RecordOption -->|Yes| StartRecording
    RecordOption -->|No| Meeting[Active Meeting]
    StartRecording --> Meeting
    
    Meeting --> EndMeeting
    StartRecording --> SaveRecording
    SaveRecording --> MeetingEnded[Meeting Archived]
    EndMeeting --> MeetingEnded
    
    classDef user fill:#d4f1f9,stroke:#05a4d2
    classDef action fill:#c9e7dd,stroke:#0ca789
    classDef decision fill:#ffe6cc,stroke:#ff9933
    classDef denied fill:#f9d1d1,stroke:#e06666
    classDef meeting fill:#e6e6fa,stroke:#8a2be2
    
    class User user
    class CreateRoom,JoinRoom,ConfigRoom,StartRecording,EndMeeting,SaveRecording action
    class CheckPermissions,WaitingRoom,HostApproval,RecordOption decision
    class Rejected denied
    class DirectJoin,WaitingArea,JoinMeeting,Meeting,MeetingEnded meeting
```

## Connection State Diagram

```mermaid
stateDiagram-v2
    [*] --> Initialize: User joins meeting
    
    Initialize --> MediaAccess: Request camera/mic
    MediaAccess --> SignalingConnected: Connect to signaling
    
    SignalingConnected --> ICEGathering: Start ICE gathering
    ICEGathering --> Connecting: Exchange SDP
    
    Connecting --> Connected: ICE success
    Connecting --> Reconnecting: ICE failure
    
    Connected --> Reconnecting: Connection lost
    Reconnecting --> Connected: Connection restored
    Reconnecting --> Failed: Max retries exceeded
    
    Connected --> Disconnected: User leaves
    Failed --> Disconnected: Session abandoned
    
    Disconnected --> [*]
    
    state Connecting {
        [*] --> ICEChecking
        ICEChecking --> ICEConnected: Connected
        ICEChecking --> ICEFailed: Failed
    }
    
    state Connected {
        [*] --> Stable
        Stable --> MediaReceiving: Remote streams received
        MediaReceiving --> QualityMonitoring: Analyze quality
        QualityMonitoring --> Stable: Quality checks
    }
```
