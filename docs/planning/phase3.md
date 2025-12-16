# PHASE 3: Microservices Architecture Migration Plan

## Executive Summary

Transform the current monolithic Congressional data collection platform into a scalable microservices architecture with three core services:
- **Poller Service**: Continuous data collection and historical backfilling
- **Backend API**: FastAPI service with SQLite for metadata and data serving
- **Frontend Service**: React app served via Nginx

All services will be containerized with Docker and exposed through Traefik reverse proxy.

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                         Traefik Proxy                           │
│                    (*.local.team-skynet.io)                     │
└─────────────┬────────────────┬────────────────┬────────────────┘
              │                │                │
              ▼                ▼                ▼
    ┌─────────────────┐ ┌─────────────┐ ┌─────────────┐
    │  Frontend       │ │  Backend    │ │  Poller     │
    │  (Nginx/React)  │ │  (FastAPI)  │ │  (Python)   │
    │  Port: 80       │ │  Port: 8000 │ │  No expose  │
    └─────────────────┘ └──────┬──────┘ └──────┬──────┘
                              │                │
                              ▼                ▼
                    ┌─────────────────────────────┐
                    │     Shared Volumes          │
                    │  - SQLite DB (metadata)     │
                    │  - Raw JSON Data Storage    │
                    │  - Analysis Results         │
                    └─────────────────────────────┘
```

## Services Architecture

### 1. Poller Service

**Purpose**: Background data collection and processing

```python
# poller/main.py
class CongressPoller:
    def __init__(self):
        self.collectors = [
            BillCollector(),
            MemberCollector(),
            VoteCollector(),
            LobbyingCollector()
        ]
    
    def run_continuous(self):
        """Run continuous polling with intelligent scheduling"""
        
    def run_historical_backfill(self, congresses: List[int]):
        """One-time historical data collection"""
```

**Features**:
- Continuous polling for new data (hourly/daily schedules)
- Historical backfilling for Congresses 113-117
- Smart rate limiting and error recovery
- Progress tracking and resumable operations
- Data validation and integrity checks

**Configuration**:
```yaml
poller:
  schedules:
    bills: "0 */6 * * *"       # Every 6 hours
    votes: "0 */1 * * *"       # Every hour
    members: "0 0 */7 * *"     # Weekly
    lobbying: "0 0 * * 1"      # Monday
  
  rate_limits:
    congress_api: 900          # requests per hour
    senate_api: 100            # requests per minute
  
  batch_sizes:
    bills: 100
    votes: 50
    members: 200
```

### 2. Backend API Service

**Purpose**: FastAPI service providing REST endpoints

```python
# backend/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="Congressional Transparency API")

@app.get("/api/v1/bills")
async def get_bills(congress: int = 118, limit: int = 100):
    """Get bills with pagination and filtering"""
    
@app.get("/api/v1/members")
async def get_members(congress: int = 118, party: str = None):
    """Get congressional members"""
    
@app.get("/api/v1/votes")
async def get_votes(congress: int = 118, chamber: str = None):
    """Get voting records"""
    
@app.get("/api/v1/analysis/{analysis_type}")
async def get_analysis(analysis_type: str, congress: int = 118):
    """Get pre-computed analysis results"""
```

**Data Layer**:
- SQLite database for metadata and indices
- JSON files for raw data storage
- Materialized analysis results
- Response caching with Redis

**Schema Design**:
```sql
-- metadata.db
CREATE TABLE data_sources (
    id INTEGER PRIMARY KEY,
    source_type TEXT,
    congress INTEGER,
    last_updated TIMESTAMP,
    record_count INTEGER,
    file_path TEXT
);

CREATE TABLE analysis_cache (
    id INTEGER PRIMARY KEY,
    analysis_type TEXT,
    parameters TEXT,
    result_path TEXT,
    computed_at TIMESTAMP,
    expires_at TIMESTAMP
);
```

### 3. Frontend Service

**Purpose**: React application with nginx reverse proxy

```dockerfile
# frontend/Dockerfile
FROM node:18-alpine AS builder
WORKDIR /app
COPY package*.json ./
RUN npm ci --only=production
COPY . .
RUN npm run build

