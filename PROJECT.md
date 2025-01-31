# Manufacturing Inventory Management System

A comprehensive system for managing manufacturing operations, inventory, and production planning.

## Overview

This system is designed to handle end-to-end manufacturing operations, from customer orders to production planning and inventory management. It supports complex bill of materials (BOM) structures, technical drawings management, and detailed machine specifications.

## Core Features

#### JWT Implementation Status (Completed)

- Token-based authentication using Simple JWT
- Custom token claims including:
  - User role (from erp_core/models.py lines 56-70)
  - Department memberships
  - Fine-grained permissions
- Token rotation and blacklisting
- Integrated with Django's RBAC system

#### Security Features

- 15-minute access token lifetime
- 1-day refresh token lifetime
- HS256 signing algorithm
- Bearer token authentication
- Automatic token blacklisting after rotation

### 1. Product Management

- Support for different product types (Montaged, Semi, Single)
- Technical drawings version control
- Customer-specific product catalogs
- Detailed product specifications and inventory tracking

### 2. Inventory Control

- Raw materials management
- Real-time stock tracking
- Inventory transaction history
- Multiple units of measure support

### 3. Bill of Materials (BOM)

- Multi-level BOM structure
- Version control for BOMs
- Support for three component types:
  - Semi-finished products
  - Raw materials
  - Manufacturing processes
- Process configuration management

### 4. Production Planning

- Sales order management
- Work order generation and tracking
- Sub-work order breakdown
- Process scheduling and machine allocation

### 5. Machine Management

- Detailed machine specifications
- Status tracking (Available, In Use, Maintenance, Retired)
- Process-machine compatibility
- Machine capacity planning

## Technical Stack

### Backend

- Python (Django)
- PostgreSQL 15+
- Prisma ORM with Django integration
- Redis 7+ for caching

### Frontend

- React 18+
- REST API integration

### Infrastructure

- AWS EC2 for hosting
- AWS RDS for database
- S3-compatible storage for files
- AutoCAD API integration for technical drawings

### DevOps & Security

- GitHub Actions for CI/CD
- Role-Based Access Control (RBAC)
- Row-Level Security (RLS)
- MinIO/AWS S3 for file storage

## Database Schema

The database is structured around several key areas:

1. **Core Entities**

   - Customers
   - Products
   - Technical Drawings

2. **Inventory Management**

   - Raw Materials
   - Units of Measure
   - Inventory Transactions

3. **BOM Structure**

   - BOM Headers
   - BOM Components
   - Process Configurations

4. **Manufacturing**

   - Machines
   - Manufacturing Processes

5. **Sales & Production**
   - Sales Orders
   - Work Orders
   - Sub Work Orders
   - Process Scheduling

## Getting Started

### Prerequisites

- Python 3.10+
- Node.js 18+
- PostgreSQL 15+
- Redis 7+
- AWS CLI (for deployment)
- Docker and Docker Compose (optional)

### Local Development Setup

1. **Clone the Repository**

   ```bash
   git clone https://github.com/your-org/manufacturing-inventory
   cd manufacturing-inventory
   ```

2. **Backend Setup**

   ```bash
   # Create and activate virtual environment
   python -m venv venv
   source venv/bin/activate  # On Windows: .\venv\Scripts\activate

   # Install dependencies
   pip install -r requirements.txt

   # Set up environment variables
   cp .env.example .env
   # Edit .env with your local configuration

   # Initialize database
   python manage.py migrate

   # Create superuser
   python manage.py createsuperuser

   # Start development server
   python manage.py runserver
   ```

3. **Frontend Setup**

   ```bash
   cd frontend
   npm install
   npm start
   ```

4. **Local Services**
   - Ensure PostgreSQL is running on port 5432
   - Start Redis server
   - For file storage, either:
     - Configure AWS S3 credentials in `.env`
     - Or set up MinIO locally for S3-compatible storage

### Development Guidelines

- Follow PEP 8 style guide for Python code
- Use ESLint and Prettier for JavaScript/React code
- Write tests for new features
- Update documentation when adding new features
- Use feature branches and pull requests for changes

### Deployment

#### Production Setup

1. **AWS Infrastructure**

   - Set up EC2 instance (t3.large or better recommended)
   - Configure RDS PostgreSQL instance
   - Create S3 bucket for file storage
   - Set up Redis through ElastiCache

2. **CI/CD Pipeline**

   - Merges to main branch trigger GitHub Actions
   - Automated tests run on pull requests
   - Successful builds deploy to staging
   - Manual approval required for production deployment

3. **Environment Configuration**

   - Set up production environment variables
   - Configure SSL certificates
   - Set up domain and DNS records
   - Initialize monitoring and logging

4. **Deployment Commands**

   ```bash
   # Build frontend
   cd frontend
   npm run build

   # Deploy backend
   python manage.py collectstatic
   python manage.py migrate
   gunicorn wsgi:application
   ```

### Monitoring and Maintenance

- Use AWS CloudWatch for monitoring
- Set up error tracking with Sentry
- Configure backup schedules for database
- Monitor system resources and scaling needs

## Contributing

(To be added: Contribution guidelines, coding standards, and PR process)

## License

MIT
