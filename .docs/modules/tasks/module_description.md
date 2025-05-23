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

## 4. Industry-Specific Requirements

### Marketing Team Requirements

- Content calendar with editorial workflow
- Campaign performance tracking (CTR, ROI, conversion rates)
- Social media post scheduling and automation
- Lead scoring and nurturing pipeline
- A/B testing management for campaigns
- Brand asset library and version control
- Influencer collaboration tracking
- Marketing automation integration

### Agency Requirements

- Client billing and time tracking
- Multi-client project segregation
- Proposal and contract management
- Client approval workflows
- Retainer vs project-based billing
- Statement of Work (SOW) templates
- Client communication portal
- Resource allocation across multiple clients

### IT Team Requirements

- Bug tracking with severity/priority levels
- Code review and approval workflows
- Sprint planning and retrospectives
- Technical debt tracking
- CI/CD pipeline integration
- Infrastructure monitoring alerts
- Security compliance checklists
- Documentation version control

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

---

## Scenarios

### A description of the starting situation:

A user named Hao and his group have a marketing project and just receives an email about the project and gets agreement from the administrator of his company. Hao and his group signed in successfully into the system to manage projects and tasks.

### A description of the main flow of events:

1. **Access to the Dashboard** for users to control the project. Hao created a project and gave it a name. Then assigned tasks and due dates for his group members.
2. **Tracking Progress.** The system will list all of the projects that Hao had created before, he will choose the one that he wants to check and see the latest progress that include the progress of task completion, timelines, project status, comments, documents that his group members attached to the task.
3. **Approval** after checking carefully all of the tasks contain a finished tag or status that fit with his requirements then he could comment to agree like "Accept and the approval" to ensure that his group members could know that he approved of what they did.
4. After the approval that the project is done Hao could set the project status into finished and everything included to that project will be frozen except the recurring task.

### A description of what can go wrong:

- The attached document could be an error and Hao can not see or watch. Make Hao could not make a decision about approval.
- The system got in trouble and made the application slowdown. It will slow the whole progress.
- System not showing the latest tracking progress. Will make Hao think that his group members did not do anything that will lead to internal problems or misunderstanding.

### Information about other concurrent activities:

- While Hao is tracking the progress and tasks that are assigned. His group members could comment, share and upload files to the tasks that they are in process.
- A developer on his way to develop a function in the system or an application in the system.

### A description of the state when the scenario finishes:

- Hao could still sign-in into the system to check the project and he could remove, archive or create to start a new project while the old one is still there.
- Project status after finishing will affect all of the tasks that involve that project except the recurring/daily tasks.
