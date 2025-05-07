<!-- filepath: d:\projects\CSA\csa-hello\.docs\modules\storage\module_diagram.md -->
# Storage Module Diagrams

## Component Architecture

```mermaid
graph TD
    subgraph Frontend
        FileExplorerUI["File Explorer UI<br>Browse & Manage Files"]
        UploaderUI["Uploader UI<br>File Upload Interface"]
        SharingUI["Sharing UI<br>Permission Management"]
        PreviewUI["Preview UI<br>File Preview"]
        SearchUI["Search UI<br>File Search Interface"]
    end
    
    subgraph Backend
        StorageController["StorageController<br>Core Storage Logic"]
        FileService["FileService<br>File Operations"]
        FolderService["FolderService<br>Folder Operations"]
        PermissionService["PermissionService<br>Access Control"]
        SearchService["SearchService<br>Content Search"]
    end
    
    subgraph Database
        FileDB[(Files)]
        FolderDB[(Folders)]
        FilePermDB[(FilePermissions)]
        FolderPermDB[(FolderPermissions)]
    end
    
    subgraph StorageLayer
        BlobStorage["Blob Storage<br>Raw File Data"]
        MetadataIndex["Metadata Index<br>Fast Metadata Retrieval"]
        ThumbnailCache["Thumbnail Cache<br>Preview Images"]
    end
    
    FileExplorerUI --> StorageController
    UploaderUI --> FileService
    SharingUI --> PermissionService
    PreviewUI --> FileService
    SearchUI --> SearchService
    
    StorageController --> FileService
    StorageController --> FolderService
    StorageController --> PermissionService
    
    FileService --> FileDB
    FileService --> BlobStorage
    FileService --> ThumbnailCache
    
    FolderService --> FolderDB
    
    PermissionService --> FilePermDB
    PermissionService --> FolderPermDB
    
    SearchService --> MetadataIndex
    SearchService --> FileDB
    SearchService --> FolderDB
    
    subgraph ExternalSystems
        CDN["Content Delivery Network<br>Fast Download"]
        AntiVirus["Anti-Virus Service<br>Security Scanning"]
        DocumentModule["Document Module<br>Collaborative Editing"]
        Messenger["Messenger Module<br>File Sharing"]
    end
    
    FileService --> CDN
    FileService --> AntiVirus
    StorageController --> DocumentModule
    StorageController --> Messenger
```

## File Upload and Processing Sequence

```mermaid
sequenceDiagram
    participant User
    participant UI as Storage UI
    participant Upload as Upload Service
    participant AV as Anti-Virus
    participant Thumb as Thumbnail Generator
    participant Storage as Blob Storage
    participant DB as Database
    
    User->>UI: Select file(s) for upload
    UI->>Upload: Initialize upload
    Upload->>DB: Create file record(s)
    DB-->>Upload: Return file ID(s)
    
    loop Each File
        UI->>Upload: Upload file chunks
        Upload->>Upload: Assemble file chunks
        
        Upload->>AV: Scan file for viruses
        AV-->>Upload: Security scan results
        
        alt If image or document
            Upload->>Thumb: Generate thumbnail
            Thumb-->>Upload: Thumbnail created
            Upload->>Storage: Store thumbnail
        end
        
        Upload->>Storage: Store complete file
        Storage-->>Upload: Confirm storage
        
        Upload->>DB: Update file metadata
        DB-->>Upload: Confirm update
    end
    
    Upload->>UI: Upload complete
    UI-->>User: Show completion status
    
    alt If shared folder
        Upload->>DB: Apply inherited permissions
        DB-->>Upload: Permissions applied
    end
```

## File Permission and Sharing Flow

```mermaid
flowchart TD
    Start([File/Folder Created])
    Owner{Apply Owner Permissions}
    SharedFolder{In Shared Folder?}
    Inherited[Apply Inherited Permissions]
    Default[Apply Default Permissions]
    
    Start --> Owner
    Owner --> SharedFolder
    SharedFolder -->|Yes| Inherited
    SharedFolder -->|No| Default
    
    Inherited --> Ready[Ready for Access]
    Default --> Ready
    
    Ready --> UserAction[User Initiates Sharing]
    
    UserAction --> ShareType{Sharing Type?}
    
    ShareType -->|Internal| InternalShare[Select Users/Groups]
    ShareType -->|External| ExternalShare[Generate Share Link]
    ShareType -->|Public| PublicShare[Create Public Access]
    
    InternalShare --> PermLevel{Permission Level?}
    ExternalShare --> ShareSettings[Configure Link Settings]
    PublicShare --> PublicSettings[Configure Public Access]
    
    PermLevel -->|View| ViewPerm[View Permission]
    PermLevel -->|Download| DownloadPerm[Download Permission]
    PermLevel -->|Edit| EditPerm[Edit Permission]
    PermLevel -->|Full| FullPerm[Full Permission]
    
    ViewPerm --> ApplyPerm[Apply Permissions]
    DownloadPerm --> ApplyPerm
    EditPerm --> ApplyPerm
    FullPerm --> ApplyPerm
    
    ShareSettings --> CreateLink[Create Secure Link]
    PublicSettings --> CreatePublic[Create Public Access]
    
    ApplyPerm --> Notify[Notify Recipients]
    CreateLink --> Delivery{Delivery Method?}
    CreatePublic --> Active[Activate Public Access]
    
    Delivery -->|Email| SendEmail[Send Email]
    Delivery -->|Copy| CopyLink[Copy to Clipboard]
    Delivery -->|Message| SendMessage[Send in Message]
    
    SendEmail --> Shared([Sharing Complete])
    CopyLink --> Shared
    SendMessage --> Shared
    Active --> Shared
    Notify --> Shared
    
    classDef start fill:#d4f1f9,stroke:#05a4d2
    classDef process fill:#c9e7dd,stroke:#0ca789
    classDef decision fill:#ffe6cc,stroke:#ff9933
    classDef permission fill:#e6e6fa,stroke:#8a2be2
    
    class Start start
    class Owner,Inherited,Default,UserAction,ApplyPerm,CreateLink,CreatePublic process
    class SharedFolder,ShareType,PermLevel,Delivery decision
    class ViewPerm,DownloadPerm,EditPerm,FullPerm permission
```

## File Lifecycle State Diagram

```mermaid
stateDiagram-v2
    [*] --> Created: User uploads file
    
    Created --> Active: File ready for use
    
    state Active {
        [*] --> Idle
        Idle --> InUse: File being accessed
        InUse --> Idle: Access complete
        Idle --> Locked: File locked for editing
        Locked --> Idle: Lock released
    }
    
    Active --> Shared: Permissions granted
    Shared --> Active: Permissions revoked
    
    Active --> Starred: User stars file
    Starred --> Active: User removes star
    
    Active --> Archived: User archives file
    Archived --> Active: User restores file
    
    Active --> Trashed: User deletes file
    Trashed --> Active: User restores from trash
    Trashed --> PermanentlyDeleted: Retention period expires
    
    PermanentlyDeleted --> [*]: File record removed
```
