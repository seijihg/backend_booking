# AWS Fargate Deployment Plan for Django Booking API

## Executive Summary
This document outlines a comprehensive deployment strategy for migrating the Django Booking API to AWS using Fargate for container orchestration. The plan ensures high availability, scalability, security, and cost-effectiveness.

## Architecture Overview

### Current Application Stack
- **Framework**: Django 5.2
- **Database**: PostgreSQL (via DATABASE_URL)
- **Cache/Queue**: Redis (for Dramatiq background tasks)
- **Web Server**: Gunicorn
- **Authentication**: JWT with django-allauth
- **External Services**: Twilio SMS
- **Apps**: user, salon, address, appointment

### Target AWS Architecture
```
┌─────────────────────────────────────────────────────────────────┐
│                        Route 53 (DNS)                           │
└────────────────────────────┬────────────────────────────────────┘
                             │
┌────────────────────────────▼────────────────────────────────────┐
│                    Application Load Balancer                     │
│                         (HTTPS/SSL)                              │
└────────────────────────────┬────────────────────────────────────┘
                             │
┌────────────────────────────▼────────────────────────────────────┐
│                     AWS Fargate Cluster                          │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │         ECS Service (Django App - Multi-AZ)              │  │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐      │  │
│  │  │   Task 1    │  │   Task 2    │  │   Task N    │      │  │
│  │  │  (Django)   │  │  (Django)   │  │  (Django)   │      │  │
│  │  └─────────────┘  └─────────────┘  └─────────────┘      │  │
│  └──────────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │         ECS Service (Dramatiq Workers)                    │  │
│  │  ┌─────────────┐  ┌─────────────┐                        │  │
│  │  │  Worker 1   │  │  Worker 2   │                        │  │
│  │  └─────────────┘  └─────────────┘                        │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                    │                    │
         ┌──────────▼──────────┐  ┌─────▼──────┐
         │   RDS PostgreSQL    │  │ ElastiCache│
         │   (Multi-AZ)        │  │   (Redis)  │
         └─────────────────────┘  └────────────┘
```

## Phase 1: Containerization

### 1.1 Dockerfile Creation
```dockerfile
# Multi-stage build for optimized image size
FROM python:3.11-slim as builder

# Install build dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    python3-dev \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Set work directory
WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --user --no-cache-dir -r requirements.txt

# Production stage
FROM python:3.11-slim

# Install runtime dependencies
RUN apt-get update && apt-get install -y \
    libpq5 \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN useradd -m -u 1000 django

# Copy Python dependencies from builder
COPY --from=builder /root/.local /home/django/.local

# Set work directory
WORKDIR /app

# Copy application code
COPY --chown=django:django . .

# Switch to non-root user
USER django

# Make sure scripts in .local are usable
ENV PATH=/home/django/.local/bin:$PATH

# Collect static files
RUN python manage.py collectstatic --noinput

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=40s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health/')"

# Run gunicorn
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "3", "--threads", "2", "--timeout", "120", "booking_api.wsgi:application"]
```

### 1.2 Docker Compose for Local Development
```yaml
version: '3.8'

services:
  db:
    image: postgres:15
    environment:
      POSTGRES_DB: booking_db
      POSTGRES_USER: booking_user
      POSTGRES_PASSWORD: booking_password
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"

  web:
    build: .
    command: python manage.py runserver 0.0.0.0:8000
    volumes:
      - .:/app
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://booking_user:booking_password@db:5432/booking_db
      - REDIS_URL=redis://redis:6379/0
      - DJANGO_SECRET_KEY=your-secret-key-here
      - DEBUG=True
      - DEVELOPMENT_MODE=True
    depends_on:
      - db
      - redis

  worker:
    build: .
    command: python manage.py rundramatiq
    volumes:
      - .:/app
    environment:
      - DATABASE_URL=postgresql://booking_user:booking_password@db:5432/booking_db
      - REDIS_URL=redis://redis:6379/0
      - DJANGO_SECRET_KEY=your-secret-key-here
    depends_on:
      - db
      - redis

volumes:
  postgres_data:
```

## Phase 2: AWS Infrastructure Setup

### 2.1 Core Infrastructure Components

#### Networking
- **VPC**: Custom VPC with CIDR 10.0.0.0/16
- **Subnets**:
  - 2 Public subnets (10.0.1.0/24, 10.0.2.0/24) for ALB
  - 2 Private subnets (10.0.10.0/24, 10.0.20.0/24) for Fargate tasks
  - 2 Database subnets (10.0.100.0/24, 10.0.200.0/24) for RDS
- **Security Groups**:
  - ALB SG: Allow 80/443 from internet
  - Fargate SG: Allow 8000 from ALB SG
  - RDS SG: Allow 5432 from Fargate SG
  - Redis SG: Allow 6379 from Fargate SG

