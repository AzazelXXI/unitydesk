# Summary Diagram (Conceptual)

```
+---------------------+     +---------------------+     +---------------------+
|     Web Client      |     |   Mobile Clients    |     |  Desktop Clients    |
| (React + TypeScript)|     | (Flutter/React Native) |   | (Tauri + React)    |
+---------------------+     +---------------------+     +---------------------+
            |                           |                          |
            +---------------------------+--------------------------+
                                        |
                                +------------------+
                                |    Ingress       | (NGINX Ingress Controller)
                                +------------------+
                                        |
+-----------------------------------------------------------------------------+
| Windows Server (Windows 10/11 Pro) với Docker Desktop & Kubernetes          |
|                                                                             |
|    +-----------------------------------------------------------------+     |
|    |                   Kubernetes Cluster (Single-node)               |     |
|    |                                                                   |     |
|    |  +----------------+  +----------------+                          |     |
|    |  | API Gateway    |  | Service Mesh   |                          |     |
|    |  | (Kong/Traefik) |  | (Istio/Linkerd)|                          |     |
|    |  +----------------+  +----------------+                          |     |
|    |                                                                   |     |
|    |  +----------------+  +----------------+  +----------------+      |     |
|    |  | Auth-Service   |  | Messenger-     |  | Calendar-      |      |     |
|    |  | Container      |  | Service         |  | Service        |      |     |
|    |  +----------------+  +----------------+  +----------------+      |     |
|    |                                                                   |     |
|    |  +----------------+  +----------------+  +----------------+      |     |
|    |  | Docs-Service   |  | Drive-Service  |  | Email-Service  |      |     |
|    |  | Container      |  | Container      |  | Container      |      |     |
|    |  +----------------+  +----------------+  +----------------+      |     |
|    |                                                                   |     |
|    |  +----------------+  +----------------+  +----------------+      |     |
|    |  | Tasks-Service  |  | Approval-      |  | Video-Service  |      |     |
|    |  | Container      |  | Service        |  | Container      |      |     |
|    |  +----------------+  +----------------+  +----------------+      |     |
|    |                                                                   |     |
|    |  +----------------+  +----------------+  +----------------+      |     |
|    |  | Admin-Service  |  | Platform-      |  | WebSocket      |      |     |
|    |  | Container      |  | Service        |  | Service        |      |     |
|    |  +----------------+  +----------------+  +----------------+      |     |
|    |                                                                   |     |
|    |  +-----------------------+  +--------------------------------+   |     |
|    |  | Message Broker        |  |     Background Tasks           |   |     |
|    |  | (RabbitMQ/Kafka)      |  |     Containers                 |   |     |
|    |  +-----------------------+  +--------------------------------+   |     |
|    |                                                                   |     |
|    |  +-----------------------+  +--------------------------------+   |     |
|    |  | Monitoring & Logging  |  |     CI/CD Pipeline              |   |     |
|    |  | (Prometheus, EFK)     |  |     (GitHub Actions/GitLab CI)  |   |     |
|    |  +-----------------------+  +--------------------------------+   |     |
|    +-----------------------------------------------------------------+     |
|                                                                             |
|    +-----------------+  +---------------+  +------------------+             |
|    |   PostgreSQL    |  |  Redis Cache  |  |   MinIO Object   |             |
|    |    Container    |  |   Container   |  |  Storage Container|             |
|    +-----------------+  +---------------+  +------------------+             |
|                                                                             |
|    +-----------------+  +---------------+                                   |
|    |  PgBouncer      |  | Elasticsearch |                                   |
|    |   Container     |  |  Container    |                                   |
|    +-----------------+  +---------------+                                   |
|                                                                             |
|    +----------------------------------------------------------------------+ |
|    |                      Persistent Volumes (Kubernetes PV)               | |
|    +----------------------------------------------------------------------+ |
|                                                                             |
+-----------------------------------------------------------------------------+
```

