<!-- filepath: d:\projects\CSA\csa-hello\.docs\modules\document\module_diagram.md -->
# Document Module Diagrams

## Component Architecture

```mermaid
graph TD
    subgraph Frontend
        DocUI["Document UI<br>Document Editor Interface"]
        VersionUI["Version UI<br>Version Management"]
        PermUI["Permission UI<br>Sharing & Access Control"]
        CollabUI["Collaboration UI<br>Real-time Editing"]
    end
    
    subgraph Backend
        DocController["DocumentController<br>Core Document Logic"]
        VersionService["VersionService<br>Version Operations"]
        PermService["PermissionService<br>Access Control"]
        CollabService["CollaborationService<br>Real-time Synchronization"]
    end
    
    subgraph Database
        DocDB[(Documents)]
        VersionDB[(DocumentVersions)]
        PermDB[(DocumentPermissions)]
        CommentDB[(Comments)]
    end
    
    DocUI --> DocController
    VersionUI --> VersionService
    PermUI --> PermService
    CollabUI --> CollabService
    
    DocController --> DocDB
    VersionService --> VersionDB
    PermService --> PermDB
    CollabService --> DocDB
    CollabService --> CommentDB
    
    subgraph ExternalSystems
        StorageSystem["Storage Module<br>File Storage"]
        NotificationSystem["Notification System<br>Change Alerts"]
        SearchIndex["Search Module<br>Content Indexing"]
    end
    
    DocController --> StorageSystem
    CollabService --> NotificationSystem
    DocController --> SearchIndex
```

## Document Collaboration Sequence

```mermaid
sequenceDiagram
    participant User1 as User 1
    participant User2 as User 2
    participant UI as Document UI
    participant Collab as CollabService
    participant Doc as DocumentService
    participant Version as VersionService
    participant DB as Database
    
    User1->>UI: Open Document
    UI->>Doc: getDocument(id)
    Doc->>DB: fetch document
    DB-->>Doc: document data
    Doc-->>UI: render document
    UI-->>User1: display document
    
    User1->>UI: Edit document
    UI->>Collab: sendChanges(delta)
    Collab->>DB: storeChanges(delta)
    Collab->>User2: broadcastChanges(delta)
    User2->>UI: See real-time changes
    
    User1->>UI: Save document
    UI->>Doc: saveDocument(content)
    Doc->>Version: createVersion(documentId, content)
    Version->>DB: saveVersion()
    DB-->>Version: version saved
    Version-->>Doc: version created
    Doc-->>UI: save successful
    UI-->>User1: show confirmation
```

## Document Access Control Flow

```mermaid
flowchart TD
    User([User])
    Request{Request Document}
    CheckOwner{Is Owner?}
    CheckPerm{Has Permission?}
    CheckPublic{Is Public?}
    Access([Access Granted])
    Denied([Access Denied])
    
    User --> Request
    Request --> CheckOwner
    CheckOwner -->|Yes| Access
    CheckOwner -->|No| CheckPerm
    CheckPerm -->|Yes| Access
    CheckPerm -->|No| CheckPublic
    CheckPublic -->|Yes| Access
    CheckPublic -->|No| Denied
    
    subgraph PermissionLevels
        View[View Only]
        Comment[Comment]
        Edit[Edit]
        Owner[Owner]
    end
    
    Access --> CheckLevel{Permission Level}
    CheckLevel -->|VIEW| View
    CheckLevel -->|COMMENT| Comment
    CheckLevel -->|EDIT| Edit
    CheckLevel -->|OWNER| Owner
    
    classDef start fill:#d4f1f9,stroke:#05a4d2
    classDef process fill:#e8f5e9,stroke:#388e3c
    classDef decision fill:#ffe6cc,stroke:#ff9933
    classDef denied fill:#f9d1d1,stroke:#e06666
    classDef perms fill:#ede7f6,stroke:#4527a0
    
    class User,Request start
    class Access process
    class CheckOwner,CheckPerm,CheckPublic,CheckLevel decision
    class Denied denied
    class View,Comment,Edit,Owner perms
```

## Document Version Control State Diagram

```mermaid
stateDiagram-v2
    [*] --> Draft: Create Document
    
    Draft --> Saved: Initial Save
    Saved --> Editing: User Edits
    
    Editing --> Saved: Save Changes
    
    Saved --> Published: Publish
    Published --> Editing: Make Changes
    
    state Saved {
        [*] --> AutoVersion: Auto Save
        [*] --> NamedVersion: Manual Save with Name
        AutoVersion --> LatestVersion: Set as latest
        NamedVersion --> LatestVersion: Set as latest
    }
    
    Published --> [*]: Archive Document
```
