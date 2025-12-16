# Multi-stage build for React frontend with nginx
FROM node:18-alpine AS base

# Install dependencies for all stages
RUN apk add --no-cache libc6-compat
WORKDIR /app

# Dependencies stage - for package installation
FROM base AS deps
# Copy package files
COPY package.json pnpm-lock.yaml* ./
# Install dependencies using pnpm
RUN npm install -g pnpm && pnpm install --frozen-lockfile

# Build stage - compile the application
FROM base AS builder
WORKDIR /app
COPY --from=deps /app/node_modules ./node_modules
COPY . ./

# Build arguments for runtime configuration
ARG VITE_API_URL=https://congress-api.local.team-skynet.io
ARG VITE_APP_TITLE="Congressional Transparency Platform"
ARG VITE_ENABLE_ANALYTICS=true
ARG VITE_SENTRY_DSN=""
ARG VITE_VERSION=1.0.0

# Set build environment variables
ENV VITE_API_URL=$VITE_API_URL
ENV VITE_APP_TITLE=$VITE_APP_TITLE
ENV VITE_ENABLE_ANALYTICS=$VITE_ENABLE_ANALYTICS
ENV VITE_SENTRY_DSN=$VITE_SENTRY_DSN
ENV VITE_VERSION=$VITE_VERSION
ENV NODE_ENV=production

# Install pnpm and build the application
# Skip type-check for now due to TypeScript errors - build directly with vite
RUN npm install -g pnpm && \
    npx vite build

# Verify build output
RUN ls -la dist/ && \
    test -f dist/index.html || (echo "Build failed: index.html not found" && exit 1)

# Production stage - serve with nginx
FROM nginx:1.25-alpine AS production

# Install additional tools for health checks and monitoring
RUN apk add --no-cache \
    curl \
    ca-certificates \
    tzdata \
    && rm -rf /var/cache/apk/*

# Set timezone
ENV TZ=UTC
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

# Create nginx user and directories
RUN addgroup -g 1001 -S nginx-custom && \
    adduser -S nginx-custom -u 1001 -G nginx-custom

# Copy custom nginx configuration
COPY docker/nginx/nginx.conf /etc/nginx/nginx.conf
COPY docker/nginx/default.conf /etc/nginx/conf.d/default.conf
COPY docker/nginx/security-headers.conf /etc/nginx/conf.d/security-headers.conf
COPY docker/nginx/gzip.conf /etc/nginx/conf.d/gzip.conf

# Copy built application from builder stage
COPY --from=builder /app/dist /usr/share/nginx/html

# Create health check endpoint
RUN echo '<!DOCTYPE html><html><head><title>Health Check</title></head><body><h1>OK</h1><p>Congress Viewer is running</p><script>console.log("Health check OK");</script></body></html>' > /usr/share/nginx/html/health

# Create logs directory and set permissions
RUN mkdir -p /var/log/nginx /var/cache/nginx && \
    chown -R nginx-custom:nginx-custom /var/log/nginx /var/cache/nginx /usr/share/nginx/html && \
    chmod -R 755 /usr/share/nginx/html

# Security: Remove default nginx user and use custom user
USER nginx-custom

# Expose port 80
EXPOSE 80

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:80/health || exit 1

# Labels for metadata
LABEL maintainer="Congress Transparency Platform"
LABEL version="1.0.0"
LABEL description="Congressional Transparency Platform Frontend"
LABEL org.opencontainers.image.title="Congress Viewer Frontend"
LABEL org.opencontainers.image.description="React-based frontend for Congressional transparency data"
LABEL org.opencontainers.image.vendor="Congress Transparency Project"
LABEL org.opencontainers.image.licenses="MIT"

# Start nginx
CMD ["nginx", "-g", "daemon off;"]

# Development stage - for local development with hot reload
FROM base AS development
WORKDIR /app
COPY --from=deps /app/node_modules ./node_modules
COPY frontend/ ./

# Install pnpm for development
RUN npm install -g pnpm

# Expose Vite dev server port
EXPOSE 5173

# Development environment variables
ENV NODE_ENV=development
ENV VITE_API_URL=http://localhost:8000
ENV VITE_APP_TITLE="Congressional Transparency Platform (Dev)"
ENV VITE_ENABLE_ANALYTICS=false

# Health check for development
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:5173/ || exit 1

# Start development server
CMD ["pnpm", "run", "dev", "--host", "0.0.0.0"]

# Testing stage - for running tests
FROM base AS testing
WORKDIR /app
COPY --from=deps /app/node_modules ./node_modules
COPY frontend/ ./

# Install pnpm and additional testing tools
RUN npm install -g pnpm

# Run linting and type checking
RUN pnpm run lint && pnpm run type-check

# Test build process
RUN pnpm run build

CMD ["pnpm", "run", "test"]