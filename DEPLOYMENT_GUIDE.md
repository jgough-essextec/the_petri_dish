# Todo App OpenShift Deployment Guide

This guide will walk you through deploying the Todo application on OpenShift using ArgoCD.

## Prerequisites

- OpenShift cluster access with cluster-admin or project-admin permissions
- ArgoCD installed and configured on your OpenShift cluster  
- `oc` CLI tool installed and configured
- Git repository access (this repo should be pushed to GitHub)

## Step 1: Push Changes to GitHub

First, commit and push all the changes we've made to your GitHub repository:

```bash
# Add all the new files
git add .

# Commit the changes
git commit -m "Add OpenShift deployment configuration with ArgoCD

- Add optimized Dockerfiles for production deployment
- Add health check endpoints to FastAPI backend
- Create comprehensive Helm chart for Kubernetes deployment
- Add OpenShift Routes for external access
- Configure ArgoCD application manifest
- Add BuildConfigs for automated container image builds

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>"

# Push to GitHub
git push origin open-shift-build
```

## Step 2: Create OpenShift Project and Build Images

```bash
# Create the project/namespace
oc new-project todo-app

# Apply the BuildConfigs and ImageStreams
oc apply -f k8s/buildconfigs.yaml

# Start the builds
oc start-build todo-backend
oc start-build todo-frontend

# Monitor the builds
oc logs -f bc/todo-backend
oc logs -f bc/todo-frontend
```

## Step 3: Deploy with ArgoCD

### Option A: Using ArgoCD UI

1. Open the ArgoCD web interface
2. Click "New App"
3. Fill in the following details:
   - **Application Name**: `todo-app`
   - **Project**: `default`
   - **Sync Policy**: `Automatic`
   - **Repository URL**: `https://github.com/jgough-essextec/the_petri_dish.git`
   - **Revision**: `open-shift-build`
   - **Path**: `k8s/helm-chart`
   - **Cluster URL**: `https://kubernetes.default.svc`
   - **Namespace**: `todo-app`
4. Click "Create"

### Option B: Using kubectl/oc CLI

```bash
# Apply the ArgoCD application manifest
oc apply -f k8s/argocd-application.yaml

# Check the application status
oc get application todo-app -n argocd
```

## Step 4: Verify Deployment

```bash
# Check if all pods are running
oc get pods -n todo-app

# Check services
oc get svc -n todo-app

# Check routes
oc get routes -n todo-app

# Check PVC for database persistence
oc get pvc -n todo-app

# View application logs
oc logs -f deployment/todo-backend -n todo-app
oc logs -f deployment/todo-frontend -n todo-app
```

## Step 5: Access the Application

Once deployed, you can access:

- **Frontend**: https://todo.apps.goughlab.goughlab.com
- **Backend API**: https://todo-api.apps.goughlab.goughlab.com
- **Health Check**: https://todo-api.apps.goughlab.goughlab.com/health

## Troubleshooting

### Build Issues

```bash
# Check build logs
oc logs -f bc/todo-backend
oc logs -f bc/todo-frontend

# Restart builds if needed
oc start-build todo-backend
oc start-build todo-frontend
```

### Pod Issues

```bash
# Check pod status
oc describe pod <pod-name> -n todo-app

# Check pod logs
oc logs <pod-name> -n todo-app

# Check events
oc get events -n todo-app --sort-by='.lastTimestamp'
```

### ArgoCD Sync Issues

```bash
# Check ArgoCD application status
oc get application todo-app -n argocd -o yaml

# Force sync if needed
argocd app sync todo-app

# Or through UI: click "Sync" button in ArgoCD UI
```

### Route/Network Issues

```bash
# Check routes
oc get routes -n todo-app

# Test internal connectivity
oc run test-pod --image=curlimages/curl -n todo-app --rm -it -- /bin/sh
# Inside the pod:
curl http://todo-backend:8000/health
curl http://todo-frontend:8080/health
```

## Configuration

### Environment Variables

Backend environment variables can be configured in `k8s/helm-chart/values.yaml`:

```yaml
backend:
  env:
    - name: DATABASE_PATH
      value: "/app/data/todos.db"
    # Add more environment variables here
```

Frontend environment variables:

```yaml
frontend:
  env:
    - name: REACT_APP_API_URL
      value: "https://todo-api.apps.goughlab.goughlab.com"
    # Add more environment variables here
```

### Resource Limits

Adjust resource limits in `values.yaml`:

```yaml
backend:
  deployment:
    resources:
      requests:
        memory: "128Mi"
        cpu: "100m"
      limits:
        memory: "256Mi"
        cpu: "200m"
```

### Scaling

To scale the application:

```bash
# Scale backend
oc scale deployment todo-backend --replicas=3 -n todo-app

# Scale frontend  
oc scale deployment todo-frontend --replicas=2 -n todo-app
```

Or update the `values.yaml` file and let ArgoCD sync the changes.

## Database Backup

The SQLite database is persisted using a PVC. To backup:

```bash
# Get the pod name
POD_NAME=$(oc get pods -l app.kubernetes.io/name=todo-backend -n todo-app -o jsonpath='{.items[0].metadata.name}')

# Copy database file
oc cp todo-app/$POD_NAME:/app/data/todos.db ./todos-backup.db
```

## Updating the Application

1. Make changes to your code
2. Commit and push to the `open-shift-build` branch
3. ArgoCD will automatically detect changes and sync
4. New container images will be built automatically via BuildConfig triggers

## Security Notes

- The application runs with non-root users (UID 1001)
- Routes use TLS edge termination
- Pod security contexts are configured
- Resource limits are set to prevent resource exhaustion

## Next Steps

1. Consider setting up monitoring with Prometheus/Grafana
2. Configure backup strategies for the database
3. Set up proper CI/CD pipelines
4. Configure network policies for additional security
5. Consider using external databases (PostgreSQL) for production

## Support

If you encounter issues:

1. Check the troubleshooting section above
2. Review OpenShift and ArgoCD documentation
3. Check application logs and events
4. Verify network connectivity and DNS resolution