FROM nginx:alpine
COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/nginx.conf
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
```

**Architecture**:
```
src/
├── components/
│   ├── charts/
│   ├── tables/
│   └── layout/
├── features/
│   ├── bills/
│   ├── members/
│   ├── votes/
│   └── analysis/
├── services/
│   ├── api.ts
│   └── cache.ts
└── stores/
    ├── bills.ts
    ├── members.ts
    └── analysis.ts
```

## Docker Compose Configuration

```yaml
# docker-compose.yml
version: '3.8'

services:
  frontend:
    build: ./frontend
    networks:
      - congress-network
      - backend
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.congress-ui.rule=Host(`congress.local.team-skynet.io`)"
      - "traefik.http.routers.congress-ui-secure.entrypoints=https"
      - "traefik.http.routers.congress-ui-secure.tls=true"
      - "traefik.http.services.congress-ui.loadbalancer.server.port=80"
      - "traefik.docker.network=backend"
  
  backend:
    build: ./backend
    environment:
      - DATABASE_URL=sqlite:///app/data/metadata.db
      - DATA_DIR=/app/data
    volumes:
      - congress-data:/app/data
    networks:
      - congress-network
      - backend
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.congress-api.rule=Host(`congress-api.local.team-skynet.io`)"
      - "traefik.http.routers.congress-api-secure.entrypoints=https"
      - "traefik.http.routers.congress-api-secure.tls=true"
      - "traefik.http.services.congress-api.loadbalancer.server.port=8000"
      - "traefik.docker.network=backend"
  
  poller:
    build: ./poller
    environment:
      - DATA_GOV_API_KEY=${DATA_GOV_API_KEY}
      - SENATE_GOV_USERNAME=${SENATE_GOV_USERNAME}
      - SENATE_GOV_PASSWORD=${SENATE_GOV_PASSWORD}
      - DATA_DIR=/app/data
      - POLL_SCHEDULE=continuous
    volumes:
      - congress-data:/app/data
    networks:
      - congress-network
    restart: unless-stopped

networks:
  congress-network:
    driver: bridge
  backend:
    external: true
    name: backend

volumes:
  congress-data:
    driver: local
