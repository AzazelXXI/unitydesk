# CSA Hello - Enterprise Information & Collaboration System

## Overview

CSA Hello is an all-in-one enterprise information and collaboration management system designed to enhance productivity, optimize information flow, and strengthen team cohesion within organizations of any size. The platform provides a comprehensive suite of integrated modules that replace the need for multiple disconnected tools.

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

CSA Hello is built on a microservices architecture using containerized services managed by Kubernetes. The system is designed for deployment flexibility, supporting both on-premises and cloud environments.

### Key Components

- **Frontend**: Web (React + TypeScript), mobile (Flutter/React Native), and desktop (Tauri + React) clients
- **Backend**: FastAPI microservices running in containers
- **Database**: PostgreSQL for relational data, Redis for caching
- **Storage**: MinIO object storage for files
- **Messaging**: RabbitMQ/Kafka for inter-service communication
- **Real-time**: WebSockets for real-time updates and notifications
- **Video**: WebRTC for video conferencing with signaling and STUN/TURN servers

## Getting Started

### Prerequisites
- Docker Desktop with Kubernetes enabled
- Node.js 18+
- Python 3.9+
- Git

### Installation

1. Clone the repository:
   ```
   git clone https://github.com/your-organization/csa-hello.git
   cd csa-hello
   ```

2. Set up the development environment:
   ```
   ./scripts/setup-dev.sh
   ```

3. Start the development servers:
   ```
   ./scripts/start-dev.sh
   ```

4. Access the application at `http://localhost:3000`

## Technology Stack

- **Backend**: Python 3.9+ with FastAPI
- **Frontend**: React, TypeScript, Zustand/Redux Toolkit
- **Mobile**: Flutter or React Native
- **Desktop**: Tauri with React
- **Database**: PostgreSQL, Redis
- **Storage**: MinIO (S3-compatible)
- **Containerization**: Docker
- **Orchestration**: Kubernetes
- **CI/CD**: GitHub Actions or GitLab CI

## Security Features

- Role-based access control (RBAC)
- JWT authentication with optional MFA
- Keycloak integration for OAuth2/OIDC
- Data encryption in transit and at rest
- Network policies for service-to-service communication

## Development Status

This project is currently in the initial development phase. Last updated: April 8, 2025.

## Contributing

Please read [CONTRIBUTING.md](CONTRIBUTING.md) for details on our code of conduct and the process for submitting pull requests.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Contact

For any inquiries, please reach out to the CSA Hello team at csa.vn.agency@csaapp.com

