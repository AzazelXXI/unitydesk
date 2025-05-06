# Task, Calendar, and Project Modules - Diagrams

This document contains visual representations of the requirements and relationships between the Task, Calendar, and Project modules as specified in the requirements.

## Module Relationships Diagram

```mermaid
graph TD
    %% Main Modules
    Task([Task Module])
    Calendar([Calendar Module])
    Project([Project Module])

    %% Relationships
    Task -- "Appears on" --> Calendar
    Task -- "Belongs to" --> Project
    Project -- "Has timeline on" --> Calendar
    Calendar -- "Creates" --> Task
    Project -- "Calculates progress from" --> Task
    Calendar -- "Displays milestones from" --> Project

    %% Styling
    classDef module fill:,stroke:#333,stroke-width:2px;
    class Task,Calendar,Project module;
```

## Entity Relationship Diagram

```mermaid
erDiagram
    USER {
        string userId
        string name
        string email
    }

    TASK {
        string taskId
        string title
        string description
        enum status
        string assigneeId
        date dueDate
        enum priority
        boolean recurring
    }

    PROJECT {
        string projectId
        string name
        string description
        date startDate
        date endDate
        float progress
    }

    EVENT {
        string eventId
        string title
        datetime startTime
        datetime endTime
        string location
        boolean isRecurring
    }

    MILESTONE {
        string milestoneId
        string projectId
        string name
        date dueDate
    }

    USER ||--o{ TASK : "is assigned to"
    USER ||--o{ PROJECT : "is member of"
    PROJECT ||--o{ TASK : "contains"
    PROJECT ||--o{ MILESTONE : "has"
    TASK }|--|| EVENT : "appears as"
    MILESTONE }|--|| EVENT : "appears as"
    TASK }|--o{ TASK : "depends on"
```

## Task Module Class Diagram

```mermaid
classDiagram
    class Task {
        +taskId: String
        +title: String
        +description: String
        +status: TaskStatus
        +assigneeId: String
        +creatorId: String
        +dueDate: DateTime
        +priority: Priority
        +tags: List~Tag~
        +timeEstimate: Duration
        +timeSpent: Duration
        +dependencies: List~Task~
        +recurringRule: RecurringRule
        +createTask()
        +updateTask()
        +deleteTask()
        +changeStatus()
        +addComment()
        +attachFile()
        +trackTime()
        +addDependency()
    }

    class TaskComment {
        +commentId: String
        +taskId: String
        +authorId: String
        +content: String
        +timestamp: DateTime
        +addComment()
        +editComment()
        +deleteComment()
    }

    class TaskAttachment {
        +attachmentId: String
        +taskId: String
        +fileName: String
        +fileType: String
        +fileSize: Number
        +uploaderId: String
        +uploadFile()
        +downloadFile()
        +deleteAttachment()
    }

    class RecurringRule {
        +ruleId: String
        +frequency: String
        +interval: Number
        +endDate: DateTime
        +calculateNextOccurrence()
    }

    Task "1" -- "*" TaskComment: has
    Task "1" -- "*" TaskAttachment: has
    Task "1" -- "0..1" RecurringRule: follows
    Task "*" -- "*" Task: depends on
```

## Calendar Module Class Diagram

```mermaid
classDiagram
    class Calendar {
        +calendarId: String
        +ownerId: String
        +name: String
        +color: String
        +visibility: String
        +createCalendar()
        +updateCalendar()
        +deleteCalendar()
        +shareCalendar()
    }

    class Event {
        +eventId: String
        +calendarId: String
        +title: String
        +description: String
        +startTime: DateTime
        +endTime: DateTime
        +location: String
        +isRecurring: Boolean
        +reminderTime: DateTime
        +createEvent()
        +updateEvent()
        +deleteEvent()
        +setReminder()
        +convertToTask()
    }

    class RecurringPattern {
        +patternId: String
        +eventId: String
        +frequency: String
        +interval: Number
        +endDate: DateTime
        +generateOccurrences()
    }

    class CalendarShare {
        +shareId: String
        +calendarId: String
        +userId: String
        +permissionLevel: String
        +shareCalendar()
        +revokeAccess()
        +updatePermission()
    }

    Calendar "1" -- "*" Event: contains
    Event "1" -- "0..1" RecurringPattern: follows
    Calendar "1" -- "*" CalendarShare: has
```

