<!-- filepath: d:\projects\CSA\csa-hello\.docs\modules\user\module_diagram.md -->
# User Module Diagrams

## Component Architecture

```mermaid
graph TD
    subgraph Frontend
        AuthUI["Authentication UI<br>Login & Registration"]
        ProfileUI["Profile UI<br>User Profile Management"]
        AdminUI["Admin UI<br>User Administration"]
        PermissionUI["Permission UI<br>Role Management"]
        PreferenceUI["Preference UI<br>User Settings"]
        OrgChartUI["Organization Chart UI<br>Department Visualization"]
        DeptUI["Department Management UI<br>Structure Administration"]
        PositionUI["Position Management UI<br>Role Administration"]
    end
      subgraph Backend
        AuthController["AuthController<br>Authentication Logic"]
        UserController["UserController<br>User Management"]
        RoleService["RoleService<br>Role & Permission Management"]
        ProfileService["ProfileService<br>Profile Management"]
        ActivityService["ActivityService<br>User Activity Tracking"]
        DepartmentService["DepartmentService<br>Department Hierarchy Management"]
        PositionService["PositionService<br>Position Management"]
        OrgChartService["OrgChartService<br>Organizational Visualization"]
        SyncService["SynchronizationService<br>HR System Integration"]
    end
    
    subgraph Database
        UserDB[(Users)]
        ProfileDB[(UserProfiles)]
        RoleDB[(Roles)]
        PermissionDB[(Permissions)]
        SessionDB[(Sessions)]
        ActivityLogDB[(ActivityLogs)]
        DepartmentDB[(Departments)]
        PositionDB[(Positions)]
        DeptMembershipDB[(DepartmentMemberships)]
        HierarchyDB[(DepartmentHierarchy)]
    end
      AuthUI --> AuthController
    ProfileUI --> ProfileService
    AdminUI --> UserController
    PermissionUI --> RoleService
    PreferenceUI --> ProfileService
    OrgChartUI --> OrgChartService
    DeptUI --> DepartmentService
    PositionUI --> PositionService
    
    AuthController --> UserDB
    AuthController --> SessionDB
    
    UserController --> UserDB
    UserController --> RoleDB
    UserController --> DepartmentDB
    UserController --> PositionDB
    
    ProfileService --> ProfileDB
    ProfileService --> UserDB
    
    RoleService --> RoleDB
    RoleService --> PermissionDB
    
    ActivityService --> ActivityLogDB
    
    DepartmentService --> DepartmentDB
    DepartmentService --> HierarchyDB
    DepartmentService --> UserDB
    DepartmentService --> DeptMembershipDB
    
    PositionService --> PositionDB
    PositionService --> UserDB
    PositionService --> DepartmentDB
    
    OrgChartService --> DepartmentDB
    OrgChartService --> PositionDB
    OrgChartService --> UserDB
    OrgChartService --> HierarchyDB
    
    SyncService --> DepartmentDB
    SyncService --> PositionDB
    SyncService --> UserDB
    
    AuthController --> ActivityService
    UserController --> ActivityService
    ProfileService --> ActivityService
    DepartmentService --> ActivityService
    PositionService --> ActivityService
    
    subgraph ExternalSystems
        OAuth["OAuth Providers<br>External Authentication"]
        EmailService["Email Service<br>Verification & Notifications"]
        AuditSystem["Audit System<br>Security Logging"]
        PermissionCaches["Permission Cache<br>Fast Permission Checks"]
    end
    
    AuthController --> OAuth
    AuthController --> EmailService
    ActivityService --> AuditSystem    RoleService --> PermissionCaches
    DepartmentService --> ExternalSystems
```

## Department Hierarchy Model