## Kubernetes Architecture Diagram

```mermaid
flowchart TD
    %% External Access
    Internet((Internet)) -->|HTTPS| IngressController[NGINX Ingress Controller]
    
    %% API Gateway
    IngressController -->|HTTP| ApiGateway[API Gateway\nKong/Traefik]
    
    %% Auth Flow
    ApiGateway --> AuthService[Auth-Service Pod]
    AuthService --> Keycloak[Keycloak Container\nOAuth2/OIDC Provider]
    
    %% Main Services
    ApiGateway --> MessengerService[Messenger-Service Pod]
    ApiGateway --> CalendarService[Calendar-Service Pod]
    ApiGateway --> DocsService[Docs-Service Pod]
    ApiGateway --> DriveService[Drive-Service Pod]
    ApiGateway --> EmailService[Email-Service Pod]
    ApiGateway --> TasksService[Tasks-Service Pod]
    ApiGateway --> ApprovalService[Approval-Service Pod]
    ApiGateway --> VideoService[Video-Service Pod]
    ApiGateway --> AdminService[Admin-Service Pod]
    ApiGateway --> PlatformService[Platform-Service Pod]
    ApiGateway --> WebsocketService[WebSocket-Service Pod]
    
    %% Databases & Storage
    PostgreSQL[(PostgreSQL StatefulSet)] <--> PgBouncer[PgBouncer Pod]
    Redis[(Redis StatefulSet)] <--> CacheService[Cache Service]
    MinIO[(MinIO Object Storage)] <--> DriveService
    MinIO <--> DocsService
    
    %% Auth connects to all services
    AuthService -.->|Authentication| MessengerService & CalendarService & DocsService & DriveService & EmailService & TasksService & ApprovalService & VideoService & AdminService & PlatformService
    
    %% Message broker
    MessageBroker[Message Broker\nRabbitMQ/Kafka] <--> MessengerService & CalendarService & DocsService & DriveService & EmailService & TasksService & ApprovalService & VideoService & AdminService
    
    %% WebSocket connections
    WebsocketService <--> MessengerService
    WebsocketService <--> DocsService
    WebsocketService <--> VideoService
    
    %% Real-time collaboration
    DocsService --> CollaborationServer[Yjs Collaboration Server]
    
    %% Video conferencing
    VideoService --> SignalingServer[WebRTC Signaling Server]
    VideoService --> StunTurnServer[STUN/TURN Server]
    VideoService --> MediaServer[SFU Media Server]
    
    %% Backend services connect to databases
    MessengerService & CalendarService & DocsService & DriveService & EmailService & TasksService & ApprovalService & VideoService & AdminService & PlatformService <--> PgBouncer
    
    %% Services using Redis
    MessengerService & WebsocketService & AuthService & VideoService <--> Redis
    
    %% Monitoring & Logging
    Prometheus[Prometheus] -->|Monitor| ApiGateway & AuthService & MessengerService & CalendarService & DocsService & DriveService & EmailService & TasksService & ApprovalService & VideoService & AdminService & PlatformService & PostgreSQL & Redis & MinIO
    Fluentd[Fluentd] -->|Collect Logs| ApiGateway & AuthService & MessengerService & CalendarService & DocsService & DriveService & EmailService & TasksService & ApprovalService & VideoService & AdminService & PlatformService
    Fluentd --> Elasticsearch[Elasticsearch]
    Elasticsearch --> Kibana[Kibana]
    Prometheus --> Grafana[Grafana]
    AlertManager[Alert Manager] --> Prometheus
    
    %% Kubernetes components
    KubeScheduler[Kube Scheduler] -.->|Schedule Pods| IngressController & ApiGateway & AuthService & MessengerService & CalendarService & DocsService & DriveService & EmailService & TasksService & ApprovalService & VideoService & AdminService & PlatformService
    KubeController[Kube Controller] -.->|Manage State| IngressController & ApiGateway & AuthService & MessengerService & CalendarService & DocsService & DriveService & EmailService & TasksService & ApprovalService & VideoService & AdminService & PlatformService
    
    %% Storage Classes
    StorageClass[Storage Classes] -.->|Provision| PostgreSQLPV[PostgreSQL PV] & RedisPV[Redis PV] & MiniOPV[MinIO PV]
    
    %% CI/CD Pipeline
    GitRepo[(Git Repository)] --> CiCdPipeline[CI/CD Pipeline\nGitHub Actions/GitLab CI]
    CiCdPipeline -->|Deploy| KubeAPI[Kubernetes API]
    
    %% Legend
    classDef service fill:#f9f,stroke:#333,stroke-width:2px;
    classDef database fill:#bbf,stroke:#333,stroke-width:2px;
    classDef monitoring fill:#dfd,stroke:#333,stroke-width:2px;
    classDef k8s fill:#fcf,stroke:#333,stroke-width:1px;
    
    class MessengerService,CalendarService,DocsService,DriveService,EmailService,TasksService,ApprovalService,VideoService,AdminService,PlatformService,WebsocketService,AuthService service;
    class PostgreSQL,Redis,MinIO,MessageBroker database;
    class Prometheus,Grafana,Fluentd,Elasticsearch,Kibana,AlertManager monitoring;
    class KubeScheduler,KubeController,KubeAPI,StorageClass k8s;
```

