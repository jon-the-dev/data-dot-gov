# Historical Congressional Data Fetcher

A comprehensive Python module for collecting historical congressional data from Congresses 113-117 (2013-2023), implementing PHASE2.md Priority 1 requirements.

## Features

### 🎯 Core Capabilities

- **Batch Processing Framework**: Queue-based processing for large-scale historical fetching
- **Progress Tracking**: Real-time progress monitoring with ETA calculations
- **Resumable Downloads**: Automatically resumes interrupted downloads from where they left off
- **Intelligent Rate Limiting**: Enhanced rate limiting with 429 backoff and burst control
- **Data Validation**: Integrity checks with SHA-256 checksums and completeness validation
- **Compressed Storage**: Gzip compression for historical data to save disk space
- **Parallel Processing**: Configurable ThreadPoolExecutor for optimal performance
- **Summary Indices**: Quick lookup indices for efficient data access

### 📊 Data Types Supported

- **Bills**: All bills from Congresses 113-117 with detailed metadata
- **Members**: Congressional members with party affiliations and details
- **House Votes**: House roll call votes with member positions
- **Senate Votes**: Senate roll call votes with member positions

### 🏗️ Architecture

```
data/
└── historical/
    ├── job_queue.pkl          # Persistent job queue
    ├── progress.json          # Progress tracking
    ├── checksums.json         # Data integrity validation
    └── congress_*/
        ├── bills/
        │   ├── raw/           # Original JSON files
        │   ├── compressed/    # Gzipped archives
        │   └── index.json     # Quick lookup index
        ├── members/
        ├── house_votes/
        └── senate_votes/
```

## Installation & Setup

### Prerequisites

```bash
# Required packages
pip install requests python-dotenv tqdm aiohttp

# Environment setup
cp .env.example .env
# Edit .env with your API keys
```

### Configuration

```python
# historical_data_fetcher.py configuration
HISTORICAL_CONFIG = {
    'congresses': [113, 114, 115, 116, 117],
    'batch_size': 100,
    'max_workers': 8,
    'rate_limit': {
        'congress_api': 900,  # requests per hour
        'senate_api': 100,    # requests per minute
    },
    'compression': True,
    'validation': True,
    'resume_on_restart': True
}
```

## Usage

### Command Line Interface

```bash
# Fetch all historical data
python historical_data_fetcher.py --all

# Fetch specific congress
python historical_data_fetcher.py --congress 117

# Fetch specific data types
python historical_data_fetcher.py --bills --members --congress 116

# Resume interrupted fetch
python historical_data_fetcher.py --resume

# Validate existing data
python historical_data_fetcher.py --validate

# Show progress
python historical_data_fetcher.py --status
```

### Python API

```python
from historical_data_fetcher import HistoricalDataFetcher

# Initialize fetcher
fetcher = HistoricalDataFetcher(
    data_dir='data/historical',
    max_workers=8,
    compression=True
)

# Fetch all data for specific congresses
fetcher.fetch_congress_data([113, 114, 115])

# Fetch specific data types
fetcher.fetch_bills(congress=117, batch_size=100)
fetcher.fetch_members(congress=117)
fetcher.fetch_votes(congress=117, chamber='house')

# Monitor progress
progress = fetcher.get_progress()
print(f"Overall progress: {progress['percentage']:.1f}%")
print(f"ETA: {progress['eta']}")

# Validate data integrity
validation_results = fetcher.validate_data()
if validation_results['all_valid']:
    print("All data validation passed")
else:
    print(f"Validation errors: {validation_results['errors']}")
```

## Core Features

### 1. Queue-Based Job Management

```python
class JobQueue:
    def __init__(self, queue_file='job_queue.pkl'):
        self.queue_file = queue_file
        self.jobs = self._load_queue()

    def add_job(self, job_type, congress, **kwargs):
        """Add a job to the queue"""
        job = {
            'id': f"{job_type}_{congress}_{uuid.uuid4().hex[:8]}",
            'type': job_type,
            'congress': congress,
            'status': 'pending',
            'created_at': datetime.utcnow(),
            'retries': 0,
            **kwargs
        }
        self.jobs.append(job)
        self._save_queue()

    def get_next_job(self):
        """Get next pending job"""
        for job in self.jobs:
            if job['status'] == 'pending':
                return job
        return None

    def mark_completed(self, job_id):
        """Mark job as completed"""
        for job in self.jobs:
            if job['id'] == job_id:
                job['status'] = 'completed'
                job['completed_at'] = datetime.utcnow()
                break
        self._save_queue()
```