```

## Migration Strategy

### Phase 3.1: Service Extraction (Weeks 1-2)

1. **Create Service Boundaries**
   ```bash
   mkdir -p services/{frontend,backend,poller}
   ```

2. **Extract Poller Service**
   - Move data collection scripts to `poller/`
   - Create unified `CongressPoller` class
   - Add scheduling and monitoring

3. **Extract Backend API**
   - Create FastAPI application
   - Implement core endpoints
   - Add SQLite metadata layer

4. **Containerize Services**
   - Write Dockerfiles for each service
   - Create docker-compose configuration
   - Test local deployment

### Phase 3.2: Data Layer Migration (Weeks 3-4)

1. **Implement SQLite Metadata Layer**
   ```python
   # backend/models.py
   from sqlalchemy import create_engine, Column, Integer, String, DateTime
   from sqlalchemy.ext.declarative import declarative_base
   
   Base = declarative_base()
   
   class DataSource(Base):
       __tablename__ = 'data_sources'
       id = Column(Integer, primary_key=True)
       source_type = Column(String)
       congress = Column(Integer)
       last_updated = Column(DateTime)
       record_count = Column(Integer)
       file_path = Column(String)
   ```

2. **Create Data Access Layer**
   ```python
   # backend/data_access.py
   class CongressDataAccess:
       def get_bills(self, congress: int, limit: int = 100):
           """Load bills from JSON files with metadata"""
           
       def get_analysis(self, analysis_type: str, congress: int):
           """Load cached analysis results"""
   ```

3. **Implement Caching Strategy**
   - Response caching for API endpoints
   - Analysis result caching
   - Smart cache invalidation

### Phase 3.3: Frontend Modernization (Weeks 5-6)

1. **State Management with Zustand**
   ```typescript
   // src/stores/bills.ts
   import { create } from 'zustand'
   
   interface BillsState {
     bills: Bill[]
     loading: boolean
     fetchBills: (congress: number) => Promise<void>
   }
   
   export const useBillsStore = create<BillsState>((set, get) => ({
     bills: [],
     loading: false,
     fetchBills: async (congress) => {
       set({ loading: true })
       const bills = await api.getBills({ congress })
       set({ bills, loading: false })
     }
   }))
   ```

2. **API Service Layer**
   ```typescript
   // src/services/api.ts
   class CongressAPI {
     private baseUrl = process.env.VITE_API_URL
     
     async getBills(params: GetBillsParams): Promise<Bill[]> {
       const response = await fetch(`${this.baseUrl}/api/v1/bills`, {
         method: 'GET',
         headers: { 'Content-Type': 'application/json' },
         body: JSON.stringify(params)
       })
       return response.json()
     }
   }
   ```

3. **Component Modernization**
   - Convert to TypeScript
   - Implement proper error boundaries
   - Add loading states and error handling
   - Implement responsive design

### Phase 3.4: Production Deployment (Weeks 7-8)

1. **Traefik Integration**
   - Configure reverse proxy labels
   - Set up SSL termination
   - Implement health checks

2. **Monitoring and Logging**
   ```python
   # Add to all services
   import structlog
   import sentry_sdk
   
   # Structured logging
   logger = structlog.get_logger()
   
   # Error tracking
   sentry_sdk.init(dsn=os.getenv('SENTRY_DSN'))
   ```

3. **CI/CD Pipeline**
   ```yaml
   # .github/workflows/deploy.yml
   name: Deploy Congressional Platform
   on:
     push:
       branches: [main]
   
   jobs:
     deploy:
       runs-on: ubuntu-latest
       steps:
         - uses: actions/checkout@v3
         - name: Build and deploy
           run: |
             docker-compose build
             docker-compose up -d
   ```

## Benefits of Microservices Architecture

### 🚀 Scalability
- **Independent Scaling**: Scale each service based on demand
- **Resource Optimization**: Allocate resources per service needs
- **Horizontal Scaling**: Add more instances as needed

### 🛠 Development
- **Team Autonomy**: Different teams can work on different services
- **Technology Flexibility**: Use best tools for each service
- **Faster Deployment**: Deploy services independently

### 🔧 Operations
- **Fault Isolation**: Service failures don't bring down entire system
- **Independent Updates**: Update services without downtime
- **Better Monitoring**: Service-specific metrics and logging

### 📊 Data Management
- **Separation of Concerns**: Clear data ownership per service
- **Optimized Storage**: Different storage strategies per service
- **Better Caching**: Service-specific caching strategies

## Monitoring and Observability

### Service Health Checks
```python
# Each service implements
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow(),
        "version": os.getenv('SERVICE_VERSION'),
        "uptime": get_uptime()
    }
```

### Metrics Collection
```python
from prometheus_client import Counter, Histogram, generate_latest

# Request metrics
REQUEST_COUNT = Counter('http_requests_total', 'Total HTTP requests', ['method', 'endpoint'])
REQUEST_DURATION = Histogram('http_request_duration_seconds', 'HTTP request duration')

# Data collection metrics
DATA_FETCH_COUNT = Counter('data_fetch_total', 'Total data fetches', ['source', 'congress'])
DATA_FETCH_DURATION = Histogram('data_fetch_duration_seconds', 'Data fetch duration')
```

### Centralized Logging
```python
import structlog

logger = structlog.get_logger()

# Structured logging with context
logger.info(
    "Bill fetched",
    congress=118,
    bill_id="HR_1234",
    duration=1.23,
    records_fetched=1
)
```

## Security Considerations

### Network Security
- All services communicate via private Docker network
- Only frontend and backend exposed through Traefik
- API rate limiting and authentication

### Data Security
- No sensitive data in containers
- Environment variables for secrets
- Regular security updates for base images

### API Security
```python
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer

security = HTTPBearer()

@app.get("/api/v1/admin/stats")
async def get_admin_stats(token: str = Depends(security)):
    if not verify_admin_token(token):
        raise HTTPException(status_code=401)
    return get_system_stats()
