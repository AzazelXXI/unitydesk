<!-- filepath: d:\projects\CSA\csa-hello\.docs\modules\customer_service\module_diagram.md -->
# Customer Service Module Diagrams

## Component Architecture

```mermaid
graph TD
    subgraph Frontend
        TicketUI["Ticket UI<br>Customer Ticket Interface"]
        WorkflowUI["Workflow UI<br>Step Management"]
        QuoteUI["Quote UI<br>Quote Generation"]
        DashboardUI["Dashboard UI<br>Service Analytics"]
    end
    
    subgraph Backend
        CSController["CustomerServiceController<br>Core Business Logic"]
        TicketService["TicketService<br>Ticket Operations"]
        WorkflowService["WorkflowService<br>Step Management"]
        QuoteService["QuoteService<br>Quote Generation"]
        AssignmentService["AssignmentService<br>Staff Assignment"]
    end
    
    subgraph Database
        TicketsDB[(ServiceTickets)]
        StepsDB[(ServiceSteps)]
        TicketStepDB[(TicketSteps)]
        QuotesDB[(QuoteDocuments)]
    end
    
    TicketUI --> CSController
    WorkflowUI --> WorkflowService
    QuoteUI --> QuoteService
    DashboardUI --> CSController
    
    CSController --> TicketService
    CSController --> WorkflowService
    CSController --> QuoteService
    WorkflowService --> AssignmentService
    
    TicketService --> TicketsDB
    WorkflowService --> StepsDB
    WorkflowService --> TicketStepDB
    QuoteService --> QuotesDB
    
    subgraph ExternalSystems
        TaskSystem["Task Module<br>Staff Task Assignment"]
        NotificationSystem["Notification System<br>Alerts & Reminders"]
        PDFGenerator["PDF Generator<br>Quote Documents"]
        ExcelGenerator["Excel Generator<br>Quote Spreadsheets"]
    end
    
    AssignmentService --> TaskSystem
    WorkflowService --> NotificationSystem
    QuoteService --> PDFGenerator
    QuoteService --> ExcelGenerator
```

## Ticket Workflow Sequence

```mermaid
sequenceDiagram
    participant Client as Client
    participant Sales as Sales Rep
    participant System as CS System
    participant Step1 as Step 1 Staff
    participant Step2 as Step 2 Staff
    
    Client->>Sales: Request Service
    Sales->>System: Create Service Ticket
    System->>System: Generate Ticket Code (YYMM-XXXX)
    System->>System: Initialize First Step
    System->>Sales: Return Ticket Details
    Sales->>Client: Create & Send Quote
    Client->>Sales: Approve Quote
    Sales->>System: Update Ticket Status (IN_PROGRESS)
    System->>Step1: Assign First Step Task
    Step1->>System: Complete Step
    System->>System: Calculate Step Cost
    System->>System: Update Ticket Total Price
    System->>Step2: Auto-assign Next Step
    Step2->>System: Complete Step
    System->>System: Update Ticket Status (COMPLETED)
    System->>Sales: Notify Completion
    Sales->>Client: Deliver Service Results
```

## Multi-Step Service Flow

```mermaid
flowchart LR
    Init([Ticket Creation])
    Quote[Quote Generation]
    Approval{Client Approval}
    Step1(Step 1: Initial Service)
    Step2(Step 2: Main Delivery)
    Step3(Step 3: Quality Check)
    Step4(Step 4: Final Delivery)
    Complete([Service Complete])
    
    Init --> Quote
    Quote --> Approval
    Approval -->|Yes| Step1
    Approval -->|No| Revised[Revised Quote]
    Revised --> Approval
    
    Step1 --> Step1Status{Completed?}
    Step1Status -->|Yes| Step2
    Step1Status -->|No| Step1
    
    Step2 --> Step2Status{Completed?}
    Step2Status -->|Yes| Step3
    Step2Status -->|No| Step2
    
    Step3 --> QualityCheck{Passes Check?}
    QualityCheck -->|Yes| Step4
    QualityCheck -->|No| RevisionNeeded[Revision Required]
    RevisionNeeded --> Step2
    
    Step4 --> Complete
    
    classDef start fill:#d4f1f9,stroke:#05a4d2
    classDef process fill:#c9e7dd,stroke:#0ca789
    classDef decision fill:#ffe6cc,stroke:#ff9933
    classDef end fill:#f9d1d1,stroke:#e06666
    
    class Init,Quote start
    class Step1,Step2,Step3,Step4,Revised process
    class Approval,Step1Status,Step2Status,QualityCheck decision
    class Complete end
```

## Ticket Status State Diagram

```mermaid
stateDiagram-v2
    [*] --> NEW: Ticket Created
    
    NEW --> IN_PROGRESS: Client Approves
    NEW --> CANCELLED: Client Declines
    
    IN_PROGRESS --> ON_HOLD: Issues Encountered
    ON_HOLD --> IN_PROGRESS: Issues Resolved
    
    IN_PROGRESS --> COMPLETED: All Steps Finished
    
    COMPLETED --> [*]
    CANCELLED --> [*]
    
    state IN_PROGRESS {
        [*] --> Step1
        Step1 --> Step2: Complete Step 1
        Step2 --> Step3: Complete Step 2
        Step3 --> [*]: Complete Step 3
    }
```