## Container Deployment Architecture

```mermaid
flowchart TD
    subgraph Windows["Windows 10/11 Host"]
        subgraph WSL2["Windows Subsystem for Linux 2"]
            subgraph Docker["Docker Desktop"]
                subgraph K8s["Kubernetes Single-Node Cluster"]
                    subgraph NS1["Namespace: csa-hello-system"]
                        ApiGW[API Gateway Pod]
                        KeyCloakPod[Keycloak Pod]
                        MonitoringPods[Monitoring Pods\nPrometheus/Grafana]
                        LoggingPods[Logging Pods\nEFK Stack]
                        MessageBrokerPod[Message Broker Pod\nRabbitMQ/Kafka]
                    end
                    
                    subgraph NS2["Namespace: csa-hello-databases"]
                        PostgresPod[PostgreSQL StatefulSet]
                        RedisPod[Redis StatefulSet]
                        MinioPod[MinIO StatefulSet]
                        ElasticPod[Elasticsearch Pod]
                    end
                    
                    subgraph NS3["Namespace: csa-hello-apps"]
                        subgraph CoreSvcs["Core Services"]
                            AuthPod[Auth-Service Pod]
                            AdminPod[Admin-Service Pod]
                            PlatformPod[Platform-Service Pod]
                        end
                        
                        subgraph CommSvcs["Communication Services"]
                            MessengerPod[Messenger-Service Pod]
                            WebSocketPod[WebSocket-Service Pod]
                            VideoPod[Video-Service Pod]
                        end
                        
                        subgraph DocsSvcs["Document Services"]
                            DocsPod[Docs-Service Pod]
                            DrivePod[Drive-Service Pod]
                        end
                        
                        subgraph ProdSvcs["Productivity Services"]
                            CalendarPod[Calendar-Service Pod]
                            EmailPod[Email-Service Pod]
                            TasksPod[Tasks-Service Pod]
                            ApprovalPod[Approval-Service Pod]
                        end
                    end
                    
                    subgraph Storage["Persistent Storage"]
                        PVs[Persistent Volumes]
                        PVCs[Persistent Volume Claims]
                        SCs[Storage Classes]
                    end
                    
                    PVs -->|Used by| PostgresPod & RedisPod & MinioPod & ElasticPod
                end
            end
        end
        
        IngressTraffic[Ingress Traffic] -->|Port 443/80| K8s
        
        BackupSystem[Backup System] -->|Backup| PVs
    end
    
    subgraph Clients["Client Devices"]
        WebClient[Web Browsers]
        MobileClient[Mobile Apps]
        DesktopClient[Desktop Apps]
    end
    
    Clients -->|HTTPS| IngressTraffic
    
    subgraph DevOps["DevOps Tools"]
        GitRepo[Git Repository]
        CICD[CI/CD Pipeline]
        Registry[Container Registry]
    end
    
    GitRepo -->|Trigger Build| CICD
    CICD -->|Push Images| Registry
    Registry -->|Pull Images| K8s
    
    %% Legend
    classDef namespace fill:#f9f,stroke:#333,stroke-width:2px;
    classDef pod fill:#bbf,stroke:#333,stroke-width:1px;
    classDef storage fill:#dfd,stroke:#333,stroke-width:1px;
    classDef external fill:#fcf,stroke:#333,stroke-width:1px;
    
    class NS1,NS2,NS3 namespace;
    class PostgresPod,RedisPod,MinioPod,ElasticPod,AuthPod,MessengerPod,DocsPod,CalendarPod,EmailPod,TasksPod,ApprovalPod,VideoPod,AdminPod,PlatformPod,WebSocketPod,DrivePod pod;
    class PVs,PVCs,SCs storage;
    class Clients,DevOps external;
```

