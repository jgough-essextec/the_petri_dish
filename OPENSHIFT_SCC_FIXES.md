# OpenShift Security Context Constraint (SCC) Fixes

## Problem
The deployment failed with SCC violations because OpenShift requires specific user ID ranges and doesn't allow hardcoded user IDs like `1001`.

## What Was Fixed

### 1. Backend Dockerfile (`backend/Dockerfile`)
**Before:**
- Created specific user `appuser` with hardcoded UID
- Used `USER appuser`
- Set ownership with `chown -R appuser:appuser`

**After:**
- Removed user creation
- Set permissions for group 0 (root group): `chmod -R g+rwx` and `chgrp -R 0`
- Let OpenShift assign user ID from allowed range

### 2. Frontend Dockerfile (`frontend/Dockerfile`)  
**Before:**
- Created specific user with UID/GID 1001
- Used `USER appuser`
- Set specific ownership

**After:**
- Removed user creation and USER directive
- Set OpenShift-compatible permissions with group 0
- Let OpenShift handle user assignment

### 3. Helm Chart Security Contexts (`k8s/helm-chart/values.yaml`)
**Before:**
```yaml
securityContext:
  runAsNonRoot: true
  runAsUser: 1001
  runAsGroup: 1001
  fsGroup: 1001

podSecurityContext:
  fsGroup: 1001
```

**After:**
```yaml
securityContext:
  runAsNonRoot: true
  # Let OpenShift assign user ID from allowed range

podSecurityContext:
  # Let OpenShift SCC handle fsGroup assignment
```

## How to Redeploy

### Step 1: Commit and Push Changes
```bash
git add .
git commit -m "Fix OpenShift SCC compatibility issues

- Remove hardcoded user IDs from Dockerfiles
- Set group 0 permissions for OpenShift compatibility  
- Remove specific security context constraints from Helm chart
- Let OpenShift SCC handle user/group assignment automatically

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>"

git push origin open-shift-build
```

### Step 2: Rebuild Container Images
```bash
# Start new builds with updated Dockerfiles
oc start-build todo-backend
oc start-build todo-frontend

# Monitor the builds
oc logs -f bc/todo-backend
oc logs -f bc/todo-frontend
```

### Step 3: Force ArgoCD Sync
```bash
# If using ArgoCD CLI
argocd app sync todo-app --force

# Or through OpenShift CLI
oc patch application todo-app -n argocd -p '{"operation":{"sync":{"revision":"HEAD"}}}' --type merge

# Or use the ArgoCD UI - click "Refresh" then "Sync"
```

### Step 4: Verify Deployment
```bash
# Check pod status
oc get pods -n todo-app

# Check events for any remaining issues
oc get events -n todo-app --sort-by='.lastTimestamp' | tail -10

# Check pod details if still having issues
oc describe pod <pod-name> -n todo-app
```

## Key OpenShift Security Concepts

### Why This Happened
- OpenShift uses Security Context Constraints (SCCs) to enforce security policies
- The `restricted-v2` SCC (default) only allows user IDs in specific ranges like `[1000810000, 1000819999]`
- Hardcoded low user IDs like `1001` are not allowed for security reasons

### OpenShift Best Practices
1. **Don't hardcode user IDs** - Let OpenShift assign them
2. **Use group 0 permissions** - OpenShift always uses root group (group 0)
3. **Set directory permissions with `g+rwx`** - Allow group write access
4. **Avoid USER directive** - Let the SCC handle user assignment
5. **Use `runAsNonRoot: true`** - Ensures security without specifying exact user

### Common SCC Errors
- `Invalid value: 1001: must be in the ranges: [1000810000, 1000819999]`
- `not usable by user or serviceaccount`
- `Forbidden: not usable by user or serviceaccount`

## Expected Behavior After Fix
- Pods should start successfully
- OpenShift will assign user IDs from the allowed range (e.g., `1000810000`)
- Applications will run with proper permissions
- Database persistence will work correctly
- Health checks will function as expected

## Troubleshooting

If you still see issues:

1. **Check SCC assignment:**
```bash
oc get pod <pod-name> -n todo-app -o yaml | grep scc
```

2. **Verify user ID assignment:**
```bash
oc exec -it <pod-name> -n todo-app -- id
```

3. **Check file permissions:**
```bash
oc exec -it <backend-pod> -n todo-app -- ls -la /app/data
```

4. **Force recreate pods:**
```bash
oc rollout restart deployment/todo-backend -n todo-app
oc rollout restart deployment/todo-frontend -n todo-app
```
