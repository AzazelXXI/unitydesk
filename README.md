# UnityDesk - Enterprise Information & Collaboration System

## Overview

UnityDesk is an all-in-one enterprise information and collaboration management system designed to enhance productivity, optimize information flow, and strengthen team cohesion within organizations of any size. The platform provides a comprehensive suite of integrated modules that replace the need for multiple disconnected tools.

## Core Modules

- **Messenger**: Real-time communication with chat, voice/video calls, screen sharing, and presence indicators
- **Calendar**: Personal and team scheduling with resource booking and meeting management
- **Docs**: Collaborative document editing with real-time co-authoring for text documents, spreadsheets, and presentations
- **Cloud Drive**: Secure file storage, sharing, and synchronization across devices
- **Email**: Integrated email management within the same interface
- **Tasks/Projects**: Task assignment, progress tracking, and project management with multiple views
- **Approvals**: Customizable workflows for internal approval processes
- **Video Conference**: High-quality video meetings with screen sharing, recording, and whiteboard features
- **Admin Console**: User and group management, security settings, and system monitoring
- **Open Platform**: APIs and SDKs for third-party integrations and custom applications

## Architecture

UnityDesk is built on a microservices architecture using containerized services managed by Kubernetes. The system is designed for deployment flexibility, supporting both on-premises and cloud environments.

### Key Components

- **Frontend**: Jinja2 templates (server-rendered via FastAPI), JavaScript (vanilla and Bootstrap)
- **Backend**: FastAPI microservices
- **Database**: PostgreSQL for relational data  
- **Real-time**: WebSockets for real-time updates and notifications
- **Video**: WebRTC for video conferencing with signaling and STUN/TURN servers

## Getting Started

### Prerequisites
- Python 3.13+
- PostgreSQL 17
- Git
- make

### Installation

1. Clone the repository:
   ```
   git clone https://github.com/your-organization/unitydesk.git
   cd unitydesk
   ```

2. Create a virtual environment:
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```
   pip install -r requirements.in
   ```

4. Apply database migrations:
   ```
   alembic upgrade head
   ```

5. Run the application:
   ```
   make run
   ```

6. Access the application at `http://localhost:8000`

## Security Features

- Role-based access control (RBAC)
- JWT authentication with optional MFA
- Keycloak integration for OAuth2/OIDC
- Data encryption in transit and at rest
- Network policies for service-to-service communication