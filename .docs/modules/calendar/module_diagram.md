<!-- filepath: d:\projects\CSA\csa-hello\.docs\modules\calendar\module_diagram.md -->
# Calendar Module Diagrams

## Component Architecture

```mermaid
graph TD
    subgraph Frontend
        CalUI["Calendar UI<br>Interactive Calendar Views"]
        EventForm["Event Form<br>Create/Edit Events"]
        NotifUI["Notification UI<br>Reminders & Alerts"]
    end
    
    subgraph Backend
        CalController["CalendarController<br>Business Logic"]
        EventService["EventService<br>Event Operations"]
        RecurService["RecurrenceService<br>Handles Recurring Events"]
        ReminderService["ReminderService<br>Manages Notifications"]
    end
    
    subgraph Database
        CalDB[(Calendar)]
        EventDB[(Events)]
        RecurRuleDB[(RecurrenceRules)]
        ParticipantDB[(Participants)]
    end
    
    CalUI --> CalController
    EventForm --> EventService
    NotifUI --> ReminderService
    
    CalController --> CalDB
    EventService --> EventDB
    EventService --> RecurService
    RecurService --> RecurRuleDB
    ReminderService --> EventDB
    EventService --> ParticipantDB
    
    subgraph ExternalSystems
        EmailService["Email Service<br>Invitation Emails"]
        NotificationSystem["Notification System<br>Push Notifications"]
    end
    
    ReminderService --> EmailService
    ReminderService --> NotificationSystem
```

## Event Creation Sequence

```mermaid
sequenceDiagram
    participant User
    participant UI as Calendar UI
    participant EC as EventController
    participant ES as EventService
    participant RS as RecurrenceService
    participant NS as NotificationService
    participant DB as Database
    
    User->>UI: Create New Event
    UI->>EC: submitEventData(eventData)
    EC->>ES: createEvent(data)
    ES->>DB: saveEventDetails()
    DB-->>ES: Return eventId
    
    alt Has Recurrence
        ES->>RS: createRecurrencePattern(eventId, pattern)
        RS->>DB: saveRecurrenceRules()
        DB-->>RS: Confirm Save
        RS-->>ES: Return recurrenceId
    end
    
    ES->>NS: scheduleNotifications(eventId)
    NS->>DB: saveNotificationSchedule()
    DB-->>NS: Confirm Save
    NS-->>ES: Notifications Scheduled
    ES-->>EC: Event Created
    EC-->>UI: Display Success
    UI-->>User: Show Confirmation
```

## Calendar Data Flow

```mermaid
flowchart LR
    User([User])
    CalView{Calendar View}
    API[Calendar API]
    Controller[Calendar Controller]
    Service[Calendar Service]
    DB[(Database)]
    Email[Email Service]
    Notif[Notification Service]
    
    User --> CalView
    CalView --> API
    API --> Controller
    Controller --> Service
    Service --> DB
    Service --> Email
    Service --> Notif
    DB --> Service
    Service --> Controller
    Controller --> API
    API --> CalView
    CalView --> User
    
    classDef userAction fill:#e1f5fe,stroke:#0277bd
    classDef frontEnd fill:#fff9c4,stroke:#fbc02d
    classDef api fill:#f9fbe7,stroke:#afb42b
    classDef backend fill:#e8f5e9,stroke:#388e3c
    classDef db fill:#ede7f6,stroke:#4527a0
    classDef services fill:#fce4ec,stroke:#c2185b
    
    class User userAction
    class CalView frontEnd
    class API api
    class Controller,Service backend
    class DB db
    class Email,Notif services
```

## User Authorization Flow

```mermaid
stateDiagram-v2
    [*] --> ViewCalendar: User opens calendar
    
    ViewCalendar --> CheckPermission: Attempt to modify
    
    state CheckPermission {
        [*] --> IsOwner
        IsOwner --> Yes: User is calendar owner
        IsOwner --> No: User is not owner
        No --> HasEditRights
        HasEditRights --> Yes: User has edit rights 
        HasEditRights --> No: User lacks edit rights
        Yes --> [*]: Allow
        No --> [*]: Deny
    }
    
    CheckPermission --> ModifyCalendar: Permission granted
    CheckPermission --> AccessDenied: Permission denied
    
    ModifyCalendar --> ViewCalendar: Changes saved
    AccessDenied --> ViewCalendar: Read-only access
    
    ViewCalendar --> [*]: User closes calendar
```