## Service Communication Diagram

```mermaid
flowchart LR
    Client[Client Applications] -->|HTTPS| Ingress[Ingress Controller]
    Ingress -->|HTTP| ApiGW[API Gateway]
    
    subgraph AuthFlow["Authentication Flow"]
        ApiGW -->|Authenticate| AuthService
        AuthService -->|Verify| KeycloakService[Keycloak]
        AuthService -->|Cache Token| RedisCache[(Redis)]
    end
    
    subgraph MessagingFlow["Messaging Flow Example"]
        ApiGW -->|Message Request| MessengerService
        MessengerService -->|Store Message| PostgreSQL[(PostgreSQL)]
        MessengerService -->|Publish Event| MessageBroker[Message Broker]
        MessageBroker -->|Notify| WebSocketService
        WebSocketService -->|Real-time Update| Client
    end
    
    subgraph DocumentFlow["Document Collaboration Flow"]
        ApiGW -->|Doc Request| DocsService
        DocsService -->|Load Doc| PostgreSQL
        DocsService -->|Sync Changes| CollabServer[Yjs Collaboration Server]
        CollabServer -->|Real-time Updates| WebSocketService
        DocsService -->|Store Files| MinIO[(MinIO Storage)]
    end
    
    subgraph VideoFlow["Video Conference Flow"]
        ApiGW -->|Conference Request| VideoService
        VideoService -->|Signaling| SignalingServer[WebRTC Signaling]
        SignalingServer -->|Connection Setup| Client
        Client -->|P2P or SFU Media| Client
        VideoService -->|For Large Meetings| MediaServer[SFU Media Server]
    end
    
    %% Legend
    classDef service fill:#f9f,stroke:#333,stroke-width:2px;
    classDef database fill:#bbf,stroke:#333,stroke-width:2px;
    classDef flow fill:#dfd,stroke:#333,stroke-width:1px;
    
    class AuthService,MessengerService,DocsService,VideoService,WebSocketService,CollabServer,SignalingServer,MediaServer service;
    class PostgreSQL,RedisCache,MinIO,MessageBroker database;
    class AuthFlow,MessagingFlow,DocumentFlow,VideoFlow flow;
```

## FastAPI Backend Architecture

