# Notification Module Diagrams

## Component Architecture

```mermaid
graph TD
    subgraph Frontend
        NotifBell["Notification Bell<br>Unread Indicator"]
        NotifCenter["Notification Center<br>List & Filters"]
        NotifCard["Notification Cards<br>Interactive Display"]
        NotifSettings["Settings Interface<br>Preferences Control"]
        NotifAdmin["Admin Interface<br>Template Management"]
    end
    
    subgraph Backend
        NotifController["NotificationController<br>API Endpoints"]
        NotifService["NotificationService<br>Business Logic"]
        TemplateEngine["Template Engine<br>Variable Substitution"]
        DeliveryManager["Delivery Manager<br>Channel Distribution"]
        NotifProcessor["Notification Processor<br>Background Tasks"]
    end
    
    subgraph Database
        NotifDB[(Notifications)]
        SettingsDB[(NotificationSettings)]
        TemplateDB[(NotificationTemplates)]
    end
    
    subgraph ExternalServices
        EmailService["Email Service<br>SMTP/API"]
        PushService["Push Notification<br>Web/Mobile"]
        SMSService["SMS Gateway<br>Text Messages"]
    end
    
    %% Frontend to Backend connections
    NotifBell --> NotifController
    NotifCenter --> NotifController
    NotifCard --> NotifController
    NotifSettings --> NotifController
    NotifAdmin --> NotifController
    
    %% Backend internal connections
    NotifController --> NotifService
    NotifService --> TemplateEngine
    NotifService --> DeliveryManager
    NotifService --> NotifProcessor
    TemplateEngine --> DeliveryManager
    
    %% Backend to Database connections
    NotifService --> NotifDB
    NotifService --> SettingsDB
    NotifService --> TemplateDB
    
    %% Backend to External Services
    DeliveryManager --> EmailService
    DeliveryManager --> PushService
    DeliveryManager --> SMSService
    
    %% Integration Points
    OtherModules["Other Platform Modules"] --> NotifService
    NotifProcessor --> OtherModules
    
    classDef frontend fill:#d4f1f9,stroke:#05a4d2
    classDef backend fill:#c9e7dd,stroke:#0ca789
    classDef database fill:#f9d3be,stroke:#e67e22
    classDef external fill:#e6e6fa,stroke:#8a2be2
    
    class NotifBell,NotifCenter,NotifCard,NotifSettings,NotifAdmin frontend
    class NotifController,NotifService,TemplateEngine,DeliveryManager,NotifProcessor backend
    class NotifDB,SettingsDB,TemplateDB database
    class EmailService,PushService,SMSService external
```

## Notification Flow Sequence Diagram

```mermaid
sequenceDiagram
    participant Source as Source Module
    participant Service as Notification Service
    participant DB as Database
    participant Template as Template Engine
    participant Delivery as Delivery Manager
    participant User as User Interface
    participant External as External Channels
    
    Source->>Service: Create Notification
    
    alt Direct Creation
        Service->>DB: Store Notification
    else Template-based
        Service->>Template: Get Template
        Template->>Service: Rendered Template
        Service->>DB: Store Notification
    end
    
    Service->>DB: Check User Preferences
    DB->>Service: Notification Settings
    
    Service->>Delivery: Deliver Notification
    
    par In-App Notification
        Delivery->>User: Push to UI via WebSocket
        User->>User: Display Notification
    and Email Notification
        Delivery->>External: Send Email
    and Push Notification
        Delivery->>External: Send Push Alert
    and SMS Notification
        Delivery->>External: Send SMS
    end
    
    Service->>DB: Update Delivery Status
    
    User->>Service: Mark as Read
    Service->>DB: Update Read Status
    
    User->>Service: Perform Action
    Service->>Source: Redirect to Source
```

## Notification Delivery Flow

