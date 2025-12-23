# Railway Deployment Guide

## Overview

Deploy the Shape Graph Visualization app to Railway with game 3821 (Germany vs Japan) data.

## Requirements

### Python Version
- Python 3.10+

### Dependencies
```
streamlit>=1.28.0
matplotlib>=3.7.0
numpy>=1.24.0
scipy>=1.10.0
kloppy>=3.18.0
certifi
```

## Data Files Included

Only game 3821 (Germany vs Japan) is deployed:

| File | Size | Description |
|------|------|-------------|
| `Tracking Data/3821.jsonl.bz2` | 40 MB | Player positions at 29.97 fps |
| `Event Data/3821.json` | 17 MB | Match events (passes, shots, etc.) |
| `Metadata/3821.json` | 1 KB | Match metadata |
| `Rosters/3821.json` | 7.5 KB | Team rosters |
| **Total** | **~57 MB** | |

## Environment Variables

Railway automatically sets these:

| Variable | Description |
|----------|-------------|
| `PORT` | Port number (auto-assigned by Railway) |

The Procfile and .streamlit/config.toml handle server configuration.

## Deployment Steps

### 1. Create Railway Project
1. Go to [railway.app](https://railway.app)
2. Sign in with GitHub
3. Click "New Project"

### 2. Connect GitHub Repository
1. Select "Deploy from GitHub repo"
2. Choose `cryptikhunterz/bacau-prototype`
3. Railway auto-detects Python project

### 3. Deploy
Railway automatically:
- Detects `requirements.txt`
- Installs dependencies
- Uses `Procfile` to start the app

### 4. Verify
1. Wait for build to complete (~2-3 minutes)
2. Click the generated URL
3. App should display with Germany vs Japan match

## Configuration Files

### Procfile
```
web: streamlit run app.py --server.port=$PORT --server.address=0.0.0.0
```

### .streamlit/config.toml
```toml
[server]
headless = true
address = "0.0.0.0"
port = 8501
enableCORS = false
enableXsrfProtection = true

[browser]
gatherUsageStats = false

[theme]
base = "dark"
```

## Potential Issues

### Cold Start Timeout
- **Issue**: First request may timeout while loading tracking data
- **Solution**: Kloppy caches data after first load; subsequent requests are fast

### Memory Usage
- **Issue**: BZ2 decompression uses memory temporarily
- **Solution**: Railway free tier (512MB) should be sufficient for single match

### Build Failures
- **Issue**: Missing dependencies
- **Solution**: Ensure `requirements.txt` matches app.py imports

### Data Not Found
- **Issue**: App can't find data files
- **Solution**: Verify `Fifa world cup 2022 data/` folder is in repo root

## Monitoring

Railway provides:
- Deploy logs
- Runtime logs
- Memory/CPU metrics

Access via Railway dashboard > Project > Deployments.

## Cost

Railway free tier includes:
- 500 hours/month execution
- 512 MB RAM
- 1 GB disk

This is sufficient for demo/testing purposes.