#### Compute
- **ECS Cluster**: booking-api-cluster
- **Task Definitions**:
  - Django Web: 1 vCPU, 2GB RAM
  - Dramatiq Worker: 0.5 vCPU, 1GB RAM
- **Services**:
  - Web Service: Min 2, Max 10 tasks
  - Worker Service: Min 1, Max 5 tasks

#### Database
- **RDS PostgreSQL**:
  - Engine: PostgreSQL 15
  - Instance: db.t3.medium
  - Multi-AZ deployment
  - Automated backups (7 days)
  - Encrypted storage

#### Cache
- **ElastiCache Redis**:
  - Engine: Redis 7
  - Node type: cache.t3.micro
  - Cluster mode disabled
  - Automatic failover

#### Storage
- **S3 Buckets**:
  - Static files bucket
  - Media files bucket
  - Backup bucket

### 2.2 Environment Variables Management

#### AWS Systems Manager Parameter Store
```
/booking-api/prod/database_url
/booking-api/prod/django_secret_key
/booking-api/prod/redis_url
/booking-api/prod/twilio_sid
/booking-api/prod/twilio_token
/booking-api/prod/twilio_phone_number
/booking-api/prod/allowed_hosts
```

## Phase 3: Deployment Process

### 3.1 Initial Setup Steps

1. **Build and Push Docker Image**
```bash
# Build image
docker build -t booking-api .

# Tag for ECR
docker tag booking-api:latest [AWS_ACCOUNT_ID].dkr.ecr.[REGION].amazonaws.com/booking-api:latest

# Push to ECR
aws ecr get-login-password --region [REGION] | docker login --username AWS --password-stdin [AWS_ACCOUNT_ID].dkr.ecr.[REGION].amazonaws.com
docker push [AWS_ACCOUNT_ID].dkr.ecr.[REGION].amazonaws.com/booking-api:latest
```

2. **Database Migration**
```bash
# Run as a one-off Fargate task
aws ecs run-task \
  --cluster booking-api-cluster \
  --task-definition booking-api-migrate \
  --launch-type FARGATE \
  --network-configuration "awsvpcConfiguration={subnets=[subnet-xxx],securityGroups=[sg-xxx]}"
```

### 3.2 Terraform Configuration Example

```hcl
# main.tf
resource "aws_ecs_cluster" "booking_api" {
  name = "booking-api-cluster"

  setting {
    name  = "containerInsights"
    value = "enabled"
  }
}

resource "aws_ecs_task_definition" "booking_api_web" {
  family                   = "booking-api-web"
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  cpu                      = "1024"
  memory                   = "2048"
  execution_role_arn       = aws_iam_role.ecs_execution.arn
  task_role_arn            = aws_iam_role.ecs_task.arn

  container_definitions = jsonencode([
    {
      name  = "django"
      image = "${aws_ecr_repository.booking_api.repository_url}:latest"

      portMappings = [
        {
          containerPort = 8000
          protocol      = "tcp"
        }
      ]

      environment = [
        {
          name  = "DJANGO_ALLOWED_HOSTS"
          value = var.allowed_hosts
        }
      ]

      secrets = [
        {
          name      = "DATABASE_URL"
          valueFrom = aws_ssm_parameter.database_url.arn
        },
        {
          name      = "DJANGO_SECRET_KEY"
          valueFrom = aws_ssm_parameter.django_secret_key.arn
        },
        {
          name      = "REDIS_URL"
          valueFrom = aws_ssm_parameter.redis_url.arn
        }
      ]

      logConfiguration = {
        logDriver = "awslogs"
        options = {
          "awslogs-group"         = aws_cloudwatch_log_group.booking_api.name
          "awslogs-region"        = var.region
          "awslogs-stream-prefix" = "web"
        }
      }
    }
  ])
}

resource "aws_ecs_service" "booking_api_web" {
  name            = "booking-api-web"
  cluster         = aws_ecs_cluster.booking_api.id
  task_definition = aws_ecs_task_definition.booking_api_web.arn
  desired_count   = 2
  launch_type     = "FARGATE"

  network_configuration {
    security_groups = [aws_security_group.fargate.id]
    subnets         = aws_subnet.private[*].id
  }

  load_balancer {
    target_group_arn = aws_lb_target_group.booking_api.arn
    container_name   = "django"
    container_port   = 8000
  }

  depends_on = [aws_lb_listener.booking_api]
}
```

## Phase 4: CI/CD Pipeline

### 4.1 GitHub Actions Configuration