### 2. Progress Tracking

```python
class ProgressTracker:
    def __init__(self, progress_file='progress.json'):
        self.progress_file = progress_file
        self.progress = self._load_progress()

    def update_progress(self, congress, data_type, completed, total):
        """Update progress for a specific data type"""
        key = f"{congress}_{data_type}"
        self.progress[key] = {
            'completed': completed,
            'total': total,
            'percentage': (completed / total) * 100 if total > 0 else 0,
            'last_updated': datetime.utcnow().isoformat()
        }
        self._save_progress()

    def get_overall_progress(self):
        """Calculate overall progress across all jobs"""
        if not self.progress:
            return {'percentage': 0, 'eta': 'Unknown'}

        total_completed = sum(p['completed'] for p in self.progress.values())
        total_jobs = sum(p['total'] for p in self.progress.values())

        percentage = (total_completed / total_jobs) * 100 if total_jobs > 0 else 0

        # Calculate ETA based on current rate
        if percentage > 0:
            elapsed = self._get_elapsed_time()
            eta_seconds = (elapsed / percentage) * (100 - percentage)
            eta = str(timedelta(seconds=int(eta_seconds)))
        else:
            eta = 'Unknown'

        return {
            'percentage': percentage,
            'completed': total_completed,
            'total': total_jobs,
            'eta': eta
        }
```

### 3. Enhanced Rate Limiting

```python
class IntelligentRateLimit:
    def __init__(self, requests_per_minute=100):
        self.rpm = requests_per_minute
        self.requests = []
        self.backoff_until = None
        self.backoff_multiplier = 1

    async def acquire(self):
        """Acquire permission to make a request"""
        now = time.time()

        # Check if we're in backoff period
        if self.backoff_until and now < self.backoff_until:
            wait_time = self.backoff_until - now
            await asyncio.sleep(wait_time)

        # Remove old requests (older than 1 minute)
        minute_ago = now - 60
        self.requests = [req_time for req_time in self.requests if req_time > minute_ago]

        # Check if we've hit the rate limit
        if len(self.requests) >= self.rpm:
            wait_time = 60 - (now - self.requests[0])
            await asyncio.sleep(wait_time)

        self.requests.append(now)

    def handle_429_response(self, retry_after=None):
        """Handle 429 Too Many Requests response"""
        if retry_after:
            self.backoff_until = time.time() + int(retry_after)
        else:
            # Exponential backoff
            backoff_time = min(300, 60 * self.backoff_multiplier)  # Max 5 minutes
            self.backoff_until = time.time() + backoff_time
            self.backoff_multiplier *= 2
```

### 4. Data Validation & Integrity

```python
class DataValidator:
    def __init__(self, checksums_file='checksums.json'):
        self.checksums_file = checksums_file
        self.checksums = self._load_checksums()

    def calculate_checksum(self, file_path):
        """Calculate SHA-256 checksum for a file"""
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                sha256_hash.update(chunk)
        return sha256_hash.hexdigest()

    def validate_file(self, file_path):
        """Validate file integrity"""
        if not os.path.exists(file_path):
            return False, "File does not exist"

        current_checksum = self.calculate_checksum(file_path)
        expected_checksum = self.checksums.get(file_path)

        if expected_checksum and current_checksum != expected_checksum:
            return False, "Checksum mismatch"

        # Store new checksum
        self.checksums[file_path] = current_checksum
        self._save_checksums()

        return True, "Valid"

    def validate_json_structure(self, file_path, expected_keys):
        """Validate JSON file structure"""
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)

            missing_keys = set(expected_keys) - set(data.keys())
            if missing_keys:
                return False, f"Missing keys: {missing_keys}"

            return True, "Valid structure"
        except json.JSONDecodeError as e:
            return False, f"Invalid JSON: {e}"
```

### 5. Compression & Storage

