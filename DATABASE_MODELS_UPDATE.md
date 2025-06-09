# Database Models Update Summary

## Overview

The database models have been completely updated to align with the Class Diagram and module description for the CSA-HELLO IT project management system.

## Major Changes Completed

### 1. ID Field Migration

- **Converted all UUID primary keys to Integer auto-increment** for better performance and easier debugging
- Updated all foreign key relationships accordingly

### 2. User Model Updates

- **Removed project_id foreign key** from User model (was causing circular dependency)
- **Implemented polymorphic inheritance** for user roles:
  - ProjectManager
  - TeamLeader
  - Developer
  - Tester
  - Designer
  - SystemAdmin
- **Updated UserStatusEnum** with proper default (OFFLINE)
- **Added proper relationships** for project membership via association table

### 3. New Models Added

- **Comment**: For task comments with author and task relationships
- **Attachment**: For file uploads with support for both tasks and projects
- **Milestone**: For project milestones with status tracking
- **Risk**: For project risk management with priority and impact scoring
- **Notification**: For user notifications with type classification

### 4. Task Model Enhancements

- **Added priority field** with enum (LOW, MEDIUM, HIGH, URGENT)
- **Added tags field** for task categorization
- **Added task dependencies** - many-to-many self-relationship
- **Added multiple assignees** support via association table
- **Enhanced time tracking** with estimated_hours and actual_hours
- **Added proper date fields** (start_date, due_date, completed_date)

### 5. Project Model Enhancements

- **Added team_members relationship** via project_members association table
- **Added milestones, risks, documents relationships**
- **Enhanced project management capabilities**

### 6. Association Tables Updates

- **project_members**: Replaces team concept, users are directly members of projects
- **task_assignees**: Multiple users can be assigned to tasks
- **task_attachments**: Tasks can have multiple attachments
- **task_dependencies**: Tasks can depend on other tasks

### 7. Removed Models

- **Team model**: Replaced with direct project membership
- **team_members association**: Consolidated into project_members

## Database Schema Migration

A new migration file has been generated:

```
migrations/versions/a051a586f8b6_update_models_to_integer_ids_and_add_.py
```

### To apply the migration:

```powershell
python -m alembic upgrade head
```

## Updated Models Structure

### Core Entities

1. **User** (with polymorphic inheritance for roles)
2. **Project** (with team members, milestones, risks)
3. **Task** (with assignees, dependencies, attachments, comments)
4. **Comment** (for task discussions)
5. **Attachment** (for file management)
6. **Milestone** (for project milestones)
7. **Risk** (for risk management)
8. **Notification** (for user notifications)
9. **Calendar** & **Event** (for scheduling)

### Key Relationships

- **User ↔ Project**: Many-to-many via project_members (owner + team members)
- **User ↔ Task**: Many-to-many via task_assignees (multiple assignees per task)
- **Task ↔ Task**: Many-to-many via task_dependencies (task dependencies)
- **Task ↔ Attachment**: Many-to-many via task_attachments
- **Project → Milestone**: One-to-many
- **Project → Risk**: One-to-many
- **User → Comment**: One-to-many (author)
- **Task → Comment**: One-to-many

## Files Updated

- `src/models/user.py` - Polymorphic inheritance, removed project_id FK
- `src/models/project.py` - Enhanced relationships, Integer IDs
- `src/models/task.py` - Priority, tags, dependencies, multiple assignees
- `src/models/association_tables.py` - New association tables with Integer FKs
- `src/models/calendar.py` - Integer IDs
- `src/models/event.py` - Integer IDs
- `migrations/env.py` - Updated imports for new models

## Files Created

- `src/models/comment.py` - New Comment model
- `src/models/attachment.py` - New Attachment model
- `src/models/milestone.py` - New Milestone model
- `src/models/risk.py` - New Risk model
- `src/models/notification.py` - New Notification model

## Files Removed

- `src/models/team.py` - Replaced with project_members association

## Next Steps

1. **Apply the migration** to update the database schema
2. **Update existing controllers and views** to work with new model structure
3. **Update API endpoints** to handle new relationships and fields
4. **Update frontend** to support new features (dependencies, multiple assignees, etc.)
5. **Add data validation** for new enum fields
6. **Test the migration** thoroughly before deploying to production

## Notes

- All models now use Integer auto-increment primary keys for better performance
- Polymorphic inheritance is properly configured for user roles
- Task dependencies enable proper project planning workflows
- Multiple assignees per task support collaborative work
- Risk management and milestone tracking enhance project management capabilities