```yaml
name: Deploy to AWS Fargate

on:
  push:
    branches: [main]

env:
  AWS_REGION: us-east-1
  ECR_REPOSITORY: booking-api
  ECS_SERVICE: booking-api-web
  ECS_CLUSTER: booking-api-cluster

jobs:
  deploy:
    runs-on: ubuntu-latest

    steps:
    - name: Checkout code
      uses: actions/checkout@v3

    - name: Configure AWS credentials
      uses: aws-actions/configure-aws-credentials@v2
      with:
        aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
        aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
        aws-region: ${{ env.AWS_REGION }}

    - name: Login to Amazon ECR
      id: login-ecr
      uses: aws-actions/amazon-ecr-login@v1

    - name: Build, tag, and push image
      env:
        ECR_REGISTRY: ${{ steps.login-ecr.outputs.registry }}
        IMAGE_TAG: ${{ github.sha }}
      run: |
        docker build -t $ECR_REGISTRY/$ECR_REPOSITORY:$IMAGE_TAG .
        docker push $ECR_REGISTRY/$ECR_REPOSITORY:$IMAGE_TAG
        docker tag $ECR_REGISTRY/$ECR_REPOSITORY:$IMAGE_TAG $ECR_REGISTRY/$ECR_REPOSITORY:latest
        docker push $ECR_REGISTRY/$ECR_REPOSITORY:latest

    - name: Update ECS service
      run: |
        aws ecs update-service \
          --cluster $ECS_CLUSTER \
          --service $ECS_SERVICE \
          --force-new-deployment
```

## Phase 5: Monitoring and Operations

### 5.1 CloudWatch Configuration
- **Metrics**:
  - ECS Service metrics (CPU, Memory)
  - ALB metrics (Request count, Target response time)
  - RDS metrics (CPU, Connections, Storage)
  - Custom application metrics via CloudWatch agent

- **Alarms**:
  - High CPU utilization (>80% for 5 minutes)
  - High memory utilization (>90%)
  - Database connection errors
  - 5XX error rate > 1%
  - Response time > 2 seconds

### 5.2 Logging Strategy
- **Application Logs**: CloudWatch Logs
- **Access Logs**: ALB logs to S3
- **Audit Logs**: CloudTrail
- **Log Retention**: 30 days for application, 90 days for audit

### 5.3 Backup and Disaster Recovery
- **RDS**: Automated backups, manual snapshots before major changes
- **Code**: Git repository, ECR image versioning
- **Configuration**: Parameter Store versioning
- **Recovery Time Objective (RTO)**: 1 hour
- **Recovery Point Objective (RPO)**: 15 minutes

## Phase 6: Security Best Practices

### 6.1 Network Security
- All traffic encrypted in transit (TLS 1.2+)
- Private subnets for all compute resources
- WAF rules on ALB for common attacks
- VPC Flow Logs enabled

### 6.2 Application Security
- Secrets in Parameter Store (encrypted)
- IAM roles for service-to-service authentication
- Security groups with least privilege
- Regular security patches via new deployments

### 6.3 Compliance
- Enable AWS Config for compliance monitoring
- CloudTrail for audit logging
- GuardDuty for threat detection
- Regular security assessments

## Cost Optimization

### Estimated Monthly Costs (US East 1)
- **Fargate**: ~$150 (2 web tasks + 1 worker task)
- **RDS**: ~$100 (db.t3.medium Multi-AZ)
- **ElastiCache**: ~$25 (cache.t3.micro)
- **ALB**: ~$25
- **Data Transfer**: ~$50
- **Other** (S3, CloudWatch, etc.): ~$50
- **Total**: ~$400/month

### Cost Optimization Strategies
1. Use Fargate Spot for non-critical workloads
2. Implement auto-scaling based on actual usage
3. Use S3 lifecycle policies for log archival
4. Reserved Instances for stable workloads
5. Regular cost review and optimization

## Migration Checklist

- [ ] Create AWS account and configure IAM
- [ ] Set up VPC and networking
- [ ] Create ECR repository
- [ ] Build and push Docker images
- [ ] Create RDS instance and migrate data
- [ ] Set up ElastiCache
- [ ] Configure Parameter Store
- [ ] Create ECS cluster and services
- [ ] Set up ALB and Route 53
- [ ] Configure CI/CD pipeline
- [ ] Set up monitoring and alarms
- [ ] Perform security review
- [ ] Test deployment
- [ ] Plan cutover strategy
- [ ] Execute production deployment
- [ ] Monitor and optimize

## Rollback Strategy

1. **Blue-Green Deployment**: Maintain previous version for quick rollback
2. **Database Migrations**: Always create reversible migrations
3. **Feature Flags**: Use for gradual feature rollout
4. **Automated Rollback**: Configure based on CloudWatch alarms

## Support and Maintenance

### Regular Tasks
- Weekly security updates review
- Monthly cost optimization review
- Quarterly disaster recovery drill
- Annual architecture review

### Documentation
- Maintain runbooks for common operations
- Document all custom configurations
- Keep architecture diagrams updated
- Regular team training on AWS services