```mermaid
graph TD
    RootDept["Company Root<br>(Level 0)"]
    
    L1Dept1["Executive<br>(Level 1)"]
    L1Dept2["Operations<br>(Level 1)"]
    L1Dept3["Product<br>(Level 1)"]
    L1Dept4["Marketing<br>(Level 1)"]
    
    L2Dept1["Finance<br>(Level 2)"]
    L2Dept2["HR<br>(Level 2)"]
    L2Dept3["Regional Ops<br>(Level 2)"]
    L2Dept4["Central Ops<br>(Level 2)"]
    L2Dept5["Engineering<br>(Level 2)"]
    L2Dept6["Design<br>(Level 2)"]
    L2Dept7["Brand<br>(Level 2)"]
    L2Dept8["Growth<br>(Level 2)"]
    
    L3Dept1["Payroll<br>(Level 3)"]
    L3Dept2["Recruiting<br>(Level 3)"]
    L3Dept3["APAC<br>(Level 3)"]
    L3Dept4["EMEA<br>(Level 3)"]
    L3Dept5["Americas<br>(Level 3)"]
    L3Dept6["Frontend<br>(Level 3)"]
    L3Dept7["Backend<br>(Level 3)"]
    L3Dept8["UX<br>(Level 3)"]
    L3Dept9["UI<br>(Level 3)"]
    
    RootDept --> L1Dept1
    RootDept --> L1Dept2
    RootDept --> L1Dept3
    RootDept --> L1Dept4
    
    L1Dept1 --> L2Dept1
    L1Dept1 --> L2Dept2
    
    L1Dept2 --> L2Dept3
    L1Dept2 --> L2Dept4
    
    L1Dept3 --> L2Dept5
    L1Dept3 --> L2Dept6
    
    L1Dept4 --> L2Dept7
    L1Dept4 --> L2Dept8
    
    L2Dept2 --> L3Dept1
    L2Dept2 --> L3Dept2
    
    L2Dept3 --> L3Dept3
    L2Dept3 --> L3Dept4
    L2Dept3 --> L3Dept5
    
    L2Dept5 --> L3Dept6
    L2Dept5 --> L3Dept7
    
    L2Dept6 --> L3Dept8
    L2Dept6 --> L3Dept9
    
    classDef root fill:#f9d5e5,stroke:#d3688b
    classDef level1 fill:#e3f2fd,stroke:#1565c0
    classDef level2 fill:#e8f5e9,stroke:#2e7d32
    classDef level3 fill:#fff8e1,stroke:#ff8f00
    
    class RootDept root
    class L1Dept1,L1Dept2,L1Dept3,L1Dept4 level1
    class L2Dept1,L2Dept2,L2Dept3,L2Dept4,L2Dept5,L2Dept6,L2Dept7,L2Dept8 level2
    class L3Dept1,L3Dept2,L3Dept3,L3Dept4,L3Dept5,L3Dept6,L3Dept7,L3Dept8,L3Dept9 level3
```

## Department-User Relationship Model

```mermaid
graph TD
    subgraph Departments
        Dept1["Engineering Department"]
        Dept2["Marketing Department"]
        Dept3["Design Department"]
    end
    
    subgraph Positions
        Pos1["Engineering Manager"]
        Pos2["Senior Developer"]
        Pos3["Junior Developer"]
        Pos4["Marketing Director"]
        Pos5["Marketing Specialist"]
        Pos6["Lead Designer"]
    end
    
    subgraph Users
        User1["John Smith<br>Engineering Manager"]
        User2["Alice Johnson<br>Senior Developer"]
        User3["Bob Williams<br>Senior Developer"]
        User4["Carol Brown<br>Junior Developer"]
        User5["David Miller<br>Marketing Director"]
        User6["Eva Davis<br>Marketing Specialist"]
        User7["Frank Wilson<br>Lead Designer"]
    end
    
    Dept1 -->|has position| Pos1
    Dept1 -->|has position| Pos2
    Dept1 -->|has position| Pos3
    Dept2 -->|has position| Pos4
    Dept2 -->|has position| Pos5
    Dept3 -->|has position| Pos6
    
    User1 -->|assigned to| Pos1
    User2 -->|assigned to| Pos2
    User3 -->|assigned to| Pos2
    User4 -->|assigned to| Pos3
    User5 -->|assigned to| Pos4
    User6 -->|assigned to| Pos5
    User7 -->|assigned to| Pos6
    
    User1 -->|manages| User2
    User1 -->|manages| User3
    User1 -->|manages| User4
    User2 -->|mentors| User4
    User5 -->|manages| User6
    
    User3 -.->|cross-department<br>collaboration| User7
    
    classDef dept fill:#e1f5fe,stroke:#0277bd
    classDef pos fill:#e8f5e9,stroke:#388e3c
    classDef user fill:#f3e5f5,stroke:#7b1fa2
    
    class Dept1,Dept2,Dept3 dept
    class Pos1,Pos2,Pos3,Pos4,Pos5,Pos6 pos
    class User1,User2,User3,User4,User5,User6,User7 user
```

## Authentication Sequence Diagram