```python
class CompressedStorage:
    def __init__(self, base_dir):
        self.base_dir = base_dir
        self.compression_level = 6  # Balance between speed and compression

    def compress_file(self, source_path, compressed_path=None):
        """Compress a JSON file with gzip"""
        if not compressed_path:
            compressed_path = source_path + '.gz'

        with open(source_path, 'rb') as f_in:
            with gzip.open(compressed_path, 'wb', compresslevel=self.compression_level) as f_out:
                shutil.copyfileobj(f_in, f_out)

        # Verify compression
        original_size = os.path.getsize(source_path)
        compressed_size = os.path.getsize(compressed_path)
        compression_ratio = compressed_size / original_size

        return {
            'original_size': original_size,
            'compressed_size': compressed_size,
            'compression_ratio': compression_ratio,
            'space_saved': original_size - compressed_size
        }

    def decompress_file(self, compressed_path, output_path=None):
        """Decompress a gzipped file"""
        if not output_path:
            output_path = compressed_path.replace('.gz', '')

        with gzip.open(compressed_path, 'rb') as f_in:
            with open(output_path, 'wb') as f_out:
                shutil.copyfileobj(f_in, f_out)

    def auto_compress_old_data(self, age_days=30):
        """Automatically compress files older than specified days"""
        cutoff_time = time.time() - (age_days * 24 * 60 * 60)

        for root, dirs, files in os.walk(self.base_dir):
            for file in files:
                if file.endswith('.json'):
                    file_path = os.path.join(root, file)
                    if os.path.getmtime(file_path) < cutoff_time:
                        self.compress_file(file_path)
                        os.remove(file_path)  # Remove original after compression
```

## Advanced Features

### 1. Parallel Processing

```python
class ParallelFetcher:
    def __init__(self, max_workers=8):
        self.max_workers = max_workers
        self.rate_limiter = IntelligentRateLimit()

    async def fetch_batch(self, urls, congress, data_type):
        """Fetch a batch of URLs in parallel"""
        async with aiohttp.ClientSession() as session:
            semaphore = asyncio.Semaphore(self.max_workers)

            async def fetch_single(url):
                async with semaphore:
                    await self.rate_limiter.acquire()
                    try:
                        async with session.get(url) as response:
                            if response.status == 429:
                                retry_after = response.headers.get('Retry-After')
                                self.rate_limiter.handle_429_response(retry_after)
                                raise aiohttp.ClientResponseError(
                                    request_info=response.request_info,
                                    history=response.history,
                                    status=429
                                )
                            response.raise_for_status()
                            return await response.json()
                    except Exception as e:
                        logger.error(f"Error fetching {url}: {e}")
                        raise

            tasks = [fetch_single(url) for url in urls]
            results = await asyncio.gather(*tasks, return_exceptions=True)

            return results
```

### 2. Smart Resume Functionality

```python
class ResumeManager:
    def __init__(self, progress_tracker, job_queue):
        self.progress_tracker = progress_tracker
        self.job_queue = job_queue

    def can_resume(self):
        """Check if there are incomplete jobs to resume"""
        return any(job['status'] in ['pending', 'in_progress'] for job in self.job_queue.jobs)

    def get_resume_point(self, congress, data_type):
        """Get the point from which to resume fetching"""
        progress_key = f"{congress}_{data_type}"
        progress = self.progress_tracker.progress.get(progress_key, {})

        return progress.get('completed', 0)

    def cleanup_partial_files(self, congress, data_type):
        """Clean up any partially downloaded files"""
        data_dir = os.path.join(self.base_dir, f"congress_{congress}", data_type)
        temp_files = glob.glob(os.path.join(data_dir, "*.tmp"))

        for temp_file in temp_files:
            os.remove(temp_file)
            logger.info(f"Removed partial file: {temp_file}")
```

### 3. Performance Monitoring

```python
class PerformanceMonitor:
    def __init__(self):
        self.start_time = time.time()
        self.metrics = {
            'requests_made': 0,
            'bytes_downloaded': 0,
            'files_processed': 0,
            'errors_encountered': 0,
            'average_response_time': 0,
            'compression_savings': 0
        }

    def record_request(self, response_time, bytes_downloaded):
        """Record metrics for a request"""
        self.metrics['requests_made'] += 1
        self.metrics['bytes_downloaded'] += bytes_downloaded

        # Update average response time
        current_avg = self.metrics['average_response_time']
        count = self.metrics['requests_made']
        self.metrics['average_response_time'] = (current_avg * (count - 1) + response_time) / count

    def get_performance_report(self):
        """Generate performance report"""
        elapsed = time.time() - self.start_time

        return {
            'elapsed_time': str(timedelta(seconds=int(elapsed))),
            'requests_per_minute': (self.metrics['requests_made'] / elapsed) * 60,
            'download_rate_mbps': (self.metrics['bytes_downloaded'] / elapsed) / (1024 * 1024),
            'files_processed': self.metrics['files_processed'],
            'error_rate': self.metrics['errors_encountered'] / max(1, self.metrics['requests_made']),
            'average_response_time': self.metrics['average_response_time'],
            'total_data_downloaded': self.metrics['bytes_downloaded'] / (1024 * 1024),  # MB
            'compression_savings_mb': self.metrics['compression_savings'] / (1024 * 1024)
        }
```