```mermaid
flowchart TD
    %% FastAPI Application Structure
    subgraph FastAPI["FastAPI Backend Architecture"]
        subgraph CoreAPI["Core API Structure"]
            App[FastAPI Main App] --> Router[API Router]
            Router --> Auth[Auth Routes]
            Router --> Users[User Routes]
            Router --> Messenger[Messenger Routes]
            Router --> Calendar[Calendar Routes]
            Router --> Docs[Docs Routes]
            Router --> Drive[Drive Routes]
            Router --> Email[Email Routes]
            Router --> Tasks[Tasks Routes]
            Router --> Approval[Approval Routes]
            Router --> Video[Video Routes]
            Router --> Admin[Admin Routes]
            Router --> Platform[Platform API Routes]
        end
        
        subgraph Middleware["Middleware Layer"]
            AuthMiddleware[Authentication Middleware]
            CORSMiddleware[CORS Middleware]
            LoggingMiddleware[Logging Middleware]
            RateLimitMiddleware[Rate Limiting]
            I18nMiddleware[Internationalization]
        end
        
        subgraph Dependencies["Dependencies"]
            AuthDep[Authentication]
            RoleDep[Role & Permissions]
            PaginationDep[Pagination]
            FilteringDep[Filtering]
            ValidationDep[Data Validation]
        end
        
        subgraph Services["Service Layer"]
            AuthService[Auth Service]
            UserService[User Service]
            MessengerService[Messenger Service]
            CalendarService[Calendar Service]
            DocsService[Docs Service]
            DriveService[Drive Service]
            EmailService[Email Service]
            TasksService[Tasks Service]
            ApprovalService[Approval Service]
            VideoService[Video Service]
            AdminService[Admin Service]
            PlatformService[Platform Service]
        end
        
        subgraph Models["Data Models"]
            subgraph Schemas["Pydantic Schemas"]
                RequestSchemas[Request Models]
                ResponseSchemas[Response Models]
                ValidationSchemas[Validation Models]
            end
            
            subgraph DBModels["Database Models"]
                SQLModels[SQLAlchemy Models]
            end
        end
        
        subgraph Database["Database Layer"]
            DBSession[Session Management]
            QueryBuilder[Query Builder]
            Migrations[Alembic Migrations]
        end
        
        subgraph BackgroundTasks["Background Processing"]
            Celery[Celery Workers]
            TaskQueue[Task Queue]
            ScheduledJobs[Scheduled Jobs]
            WebsocketManager[WebSocket Manager]
        end
    end

    %% External Connections
    FastAPI -->|HTTP/WebSockets| Clients[Client Applications]
    Database -->|SQL Queries| PostgreSQL[(PostgreSQL)]
    BackgroundTasks -->|Cache/Pub-Sub| Redis[(Redis)]
    Services -->|Object Storage| MinIO[(MinIO)]
    BackgroundTasks -->|Message Queue| RabbitMQ[(RabbitMQ/Kafka)]
    
    %% Communications between components
    Router --> Dependencies
    Router --> Services
    Services --> Models
    Services --> Database
    Services --> BackgroundTasks
    App --> Middleware
    
    %% Legend
    classDef api fill:#f9f,stroke:#333,stroke-width:2px;
    classDef service fill:#bbf,stroke:#333,stroke-width:2px;
    classDef data fill:#dfd,stroke:#333,stroke-width:2px;
    classDef external fill:#fcf,stroke:#333,stroke-width:1px;
    
    class CoreAPI,Router,Auth,Users,Messenger,Calendar,Docs,Drive,Email,Tasks,Approval,Video,Admin,Platform api;
    class Services,AuthService,UserService,MessengerService,CalendarService,DocsService,DriveService,EmailService,TasksService,ApprovalService,VideoService,AdminService,PlatformService service;
    class Models,Schemas,DBModels,Database data;
    class PostgreSQL,Redis,MinIO,RabbitMQ,Clients external;
```

## FastAPI Service Implementation Details