## Project Module Class Diagram

```mermaid
classDiagram
    class Project {
        +projectId: String
        +name: String
        +description: String
        +startDate: DateTime
        +endDate: DateTime
        +status: ProjectStatus
        +progress: Float
        +createProject()
        +updateProject()
        +deleteProject()
        +calculateProgress()
        +addTeamMember()
    }

    class Milestone {
        +milestoneId: String
        +projectId: String
        +name: String
        +description: String
        +dueDate: DateTime
        +status: MilestoneStatus
        +createMilestone()
        +updateMilestone()
        +deleteMilestone()
    }

    class ProjectMember {
        +memberId: String
        +projectId: String
        +userId: String
        +role: String
        +joinDate: DateTime
        +addMember()
        +removeMember()
        +changeRole()
    }

    class Risk {
        +riskId: String
        +projectId: String
        +description: String
        +probability: String
        +impact: String
        +mitigationPlan: String
        +addRisk()
        +updateRisk()
        +deleteRisk()
    }

    Project "1" -- "*" Milestone: contains
    Project "1" -- "*" ProjectMember: has
    Project "1" -- "*" Risk: manages
    Project "1" -- "*" Task: contains
```

## User Flow Diagram

```mermaid
flowchart TD
    Start([Start]) --> CreateProject[Create New Project]
    CreateProject --> SetProjectDetails[Set Project Details]
    SetProjectDetails --> AddTeamMembers[Add Team Members]
    AddTeamMembers --> CreateMilestones[Create Project Milestones]
    CreateMilestones --> ViewProjectOnCalendar[View Project Timeline on Calendar]
    ViewProjectOnCalendar --> CreateTask[Create New Task]
    CreateTask --> AssignTask[Assign Task to Team Member]
    AssignTask --> SetDueDate[Set Task Due Date]
    SetDueDate --> ViewTaskOnCalendar[View Task on Calendar]
    ViewTaskOnCalendar --> CompleteTask[Complete Task]
    CompleteTask --> UpdateProjectProgress[Update Project Progress]
    UpdateProjectProgress --> ProjectComplete{Is Project Complete?}
    ProjectComplete -- Yes --> End([End])
    ProjectComplete -- No --> CreateTask
```

## Integration Points Visualization

```mermaid
graph TD
    subgraph TaskModule[Task Module]
        CreateTask[Create Task]
        UpdateTask[Update Task Status]
        AssignTask[Assign Task]
    end

    subgraph CalendarModule[Calendar Module]
        ShowEvents[Show Events]
        CreateEvent[Create Event]
        SetReminder[Set Reminder]
    end

    subgraph ProjectModule[Project Module]
        TrackProgress[Track Progress]
        ManageMilestones[Manage Milestones]
        AssignTeam[Assign Team]
    end

    %% Task to Calendar Integration
    CreateTask --> |Due Date Appears on Calendar| ShowEvents
    AssignTask --> |Assigned to User Calendar| ShowEvents
    CreateEvent --> |Can Convert to Task| CreateTask

    %% Task to Project Integration
    CreateTask --> |Task Added to Project| TrackProgress
    UpdateTask --> |Updates Project Progress| TrackProgress

    %% Project to Calendar Integration
    ManageMilestones --> |Milestone Appears on Calendar| ShowEvents

    %% Styling
    classDef module fill:,stroke:#333,stroke-width:2px;
    class TaskModule,CalendarModule,ProjectModule module;
```