## Running Historical Data Collection

### Complete Historical Collection

```bash
# Full historical data collection for all congresses
python historical_data_fetcher.py \
    --all \
    --congresses 113,114,115,116,117 \
    --compress \
    --validate \
    --max-workers 8 \
    --batch-size 100
```

### Targeted Collection

```bash
# Collect only bills for Congress 117
python historical_data_fetcher.py \
    --bills \
    --congress 117 \
    --batch-size 50

# Collect votes for multiple congresses
python historical_data_fetcher.py \
    --house-votes \
    --senate-votes \
    --congresses 116,117 \
    --max-workers 4
```

### Monitoring & Maintenance

```bash
# Check collection status
python historical_data_fetcher.py --status

# Validate all collected data
python historical_data_fetcher.py --validate-all

# Compress old data (30+ days)
python historical_data_fetcher.py --compress-old --age-days 30

# Generate collection report
python historical_data_fetcher.py --report
```

## Data Access Patterns

### Quick Access Index

```python
# Each data type has an index for quick lookups
{
    "congress": 117,
    "data_type": "bills",
    "total_records": 12543,
    "last_updated": "2024-01-15T10:30:00Z",
    "files": {
        "raw": "bills/raw/",
        "compressed": "bills/compressed/",
        "index": "bills/index.json"
    },
    "statistics": {
        "by_party": {"R": 6234, "D": 6309},
        "by_chamber": {"house": 8234, "senate": 4309},
        "by_status": {"introduced": 10234, "passed": 1234, "enacted": 75}
    }
}
```

### Efficient Data Loading

```python
class HistoricalDataLoader:
    def load_congress_bills(self, congress, limit=None, offset=0):
        """Load bills efficiently using index"""
        index_path = f"data/historical/congress_{congress}/bills/index.json"
        with open(index_path) as f:
            index = json.load(f)

        bill_files = index['files']['raw'][offset:offset+limit] if limit else index['files']['raw'][offset:]

        bills = []
        for file_path in bill_files:
            with open(file_path) as f:
                bills.append(json.load(f))

        return bills

    def search_historical_data(self, query, congresses=None, data_types=None):
        """Search across historical data"""
        # Implementation for cross-congress search
        pass
```

## Storage Requirements

### Estimated Data Sizes

| Data Type | Per Congress | 5 Congresses | Compressed |
|-----------|-------------|--------------|------------|
| Bills | 2.5 GB | 12.5 GB | 3.1 GB |
| Members | 50 MB | 250 MB | 62 MB |
| House Votes | 1.2 GB | 6.0 GB | 1.5 GB |
| Senate Votes | 800 MB | 4.0 GB | 1.0 GB |
| **Total** | **4.55 GB** | **22.75 GB** | **5.66 GB** |

### Disk Space Management

```python
# Automatic cleanup and archiving
RETENTION_POLICY = {
    'raw_files': 90,      # Keep raw files for 90 days
    'compressed': 365,    # Keep compressed for 1 year
    'indices': 'forever', # Always keep indices
    'checksums': 'forever'# Always keep validation data
}
```

## Troubleshooting

### Common Issues

1. **Rate Limiting**
   ```bash
   # Reduce worker count and batch size
   python historical_data_fetcher.py --max-workers 2 --batch-size 25
   ```

2. **Network Timeouts**
   ```bash
   # Increase timeout and retry settings
   python historical_data_fetcher.py --timeout 60 --retries 5
   ```

3. **Disk Space**
   ```bash
   # Enable compression and cleanup
   python historical_data_fetcher.py --compress --cleanup-old
   ```

4. **Memory Issues**
   ```bash
   # Reduce batch size
   python historical_data_fetcher.py --batch-size 10 --max-workers 2
   ```

### Monitoring Commands

```bash
# Real-time progress monitoring
watch -n 5 "python historical_data_fetcher.py --status"

# Check disk usage
du -sh data/historical/

# Monitor active downloads
netstat -an | grep :443 | wc -l
```

This historical data fetcher provides a robust, scalable solution for collecting comprehensive congressional data across multiple congresses while maintaining data integrity and providing detailed progress tracking.