```mermaid
flowchart TD
    %% Example of a detailed FastAPI Service implementation
    subgraph MessengerService["Messenger Service Implementation"]
        subgraph Routes["API Routes"]
            GetConversations[GET /conversations]
            GetMessages[GET /conversations/{id}/messages]
            PostMessage[POST /conversations/{id}/messages]
            CreateConversation[POST /conversations]
            AddMembers[PUT /conversations/{id}/members]
            GetPresence[GET /users/presence]
            UpdatePresence[PUT /users/presence]
            SearchMessages[GET /messages/search]
        end
        
        subgraph ServiceLayer["Service Functions"]
            CreateMessageSvc[create_message]
            GetMessagesSvc[get_messages]
            CreateConversationSvc[create_conversation]
            GetConversationsSvc[get_conversations]
            ManageMembersSvc[manage_members]
            NotifyUsersSvc[notify_users]
            SearchMessagesSvc[search_messages]
        end
        
        subgraph Models["Data Models"]
            MessageSchema[MessageSchema]
            ConversationSchema[ConversationSchema]
            UserPresenceSchema[UserPresenceSchema]
            MessageDB[MessageDBModel]
            ConversationDB[ConversationDBModel]
            UserPresenceDB[UserPresenceDBModel]
        end
        
        subgraph RealTime["Real-time Functions"]
            WebSocketHandler[WebSocket Handler]
            MessageBroadcaster[Message Broadcaster]
            PresenceUpdater[Presence Updater]
            TypingIndicator[Typing Indicator]
        end
        
        subgraph BackgroundTasks["Background Jobs"]
            ProcessAttachmentJob[Process Attachments]
            StoreMessagesJob[Store Messages]
            GenerateNotificationsJob[Generate Notifications]
            IndexMessagesJob[Index Messages for Search]
        end
    end
    
    %% Connections
    GetConversations --> GetConversationsSvc
    GetMessages --> GetMessagesSvc
    PostMessage --> CreateMessageSvc
    CreateConversation --> CreateConversationSvc
    AddMembers --> ManageMembersSvc
    UpdatePresence --> PresenceUpdater
    SearchMessages --> SearchMessagesSvc
    
    CreateMessageSvc --> MessageSchema
    CreateMessageSvc --> MessageDB
    CreateMessageSvc --> NotifyUsersSvc
    GetMessagesSvc --> MessageDB
    CreateConversationSvc --> ConversationSchema
    CreateConversationSvc --> ConversationDB
    
    NotifyUsersSvc --> WebSocketHandler
    NotifyUsersSvc --> MessageBroadcaster
    PresenceUpdater --> WebSocketHandler
    PostMessage --> ProcessAttachmentJob
    CreateMessageSvc --> StoreMessagesJob
    NotifyUsersSvc --> GenerateNotificationsJob
    StoreMessagesJob --> IndexMessagesJob
    
    %% External connections
    MessageBroadcaster -->|Pub/Sub| Redis[(Redis)]
    StoreMessagesJob -->|Store| PostgreSQL[(PostgreSQL)]
    ProcessAttachmentJob -->|Upload| ObjectStorage[(MinIO)]
    GenerateNotificationsJob -->|Push| NotificationService[Notification Service]
    IndexMessagesJob -->|Index| SearchIndex[(Full-text Search)]
    
    %% Legend
    classDef route fill:#f9f,stroke:#333,stroke-width:2px;
    classDef service fill:#bbf,stroke:#333,stroke-width:2px;
    classDef model fill:#dfd,stroke:#333,stroke-width:2px;
    classDef realtime fill:#fdf,stroke:#333,stroke-width:1px;
    classDef job fill:#ffd,stroke:#333,stroke-width:1px;
    
    class GetConversations,GetMessages,PostMessage,CreateConversation,AddMembers,GetPresence,UpdatePresence,SearchMessages route;
    class CreateMessageSvc,GetMessagesSvc,CreateConversationSvc,GetConversationsSvc,ManageMembersSvc,NotifyUsersSvc,SearchMessagesSvc service;
    class MessageSchema,ConversationSchema,UserPresenceSchema,MessageDB,ConversationDB,UserPresenceDB model;
    class WebSocketHandler,MessageBroadcaster,PresenceUpdater,TypingIndicator realtime;
    class ProcessAttachmentJob,StoreMessagesJob,GenerateNotificationsJob,IndexMessagesJob job;
```

