<!-- filepath: d:\projects\CSA\csa-hello\.docs\modules\messenger\module_diagram.md -->
# Messenger Module Diagrams

## Component Architecture

```mermaid
graph TD
    subgraph Frontend
        ChatUI["Chat UI<br>Messaging Interface"]
        ThreadUI["Thread UI<br>Message Threading"]
        MediaUI["Media UI<br>File/Media Handling"]
        PresenceUI["Presence UI<br>Online Status Indicators"]
    end
    
    subgraph Backend
        ChatController["ChatController<br>Core Messaging Logic"]
        MessageService["MessageService<br>Message Operations"]
        NotifService["NotificationService<br>Alert Delivery"]
        PresenceService["PresenceService<br>Online Status Tracking"]
    end
    
    subgraph Database
        ChatDB[(Chats)]
        MessageDB[(Messages)]
        MemberDB[(ChatMembers)]
        ReactionDB[(MessageReactions)]
    end
    
    subgraph WebSockets
        WSServer["WebSocket Server<br>Real-time Communication"]
        WSConnection["WebSocket Connections<br>Client Connection Pool"]
        EventBus["Event Bus<br>Message Broadcasting"]
    end
    
    ChatUI --> ChatController
    ThreadUI --> MessageService
    MediaUI --> MessageService
    PresenceUI --> PresenceService
    
    ChatController --> ChatDB
    MessageService --> MessageDB
    ChatController --> MemberDB
    MessageService --> ReactionDB
    
    ChatController --> WSServer
    MessageService --> EventBus
    PresenceService --> EventBus
    
    WSServer --> WSConnection
    WSConnection --> EventBus
    
    subgraph ExternalSystems
        Storage["Storage Module<br>File Storage"]
        NotificationSystem["Notification System<br>Push Notifications"]
        UserService["User Module<br>User Information"]
    end
    
    MessageService --> Storage
    NotifService --> NotificationSystem
    PresenceService --> UserService
```

## Chat Message Sequence

```mermaid
sequenceDiagram
    participant Sender as Sender
    participant SenderUI as Sender UI
    participant WSServer as WebSocket Server
    participant MsgService as Message Service
    participant DB as Database
    participant ReceiverUI as Receiver UI
    participant Receiver as Receiver
    
    Sender->>SenderUI: Type message
    SenderUI->>SenderUI: Show typing indicator
    SenderUI->>WSServer: Send typing event
    WSServer->>ReceiverUI: Broadcast typing indicator
    ReceiverUI->>Receiver: Show "User is typing..."
    
    Sender->>SenderUI: Send message
    SenderUI->>WSServer: Send message event
    WSServer->>MsgService: Process message
    MsgService->>DB: Store message
    DB-->>MsgService: Message stored
    
    MsgService->>WSServer: Message ready to broadcast
    WSServer->>ReceiverUI: Deliver message
    ReceiverUI->>Receiver: Display message
    
    ReceiverUI->>WSServer: Send read receipt
    WSServer->>MsgService: Process read receipt
    MsgService->>DB: Store read receipt
    WSServer->>SenderUI: Deliver read receipt
    SenderUI->>Sender: Show "Read" status
    
    Receiver->>ReceiverUI: Add reaction
    ReceiverUI->>WSServer: Send reaction event
    WSServer->>MsgService: Process reaction
    MsgService->>DB: Store reaction
    WSServer->>SenderUI: Deliver reaction update
    SenderUI->>Sender: Show reaction
```

## Chat Types Flow Diagram

```mermaid
flowchart TD
    Start([User Initiates Chat])
    ChatType{Chat Type?}
    
    subgraph DirectChat [Direct Chat Process]
        SelectUser[Select User]
        CheckHistory{Existing Chat?}
        LoadChat[Load Existing Chat]
        CreateDirect[Create Direct Chat]
    end
    
    subgraph GroupChat [Group Chat Process]
        SelectUsers[Select Multiple Users]
        NameGroup[Name Group Chat]
        CreateGroup[Create Group]
        AddMembers[Add Members]
    end
    
    subgraph ChannelChat [Channel Process]
        CreateChannel[Create Channel]
        SetPermissions[Set Access Permissions]
        AddDescription[Add Description]
        InviteMembers[Invite Members]
    end
    
    Start --> ChatType
    ChatType -->|Direct| SelectUser
    ChatType -->|Group| SelectUsers
    ChatType -->|Channel| CreateChannel
    
    SelectUser --> CheckHistory
    CheckHistory -->|Yes| LoadChat
    CheckHistory -->|No| CreateDirect
    CreateDirect --> Chat[Active Chat]
    LoadChat --> Chat
    
    SelectUsers --> NameGroup
    NameGroup --> CreateGroup
    CreateGroup --> AddMembers
    AddMembers --> Chat
    
    CreateChannel --> SetPermissions
    SetPermissions --> AddDescription
    AddDescription --> InviteMembers
    InviteMembers --> Chat
    
    Chat --> Send[Send Messages]
    Send --> Receive[Receive Messages]
    
    classDef start fill:#d4f1f9,stroke:#05a4d2
    classDef process fill:#c9e7dd,stroke:#0ca789
    classDef decision fill:#ffe6cc,stroke:#ff9933
    classDef chat fill:#e6e6fa,stroke:#8a2be2
    
    class Start start
    class SelectUser,SelectUsers,NameGroup,CreateGroup,AddMembers,CreateChannel,SetPermissions,AddDescription,InviteMembers process
    class ChatType,CheckHistory decision
    class Chat,LoadChat,CreateDirect,Send,Receive chat
```

## Message State Diagram

```mermaid
stateDiagram-v2
    [*] --> Draft: User types message
    
    Draft --> Sending: User clicks send
    Sending --> Sent: Server acknowledgment
    Sending --> Failed: Network error
    
    Failed --> Retry: Auto/manual retry
    Retry --> Sending: Retrying
    
    Sent --> Delivered: Message on receiver's device
    Delivered --> Read: Receiver viewed message
    
    state Read {
        [*] --> Seen
        Seen --> Reacted: User adds reaction
        Seen --> Replied: User replies in thread
    }
    
    Read --> Edited: Sender edits
    Edited --> Read: Receiver sees edited
    Read --> Deleted: Sender deletes
    
    Deleted --> [*]: Message removed
```
