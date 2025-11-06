# Multi-stage build for React frontend

# Build stage
FROM node:18-alpine AS builder

WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm ci --only=production

# Copy source code
COPY . .

# Build the React app
RUN npm run build

# Production stage
FROM nginx:1.21-alpine

# Create non-root user for security
RUN addgroup -g 1001 appuser && adduser -S -u 1001 -G appuser appuser

# Copy built React app to nginx html directory
COPY --from=builder /app/build /usr/share/nginx/html

# Copy custom nginx configuration
COPY nginx.conf /etc/nginx/nginx.conf

# Create directories with proper permissions
RUN mkdir -p /var/cache/nginx /var/run /var/log/nginx && \
    chown -R appuser:appuser /var/cache/nginx /var/run /var/log/nginx /usr/share/nginx/html && \
    chmod -R 755 /var/cache/nginx /var/run /var/log/nginx /usr/share/nginx/html

# Switch to non-root user
USER appuser

# Expose port 8080 (non-privileged port)
EXPOSE 8080

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD wget --no-verbose --tries=1 --spider http://localhost:8080/health || exit 1

# Start nginx
CMD ["nginx", "-g", "daemon off;"]