```mermaid
sequenceDiagram
    participant User
    participant UI as Authentication UI
    participant Auth as AuthController
    participant User as UserService
    participant OAuth as OAuth Provider
    participant Email as Email Service
    participant DB as Database
    
    alt Standard Login
        User->>UI: Enter credentials
        UI->>Auth: authenticate(email, password)
        Auth->>DB: validateCredentials(email, password)
        DB-->>Auth: Validation result
        
        alt Valid Credentials
            Auth->>DB: createSession(userId)
            DB-->>Auth: Session token
            Auth->>Auth: Generate JWT
            Auth-->>UI: Return JWT & user info
            UI-->>User: Login successful
        else Invalid Credentials
            Auth-->>UI: Authentication failed
            UI-->>User: Show error message
        end
    else OAuth Login
        User->>UI: Click OAuth provider
        UI->>OAuth: Redirect to provider login
        OAuth-->>User: Provider login form
        User->>OAuth: Authenticate with provider
        OAuth-->>UI: Return with auth code
        UI->>Auth: authenticateOAuth(provider, code)
        Auth->>OAuth: Verify auth code & get profile
        OAuth-->>Auth: User profile data
        
        Auth->>DB: findOrCreateUser(oauthData)
        DB-->>Auth: User record
        Auth->>DB: createSession(userId)
        DB-->>Auth: Session token
        Auth->>Auth: Generate JWT
        Auth-->>UI: Return JWT & user info
        UI-->>User: Login successful
    end
    
    Auth->>Email: Log successful login
```

## User Registration and Verification Flow

```mermaid
flowchart TD
    Start([User Registration])
    
    Registration[Complete Registration Form]
    Validation{Form Valid?}
    EmailCheck{Email Available?}
    CreateUser[Create User Record]
    AssignRoles[Assign Default Roles]
    SendVerification[Send Verification Email]
    
    VerificationLink[User Clicks Verification Link]
    TokenCheck{Token Valid?}
    ActivateUser[Activate User Account]
    InvalidToken[Show Invalid Token Error]
    
    LoginPrompt[Prompt User to Login]
    
    Start --> Registration
    Registration --> Validation
    Validation -->|Yes| EmailCheck
    Validation -->|No| FormError[Show Validation Errors]
    FormError --> Registration
    
    EmailCheck -->|Yes| CreateUser
    EmailCheck -->|No| EmailError[Show Email In Use Error]
    EmailError --> Registration
    
    CreateUser --> AssignRoles
    AssignRoles --> SendVerification
    SendVerification --> PendingState[Registration Complete - Awaiting Verification]
    
    PendingState --> VerificationLink
    VerificationLink --> TokenCheck
    TokenCheck -->|Yes| ActivateUser
    TokenCheck -->|No| InvalidToken
    
    InvalidToken -->|Request New Link| ResendLink[Resend Verification]
    ResendLink --> PendingState
    
    ActivateUser --> LoginPrompt
    
    classDef start fill:#d4f1f9,stroke:#05a4d2
    classDef process fill:#c9e7dd,stroke:#0ca789
    classDef decision fill:#ffe6cc,stroke:#ff9933
    classDef error fill:#f9d1d1,stroke:#e06666
    classDef success fill:#e6f4ea,stroke:#137333
    
    class Start start
    class Registration,CreateUser,AssignRoles,SendVerification,VerificationLink,ActivateUser,ResendLink process
    class Validation,EmailCheck,TokenCheck decision
    class FormError,EmailError,InvalidToken error
    class LoginPrompt,PendingState success
```

## Role-based Access Control Model

```mermaid
stateDiagram-v2
    [*] --> UserCreated: New user registered
    UserCreated --> RoleAssigned: Default role assigned
    
    state RoleAssigned {
        [*] --> StandardUser
        StandardUser --> Manager: Promoted to manager
        Manager --> Admin: Promoted to admin
        Admin --> StandardUser: Demoted from admin
        Manager --> StandardUser: Demoted from manager
    }
    
    RoleAssigned --> PermissionCheck: Access attempt
    
    state PermissionCheck {
        [*] --> CheckRole
        CheckRole --> EvaluatePermissions
        EvaluatePermissions --> CacheResult
    }
    
    PermissionCheck --> AccessGranted: Permission found
    PermissionCheck --> AccessDenied: Permission not found
    
    AccessDenied --> RoleAssigned: Back to current role
    AccessGranted --> AccessLogged: Record access
    AccessLogged --> RoleAssigned: Back to current role
    
    RoleAssigned --> UserDeactivated: User account deactivated
    UserDeactivated --> RoleAssigned: User account reactivated
    UserDeactivated --> UserDeleted: User permanently removed
    
    UserDeleted --> [*]
```
