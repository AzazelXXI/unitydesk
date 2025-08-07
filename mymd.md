## 1. User Class
The User class represents a user account in the UnityDesk system.

| Field | Type | Description |
|-------|------|-------------|
| userId | String | Unique identifier for each user |
| email | String | User's email address, used for login and communication |
| name | String | User's full name or display name |
| status | UserStatus | Current status of the user (e.g., active, away, offline) |
| roles | List\<String\> | List of roles assigned to the user, determining permissions |

**Methods:**
- `getProfile()`: Retrieves the user's detailed profile information
- `updateProfile()`: Updates the user's profile information
- `changePassword()`: Changes the user's password securely
- `login()`: Authenticates the user into the system
- `logout()`: Ends the user's current session

## 2. Message Class
The Message class represents a single message within a conversation.

| Field | Type | Description |
|-------|------|-------------|
| messageId | String | Unique identifier for each message |
| chatId | String | ID of the chat this message belongs to |
| senderId | String | ID of the user who sent this message |
| content | MessageContent | Content of the message (text, media, etc.) |
| timestamp | DateTime | Time when the message was sent |
| status | MessageStatus | Current status of the message (sent, delivered, read) |

**Methods:**
- `react()`: Adds a reaction to the message
- `edit()`: Modifies the content of the message
- `delete()`: Removes the message from the chat

## 3. Chat Class
The Chat class represents a conversation between multiple users.

| Field | Type | Description |
|-------|------|-------------|
| chatId | String | Unique identifier for each chat |
| type | ChatType | Type of chat (direct, group, channel) |
| name | String | Display name of the chat (group name, etc.) |
| avatar | String | Path or URL to the chat's avatar image |
| members | List\<User\> | List of users participating in this chat |

**Methods:**
- `sendMessage()`: Sends a new message to the chat
- `addMember()`: Adds a user to the chat
- `removeMember()`: Removes a user from the chat

## 4. Project Class
The Project class represents a work project that contains tasks and members.

| Field | Type | Description |
|-------|------|-------------|
| projectId | String | Unique identifier for each project |
| name | String | Name/title of the project |
| description | String | Detailed description of the project |
| members | List\<User\> | Users assigned to this project |

**Methods:**
- `addMember()`: Adds a user to the project team
- `removeMember()`: Removes a user from the project team
- `updateStatus()`: Updates the current status of the project

## 5. Task Class
The Task class represents a work item within a project.

| Field | Type | Description |
|-------|------|-------------|
| taskId | String | Unique identifier for each task |
| title | String | Short title of the task |
| description | String | Detailed description of the task |
| status | TaskStatus | Current status of the task (todo, in progress, done) |
| assigneeId | String | ID of the user assigned to this task |
| creatorId | String | ID of the user who created this task |
| dueDate | DateTime | Deadline for task completion |
| priority | Priority | Importance level of the task (low, medium, high) |

**Methods:**
- `addSubtask()`: Creates a subtask under this task
- `updateStatus()`: Changes the current status of the task
- `assignTo()`: Assigns the task to a specific user
- `addComment()`: Adds a comment to the task

## 6. Document Class
The Document class represents a document stored in the system.

| Field | Type | Description |
|-------|------|-------------|
| documentId | String | Unique identifier for each document |
| ownerId | String | ID of the user who owns this document |
| title | String | Title of the document |
| content | DocumentContent | Content of the document (text, format, etc.) |
| permissions | List\<Permission\> | Access permissions for the document |
| version | int | Current version number of the document |

**Methods:**
- `share()`: Shares the document with other users
- `updateContent()`: Modifies the content of the document
- `createVersion()`: Creates a new version of the document
- `delete()`: Removes the document from the system

## 7. Calendar Class
The Calendar class represents a user's calendar for event management.

| Field | Type | Description |
|-------|------|-------------|
| calendarId | String | Unique identifier for each calendar |
| ownerId | String | ID of the user who owns this calendar |
| name | String | Name/title of the calendar |
| color | String | Color code for calendar display |
| visibility | VisibilityType | Privacy setting for the calendar (public, private, team) |

**Methods:**
- `addEvent()`: Adds a new event to the calendar
- `getEvents()`: Retrieves events within a specific time range
- `shareWith()`: Shares the calendar with other users
- `removeEvent()`: Deletes an event from the calendar
- `changeVisibility()`: Modifies the privacy settings of the calendar

## 8. Event Class
The Event class represents a scheduled event or meeting.

| Field | Type | Description |
|-------|------|-------------|
| eventId | String | Unique identifier for each event |
| calendarId | String | ID of the calendar this event belongs to |
| title | String | Title of the event |
| description | String | Detailed description of the event |
| start | DateTime | Start time of the event |
| end | DateTime | End time of the event |
| location | String | Physical or virtual location of the event |
| attendees | List\<User\> | Users invited to or attending the event |

**Methods:**
- `inviteAttendee()`: Invites a user to the event
- `removeAttendee()`: Removes a user from the event
- `updateTime()`: Changes the start and end times of the event
- `cancel()`: Cancels the event

## Relationships
- User is assigned to Projects and Tasks
- User participates in Chats and sends Messages
- User creates/owns Documents
- User attends Events
- Project contains Tasks
- Chat contains Messages
- Document belongs to Projectas
- d'a
- sf
- \as'f
- as'fas'f
- 