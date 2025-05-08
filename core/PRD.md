# Core Module - Product Requirements Document

## Overview

The Core module serves as the foundation of the ERP system, providing essential functionality that supports all other modules. It manages user authentication, authorization, user profiles, departments, and system-wide features.

## Features

### User Management

- **User Authentication**: Email-based authentication with secure password handling
- **Role-Based Access Control**: Four roles (Admin, Engineer, Operator, Viewer) with progressive permissions
- **User Profiles**: Extended user information including department association, employee ID, and contact information
- **Department Management**: Organization of users into departments with hierarchy support

### Customer Management

- **Customer Records**: Store and manage customer information with unique codes
- **Data Validation**: Business rules for customer data entry including code formatting rules

### Audit System

- **Change Tracking**: Records all CRUD operations on important entities
- **Audit Trail**: Maintains who changed what and when for compliance and debugging

### Permissions Framework

- **Granular Permission Controls**: Code-based permission system
- **Role-Permission Assignments**: Matrix of roles and their associated permissions

### Core Services

- **Dashboard**: Centralized view of key metrics and system status
- **Import/Export**: Functionality for data migration and reporting
- **Email**: System email capabilities for notifications
- **Notifications**: In-app and external notification system

## Technical Requirements

### Models

- `User`: Extended Django user with role-based controls
- `UserProfile`: Extended user information
- `Department`: Organizational structure
- `DepartmentMembership`: Many-to-many relationship between users and departments
- `Customer`: Customer information
- `AuditLog`: System-wide change tracking
- `Permission`: Available system permissions
- `RolePermission`: Role to permission mappings

### Middleware

- Authentication checks
- Audit logging
- Performance monitoring

### Utilities

- Reusable helper functions
- System-wide constants

## Integration Points

- Authentication for all other modules
- User information accessible to all modules
- Customer data used by Sales, Manufacturing, and other modules
- Audit system used by all other modules

## Security Considerations

- Password policy enforcement
- Role-based access restrictions
- Input validation and sanitization
- Token management
- Session security

## Future Enhancements

- Two-factor authentication
- Single sign-on integration
- Enhanced user activity tracking
- Advanced reporting capabilities
