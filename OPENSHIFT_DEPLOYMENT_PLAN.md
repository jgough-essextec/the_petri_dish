# OpenShift Deployment Plan - Todo Application

## Overview
This plan outlines the deployment of a full-stack Todo application on OpenShift using ArgoCD for GitOps deployment.

**Application Components:**
- **Backend**: Python FastAPI (port 8000) with SQLite database
- **Frontend**: React application (port 3000)
- **Database**: SQLite (requires persistent storage)

## Deployment Strategy
- **Container Registry**: Use OpenShift's built-in registry or external registry (Docker Hub, Quay.io)
- **GitOps**: ArgoCD pointing to Helm chart in this repository
- **Database**: Persistent Volume Claim for SQLite database file
- **Networking**: OpenShift Routes for external access

## Phase 1: Container Optimization

### 1.1 Backend Container Improvements
- [ ] Review and optimize `backend/Dockerfile`
- [ ] Add health check endpoints to FastAPI app
- [ ] Configure for production (disable debug mode, proper logging)
- [ ] Add non-root user for security
- [ ] Multi-stage build for smaller image size

### 1.2 Frontend Container Improvements
- [ ] Review and optimize `frontend/Dockerfile`
- [ ] Multi-stage build (build stage + nginx serving stage)
- [ ] Configure nginx for production serving
- [ ] Add health check endpoint
- [ ] Environment variable configuration for API endpoint

### 1.3 Container Registry Setup
- [ ] Decide on container registry (OpenShift internal, Docker Hub, or Quay.io)
- [ ] Create registry credentials if using external registry
- [ ] Set up automated builds (optional)

## Phase 2: Kubernetes/OpenShift Resources

### 2.1 Namespace and RBAC
- [ ] Create namespace for the application
- [ ] Set up service accounts if needed
- [ ] Configure RBAC policies

### 2.2 Database Persistence
- [ ] Create PersistentVolumeClaim for SQLite database
- [ ] Configure volume mounts in backend deployment
- [ ] Plan database initialization strategy

### 2.3 Backend Deployment Resources
- [ ] Deployment manifest for FastAPI backend
- [ ] Service for backend (ClusterIP)
- [ ] ConfigMap for environment variables
- [ ] Secret for sensitive data (if any)
- [ ] Resource limits and requests
- [ ] Liveness and readiness probes

### 2.4 Frontend Deployment Resources
- [ ] Deployment manifest for React frontend
- [ ] Service for frontend (ClusterIP)
- [ ] ConfigMap for runtime configuration
- [ ] Resource limits and requests
- [ ] Liveness and readiness probes

### 2.5 Networking
- [ ] Route for frontend (external access)
- [ ] Route for backend API (external access)
- [ ] Network policies (optional, for security)

## Phase 3: Helm Chart Creation

### 3.1 Helm Chart Structure
```
helm-chart/
├── Chart.yaml
├── values.yaml
├── values-dev.yaml
├── values-prod.yaml
└── templates/
    ├── backend/
    │   ├── deployment.yaml
    │   ├── service.yaml
    │   ├── configmap.yaml
    │   └── pvc.yaml
    ├── frontend/
    │   ├── deployment.yaml
    │   ├── service.yaml
    │   ├── configmap.yaml
    │   └── route.yaml
    ├── backend-route.yaml
    ├── namespace.yaml
    └── NOTES.txt
```

### 3.2 Helm Chart Components
- [ ] Create Chart.yaml with metadata
- [ ] Create values.yaml with default configuration
- [ ] Create environment-specific values files
- [ ] Template all Kubernetes resources
- [ ] Add helper templates for common labels/selectors
- [ ] Include resource quotas and limits

### 3.3 Configuration Management
- [ ] Environment-specific values (dev, staging, prod)
- [ ] Image tags and registry configuration
- [ ] Resource allocations per environment
- [ ] Database configuration options
- [ ] Ingress/Route configuration

## Phase 4: ArgoCD Application Setup

### 4.1 ArgoCD Application Manifest
- [ ] Create ArgoCD Application YAML
- [ ] Configure source repository (this GitHub repo)
- [ ] Set target namespace and cluster
- [ ] Configure sync policies (auto-sync, self-heal)
- [ ] Set up sync windows if needed

### 4.2 Repository Structure
- [ ] Organize repository for GitOps
- [ ] Create separate directories for different environments
- [ ] Document deployment process
- [ ] Set up proper .gitignore for generated files

## Phase 5: Environment Configuration

### 5.1 Development Environment
- [ ] Configure dev-specific values
- [ ] Smaller resource allocations
- [ ] Debug logging enabled
- [ ] Relaxed security policies

### 5.2 Production Environment
- [ ] Configure prod-specific values
- [ ] Appropriate resource allocations
- [ ] Production logging configuration
- [ ] Security hardening
- [ ] Backup strategies

## Phase 6: Security and Monitoring

### 6.1 Security
- [ ] Configure pod security context
- [ ] Network policies
- [ ] Secret management
- [ ] Image scanning integration
- [ ] RBAC configuration

### 6.2 Monitoring and Observability
- [ ] Configure health checks
- [ ] Add metrics endpoints (optional)
- [ ] Log aggregation setup
- [ ] Alerting configuration (if monitoring stack available)

## Phase 7: Testing and Validation

### 7.1 Local Testing
- [ ] Test Helm chart locally with `helm template`
- [ ] Validate Kubernetes manifests
- [ ] Test container builds

### 7.2 Deployment Testing
- [ ] Deploy to development environment
- [ ] Verify application functionality
- [ ] Test ArgoCD sync process
- [ ] Validate persistence across pod restarts
- [ ] Test rolling updates

## Phase 8: Documentation and Maintenance

### 8.1 Documentation
- [ ] Update README with deployment instructions
- [ ] Document environment variables
- [ ] Create troubleshooting guide
- [ ] Document rollback procedures

### 8.2 Maintenance
- [ ] Set up automated security updates
- [ ] Plan for database backups
- [ ] Monitor resource usage
- [ ] Plan scaling strategies

## Key Decisions Needed

Before proceeding, please clarify:

1. **Container Registry**: Where should we push the container images?
   - OpenShift internal registry
   - Docker Hub
   - Quay.io
   - Another registry?

2. **Environment**: Are you planning for just one environment or multiple (dev/prod)?

3. **Domain**: Do you have a domain name for the application routes?

4. **Database**: Are you okay with SQLite for now, or would you prefer a more robust database for production?

5. **Resources**: Any specific resource requirements or constraints on your OpenShift cluster?

6. **Secrets**: Any sensitive configuration that needs to be managed as secrets?

## Estimated Timeline
- **Phase 1-2**: 1-2 days (Container and resource optimization)
- **Phase 3**: 1 day (Helm chart creation)
- **Phase 4**: 0.5 days (ArgoCD setup)
- **Phase 5-6**: 1 day (Environment and security configuration)
- **Phase 7-8**: 1 day (Testing and documentation)

**Total estimated time**: 4-5 days

## Next Steps
Once you review this plan and answer the key questions, we can proceed with implementation starting from Phase 1.