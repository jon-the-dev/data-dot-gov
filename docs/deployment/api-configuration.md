# Frontend API Configuration

This document explains how the frontend communicates with the backend API in different environments.

## Overview

The frontend uses environment-specific configuration to determine the API base URL. This allows the same codebase to work in both development and production environments.

## Configuration Files

### `.env` - Default Environment
```env
VITE_API_URL=http://localhost:8000/api/v1
```
Default fallback used if no environment-specific file exists.

### `.env.development` - Development Environment
```env
VITE_API_URL=http://localhost:8000/api/v1
```
Used when running `pnpm run dev` locally.

### `.env.production` - Production Environment
```env
VITE_API_URL=/api/v1
```
Used when building for production (`pnpm run build`). Uses relative paths that work through Traefik reverse proxy.

## How It Works

### Development Mode
When running locally with `pnpm run dev`:
1. Vite loads `.env.development`
2. API calls use `http://localhost:8000/api/v1`
3. Vite dev server proxies `/api` requests to `localhost:8000` (configured in `vite.config.js`)
4. Direct connection to local backend

### Production Mode
When deployed via Docker:
1. Docker build uses `.env.production`
2. API calls use relative path `/api/v1`
3. Nginx serves frontend on port 80
4. Traefik reverse proxy routes requests:
   - `https://congress.local.team-skynet.io` → Frontend (nginx)
   - `https://congress.local.team-skynet.io/api/v1/*` → Backend (FastAPI on port 8000)
5. Single domain, no CORS issues

## Vite Configuration

The `vite.config.js` includes a development proxy:

```javascript
server: {
  port: 5173,
  host: true,
  proxy: {
    '/api': {
      target: 'http://localhost:8000',
      changeOrigin: true,
      secure: false
    }
  }
}
```

This allows development code to use relative paths like `/api/v1/...` which get proxied to the backend.

## Service Implementation

Both `pollerService.ts` and `dataService.js` use the environment variable:

```typescript
private static API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1';
```

This pattern:
1. Checks `import.meta.env.VITE_API_URL` first
2. Falls back to `localhost:8000/api/v1` if not set
3. Works in both TypeScript and JavaScript files

## Traefik Routing

The production deployment uses Traefik labels in `docker-compose.yml`:

```yaml
frontend:
  labels:
    - "traefik.http.routers.congress.rule=Host(`congress.local.team-skynet.io`)"

backend:
  labels:
    - "traefik.http.routers.congress-api.rule=Host(`congress.local.team-skynet.io`) && PathPrefix(`/api`)"
```

This ensures both frontend and backend are accessible on the same domain.

## Troubleshooting

### Issue: `net::ERR_BLOCKED_BY_CLIENT`
**Cause**: Frontend trying to connect to `localhost:8000` in production
**Solution**: Ensure `.env.production` exists with relative path `/api/v1`

### Issue: CORS errors
**Cause**: Frontend and backend on different domains
**Solution**: Use relative paths in production (handled by `.env.production`)

### Issue: 404 on API calls in production
**Cause**: Traefik routing misconfigured
**Solution**: Verify Traefik labels in `docker-compose.yml` include PathPrefix rules

### Issue: API works in dev but not production
**Cause**: Different environment files being used
**Solution**:
1. Check `.env.production` exists and has correct URL
2. Rebuild Docker containers: `docker compose up --build -d`
3. Verify build includes new environment file

## Testing

### Development
```bash
cd frontend
pnpm run dev
# Open http://localhost:5173
# API calls should work through Vite proxy
```

### Production Build
```bash
cd frontend
pnpm run build
# Check dist/assets/index-*.js for API_BASE_URL
# Should contain "/api/v1" not "localhost:8000"
```

### Docker Production
```bash
docker compose up --build -d
# Open https://congress.local.team-skynet.io
# Check browser console for API calls
# Should see requests to /api/v1/* not localhost
```

## Related Issues

- Issue #20: Frontend Making Requests to Localhost Instead of Production API
- Issue #17: Trigger Fetch Buttons Not Working (caused by #20)
- Issue #18: Poller Status Shows Error (caused by #20)
- Issue #19: Data Freshness Table Empty (caused by #20)
