# UnityDesk
## 1. Introduction
- UnityDesk is a Web Application designed to provide services like Project Management, Task Management, Storage, Video-Calling, Messages, Calendar.
- It is built using ReactJS, NodeJS, ExpressJS and PostgreSQL.
  
## 2. Purpose
- Building an all-in-one platform for managing projects, tasks, and communication.
- Improve productivity by integrating various tools into a single application.
- Facilitate collaboration through features like video calling and messaging.
- Provide a strong solution instead of using multiple applications for different tasks.
- Digital workspace for teams to collaborate effectively.
## 3. Features
- **Project Management**: Create and manage projects with tasks, deadlines, and team members.
- **Task Management**: Assign tasks, set priorities, and track progress.
- **Storage**: Securely store and share files within the application.
- **Video Calling**: Integrated video calling for real-time communication.
- **Messages**: In-app messaging for quick communication between team members.
- **Calendar**: Schedule events, deadlines, and meetings with a built-in calendar.
## 4. Functionality
- **User**:
  - User Profile: Manage personal information and settings.
  - Project Creation: Create new projects and invite team members.
  - Task Assignment: Assign tasks to team members and set deadlines.
  - File Management: Upload, download, and share files securely.
  - Messaging: Send and receive messages within the application.
  - Video Calls: Initiate and join video calls with team members.
  - Calendar: View and manage personal and project-related events.
  - Role-Based Access Control: Different roles with specific permissions.
    - **User**: Basic access to projects and tasks.
    - **Manager**: Additional permissions to manage tasks and projects.
    - **Admin**: Full access to all features and settings.
- **Manager**:
  - Task Management: Oversee task assignments and progress.
  - Project Oversight: Monitor project status and team performance.
  - Team Collaboration: Facilitate communication and collaboration among team members.
  - Reporting: Generate reports on project and task progress.
- **Admin**:
  - User Management: Manage user accounts, roles, and permissions.
  - Project Oversight: Monitor all projects and tasks across the platform.
  - System Settings: Configure application settings and manage integrations.
- **Team Collaboration**:
  - Real-time Updates: Receive notifications for task updates, messages, and events.
  - Collaboration Tools: Use shared documents and resources for team collaboration.
- **Security**: Ensure data security with user authentication and authorization.
- **Performance**: Optimize application performance for a smooth user experience.
- **Scalability**: Designed to handle a growing number of users and projects. 
## 5. Technologies Used
- **Frontend**: ReactJS for building the user interface.
- **Backend**: NodeJS and ExpressJS for server-side logic and API development.
- **Database**: PostgreSQL for data storage and management and Redis for caching.
- **Authentication**: JWT (JSON Web Tokens) for secure user authentication.
- **Real-time Communication**: WebSocket for real-time messaging and notifications.
- **File Storage**: Integration with cloud storage solutions for file management.
## 6. Installation and Setup
- Clone the repository from GitHub.
- Install dependencies using npm or yarn.
- Set up environment variables for database connection and other configurations.
- Run the application using npm start or yarn start.
- Access the application through a web browser at `http://localhost:3000`.