## Containerized FastAPI Microservices Architecture

```mermaid
flowchart LR
    subgraph DockerEnv["Docker Environment"]
        subgraph APIGateway["API Gateway (Traefik/Kong)"]
            GatewayService[Gateway Service]
            AuthHandler[Auth Handler]
            RouteHandler[Route Handler]
            RateLimit[Rate Limiter]
        end
        
        subgraph CoreServices["Core Microservices"]
            AuthService[Auth Service\nFastAPI + JWT]
            UserService[User Service\nFastAPI]
            AdminService[Admin Service\nFastAPI]
        end
        
        subgraph AppServices["Application Microservices"]
            MessengerService[Messenger Service\nFastAPI + WebSockets]
            CalendarService[Calendar Service\nFastAPI]
            DocsService[Docs Service\nFastAPI + Yjs]
            DriveService[Drive Service\nFastAPI]
            EmailService[Email Service\nFastAPI]
            TasksService[Tasks Service\nFastAPI]
            ApprovalService[Approval Service\nFastAPI]
            VideoService[Video Service\nFastAPI + WebRTC]
            PlatformService[Platform Service\nFastAPI]
        end
        
        subgraph DataServices["Data Services"]
            PostgreSQLService[PostgreSQL]
            RedisService[Redis]
            MinIOService[MinIO]
            RabbitMQService[RabbitMQ]
            ElasticsearchService[Elasticsearch]
        end
        
        subgraph SupportServices["Support Services"]
            CeleryService[Celery Workers]
            LoggingService[Logging Service]
            MonitoringService[Monitoring\nPrometheus + Grafana]
        end
    end
    
    %% External Clients
    Clients[Client Apps\nWeb/Mobile/Desktop] -->|HTTPS| APIGateway
    
    %% Gateway to Services
    GatewayService --> AuthService
    GatewayService --> CoreServices
    GatewayService --> AppServices
    
    %% Service Dependencies
    CoreServices -->|Authentication| AuthService
    AppServices -->|Authentication| AuthService
    CoreServices -->|Database| PostgreSQLService
    AppServices -->|Database| PostgreSQLService
    MessengerService & DocsService & VideoService -->|Real-time| RedisService
    DriveService -->|Object Storage| MinIOService
    AppServices --> CoreServices
    AppServices & CoreServices -->|Background Tasks| CeleryService
    CeleryService --> RabbitMQService
    MessengerService & DocsService -->|Search| ElasticsearchService
    
    %% Monitoring
    LoggingService -.->|Collect Logs| CoreServices & AppServices & APIGateway
    MonitoringService -.->|Monitor| CoreServices & AppServices & DataServices & SupportServices
    
    %% Legend
    classDef gateway fill:#f96,stroke:#333,stroke-width:2px;
    classDef core fill:#bbf,stroke:#333,stroke-width:2px;
    classDef app fill:#9cf,stroke:#333,stroke-width:2px;
    classDef data fill:#bd8,stroke:#333,stroke-width:2px;
    classDef support fill:#ffc,stroke:#333,stroke-width:1px;
    classDef client fill:#fcf,stroke:#333,stroke-width:1px;
    
    class APIGateway,GatewayService,AuthHandler,RouteHandler,RateLimit gateway;
    class CoreServices,AuthService,UserService,AdminService core;
    class AppServices,MessengerService,CalendarService,DocsService,DriveService,EmailService,TasksService,ApprovalService,VideoService,PlatformService app;
    class DataServices,PostgreSQLService,RedisService,MinIOService,RabbitMQService,ElasticsearchService data;
    class SupportServices,CeleryService,LoggingService,MonitoringService support;
    class Clients client;
```
