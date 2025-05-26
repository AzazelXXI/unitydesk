# CSA-HELLO: Module Requirements Specification

---

**Members:**

- Hoàng Chí Trung - 2280603437
- Nguyễn Vũ Anh Hào - 2280600848
- Nguyễn Minh Duy - 2280600471

**Topic:** Projects/Tasks Management for Office Company (Marketing, Agency, IT)

---

# Requirements

## 1. Task Module

### Functionality Requirements

- Create, read, update, and delete tasks
- Set task titles, descriptions, priority levels, and status
- Assign tasks to specific users or teams
- Add due dates for tasks
- Support attachments and comments on tasks
- Enable task categorization and tagging
- Set task dependencies (blocking/blocked by)
- Support recurring tasks

### Non-functional Requirements

- Intuitive task creation interface
- Drag-and-drop prioritization
- Clear visual status indicators
- Easy filtering and sorting options
- Notification system for task updates

## 2. Calendar Module

### Functionality Requirements

- Daily, weekly, monthly, and agenda views
- Create and manage events with start/end times
- Support for recurring events
- Set reminders and notifications
- Team calendar sharing and permissions
- Color-coding for different event types
- Resource scheduling capabilities
- Export/import calendar data (iCal format)

### Non-functional Requirements

- Clean, intuitive calendar interface
- Easy event creation with quick-add functionality
- Drag-and-drop event scheduling and duration adjustment
- Customizable view preferences

## 3. Project Module

### Functionality Requirements

- Create and manage projects with descriptions and objectives
- Set project start/end dates and milestones
- Assign team members and define roles
- Track project progress and status
- Create project templates for reuse
- Support for project documentation
- Budget and resource allocation tracking
- Risk management capabilities

### Non-functional Requirements

- Dashboard overview of project status
- Gantt chart visualization option
- Customizable project views (Kanban, list, timeline)
- Easy navigation between projects
- Progress indicators and reporting tools

## 4. Target Audience
- Marketing teams:
    - Content creation tasks
    - Campaign management
    - Social media scheduling
    - Event planning
    - Basic approval workflows
    - Task comments
- Agency teams:
    - Client project management
    - Task delegation and tracking
    - Resource allocation
    - Time tracking for billable hours
    - Reporting and analytics for client projects
- IT teams:
    - Software development tasks
    - Bug tracking and issue resolution
    - Sprint planning and backlog management
    - Deployment scheduling
    - Documentation and knowledge base management

---

## Cross-Module Relationships

### Task-Project Relationship

- Tasks belong to projects (required or optional)
- Tasks inherit project properties (team, category)
- Tasks contribute to project progress metrics
- Project filters apply to task views
- Bulk task operations within projects

### Project-Calendar Relationship

- Project timeline visible on calendar
- Project milestones marked as special events
- Project deadlines trigger calendar reminders
- Team availability viewable against project timeline
- Resource allocation visible on calendar views

### Task-Calendar Relationship

- Tasks appear on calendar based on due dates
- Task work sessions can be scheduled on calendar
- Calendar events can generate tasks
- Completion of calendar events can update task status
- Time conflicts highlighted between tasks and events

---

## Stakeholder Analysis

### Project Managers

**Responsibilities:**

- Project Management: Create, edit, delete projects and define scope
- Planning: Build timelines, set milestones and deadlines
- Task Assignment: Create and assign tasks to appropriate team members
- Progress Tracking: Monitor completion rates and update project status
- Resource Management: Allocate and adjust resources across projects
- Risk Management: Identify, assess, and reduce risks throughout projects
- Reporting: Create and share performance and progress reports

**System Interactions:**

- Use Gantt charts to manage timelines
- Apply project templates for quick project initialization
- Create and analyze project performance reports
- Manage project budgets and expenses
- Track resource allocation on calendars

### Team Members

**Responsibilities:**

- Task Management: View, accept, and update status of assigned tasks
- Time Tracking: Record and report time spent on each task
- Collaboration: Add comments, share documents, and provide feedback on tasks
- Personal Planning: Organize personal work based on priorities and deadlines
- Issue Reporting: Report obstacles or dependencies affecting task progress

**System Interactions:**

- Use task filters to view assigned tasks
- Update task status (todo, in progress, review, done)
- Use time tracking to record working hours
- Attach documents to tasks
- Receive notifications when tasks or projects are updated

### Clients/Members

**Responsibilities:**

- Progress Tracking: View reports and updates about their projects
- Approval: Review and approve deliverables or milestones
- Feedback Provision: Provide feedback on completed tasks
- Change Requests: Propose changes or adjustments to project scope

**System Interactions:**

- Limited access to dashboard overview of project status
- View shared progress reports
- Receive notifications about important milestones
- Approve or reject deliverables