```

## Testing Strategy

### Unit Tests
```python
# tests/test_poller.py
import pytest
from poller.collectors import BillCollector

@pytest.fixture
def bill_collector():
    return BillCollector(api_key="test_key")

def test_bill_fetch(bill_collector, mock_api):
    bills = bill_collector.fetch_bills(congress=118, limit=5)
    assert len(bills) == 5
    assert all(bill['congress'] == 118 for bill in bills)
```

### Integration Tests
```python
# tests/test_api_integration.py
import requests

def test_api_bills_endpoint():
    response = requests.get("http://localhost:8000/api/v1/bills?congress=118")
    assert response.status_code == 200
    data = response.json()
    assert 'bills' in data
    assert len(data['bills']) > 0
```

### End-to-End Tests
```python
# tests/test_e2e.py
from playwright.sync_api import sync_playwright

def test_frontend_loads():
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.goto("http://congress.local.team-skynet.io")
        assert page.title() == "Congressional Transparency Platform"
        browser.close()
```

## Performance Optimization

### Caching Strategy
```python
# backend/cache.py
import redis
from functools import wraps

redis_client = redis.Redis(host='redis', port=6379, db=0)

def cache_response(ttl=3600):
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            cache_key = f"{func.__name__}:{hash(str(args) + str(kwargs))}"
            cached = redis_client.get(cache_key)
            if cached:
                return json.loads(cached)
            
            result = await func(*args, **kwargs)
            redis_client.setex(cache_key, ttl, json.dumps(result))
            return result
        return wrapper
    return decorator

@cache_response(ttl=1800)  # 30 minutes
async def get_bills(congress: int, limit: int):
    # Expensive database operation
    pass
```

### Database Optimization
```python
# backend/database.py
from sqlalchemy import create_engine, Index
from sqlalchemy.pool import StaticPool

# SQLite optimization
engine = create_engine(
    "sqlite:///data/metadata.db",
    poolclass=StaticPool,
    connect_args={
        "check_same_thread": False,
        "timeout": 20,
        "isolation_level": None  # Autocommit mode
    },
    echo=False
)

# Add indexes for common queries
Index('idx_bills_congress', Bill.congress)
Index('idx_votes_congress_chamber', Vote.congress, Vote.chamber)
Index('idx_members_congress_party', Member.congress, Member.party)
```

## Rollback Strategy

In case of issues during migration:

1. **Immediate Rollback**
   ```bash
   # Stop microservices
   docker-compose down
   
   # Restart monolithic version
   git checkout pre-microservices
   docker-compose -f docker-compose.legacy.yml up -d
   ```

2. **Data Recovery**
   - All data remains in shared volumes
   - No data migration required for rollback
   - Analysis results preserved

3. **Gradual Migration**
   - Run both versions in parallel
   - Gradually shift traffic to microservices
   - Fallback to monolith if needed

## Success Metrics

### Technical Metrics
- **Response Time**: <200ms for API endpoints
- **Uptime**: 99.9% availability
- **Deployment Time**: <5 minutes for service updates
- **Recovery Time**: <1 minute for service failures

### Operational Metrics
- **Data Freshness**: <1 hour lag for new congressional data
- **Historical Coverage**: 100% for Congresses 113-118
- **API Reliability**: <0.1% error rate
- **Cache Hit Rate**: >80% for common queries

### Development Metrics
- **Build Time**: <10 minutes for full pipeline
- **Test Coverage**: >90% for all services
- **Code Quality**: Zero critical security vulnerabilities
- **Documentation**: 100% API endpoint documentation

## Conclusion

Phase 3 microservices migration will transform the Congressional Transparency Platform into a modern, scalable, and maintainable system. The separation of concerns between data collection, API serving, and frontend presentation will enable independent development, deployment, and scaling of each component.

The migration preserves all existing functionality while adding:
- Better performance through caching and optimization
- Improved reliability through service isolation
- Enhanced monitoring and observability
- Easier maintenance and updates
- Preparation for future enhancements

This architecture positions the platform for long-term success and scalability as congressional transparency needs grow.