```mermaid
flowchart TD
    Start([New Notification]) --> CreateNotif[Create Notification]
    CreateNotif --> CheckSettings{Check User Settings}
    
    CheckSettings -->|Get Preferences| UserPrefs[User Notification Preferences]
    UserPrefs --> FilterByType{Filter By Type}
    
    FilterByType -->|Disabled| Skip[Skip Notification]
    FilterByType -->|Enabled| CheckPriority{Check Priority}
    
    CheckPriority -->|Below Threshold| Skip
    CheckPriority -->|Meets Threshold| CheckChannels{Select Delivery Channels}
    
    CheckChannels -->|In-App Enabled| InApp[Deliver In-App Notification]
    CheckChannels -->|Email Enabled| Email[Send Email Notification]
    CheckChannels -->|Push Enabled| Push[Send Push Notification]
    CheckChannels -->|SMS Enabled| SMS[Send SMS Notification]
    
    InApp --> UpdateStatus[Update Delivery Status]
    Email --> UpdateStatus
    Push --> UpdateStatus
    SMS --> UpdateStatus
    
    UpdateStatus --> End([Notification Processed])
    Skip --> End
    
    classDef start fill:#e5f8e5,stroke:#3c763d
    classDef process fill:#e3f2fd,stroke:#1565c0
    classDef decision fill:#fff8e1,stroke:#ff8f00
    classDef end fill:#f9d1d1,stroke:#e06666
    
    class Start start
    class CreateNotif,UserPrefs,InApp,Email,Push,SMS,UpdateStatus process
    class CheckSettings,FilterByType,CheckPriority,CheckChannels decision
    class End,Skip end
```

## Notification State Diagram

```mermaid
stateDiagram-v2
    [*] --> Created: Notification Created
    
    state "Delivery Status" as DeliveryStatus {
        Queued --> InAppDelivered: In-App Delivered
        Queued --> EmailSent: Email Sent
        Queued --> PushSent: Push Sent
        Queued --> SMSSent: SMS Sent
    }
    
    Created --> DeliveryStatus: Process Notification
    
    state "User Interaction" as UserInteraction {
        Unread --> Read: User Opens
        Read --> Actioned: User Takes Action
    }
    
    DeliveryStatus --> UserInteraction: Delivered to User
    
    UserInteraction --> Archived: User Archives
    UserInteraction --> Deleted: User Deletes
    
    Archived --> [*]
    Deleted --> [*]
```

## Template System Architecture

```mermaid
graph TD
    subgraph TemplateSystem
        TemplateRepo[("Template Repository")]
        TemplateRenderer["Template Renderer"]
        VariableParser["Variable Parser"]
        ChannelFormatter["Channel Formatter"]
    end
    
    Data["Notification Data"] --> VariableParser
    TemplateRepo --> TemplateRenderer
    VariableParser --> TemplateRenderer
    TemplateRenderer --> ChannelFormatter
    
    ChannelFormatter -->|In-App| InAppNotification["UI Notification"]
    ChannelFormatter -->|Email| EmailNotification["HTML/Text Email"]
    ChannelFormatter -->|Push| PushNotification["Push Payload"]
    ChannelFormatter -->|SMS| SMSNotification["Plain Text SMS"]
    
    classDef data fill:#f9d3be,stroke:#e67e22
    classDef template fill:#c9e7dd,stroke:#0ca789
    classDef output fill:#d4f1f9,stroke:#05a4d2
    
    class Data data
    class TemplateRepo,TemplateRenderer,VariableParser,ChannelFormatter template
    class InAppNotification,EmailNotification,PushNotification,SMSNotification output
```

## User Preference Model

```mermaid
erDiagram
    USER ||--o{ NOTIFICATION-SETTING : has
    USER ||--o{ NOTIFICATION : receives
    NOTIFICATION-SETTING {
        int user_id
        enum notification_type
        bool in_app_enabled
        bool email_enabled
        bool push_enabled
        bool sms_enabled
        enum min_priority
    }
    
    NOTIFICATION-TYPE ||--o{ NOTIFICATION-SETTING : configures
    NOTIFICATION-TYPE ||--o{ NOTIFICATION : categorizes
    NOTIFICATION-TYPE {
        string type_name
        string description
        bool is_default_enabled
    }
    
    NOTIFICATION {
        int id
        int user_id
        string title
        string content
        enum notification_type
        enum priority
        string resource_type
        int resource_id
        json data
        string icon
        datetime created_at
        datetime read_at
        bool in_app_delivered
        bool email_delivered
        bool push_delivered
        bool sms_delivered
    }
    
    NOTIFICATION-TEMPLATE ||--o{ NOTIFICATION : creates
    NOTIFICATION-TEMPLATE {
        int id
        string name
        enum notification_type
        string title_template
        string content_template
        string email_subject_template
        string email_body_template
        string sms_template
        string default_icon
        bool is_active
    }
```
