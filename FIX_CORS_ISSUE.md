# Fix: CORS Error in Dashboard

## Problem
The dashboard at `http://localhost:3000` was blocked from accessing the Risk Engine API at `http://localhost:9000` due to CORS (Cross-Origin Resource Sharing) policy.

**Error Messages:**
```
Access to XMLHttpRequest at 'http://localhost:9000/incidents' from origin 'http://localhost:3000' 
has been blocked by CORS policy: No 'Access-Control-Allow-Origin' header is present on the requested resource.
```

## Root Cause
The Risk Engine and Blockchain Gateway FastAPI services didn't have CORS middleware configured, so browsers blocked cross-origin requests from the dashboard.

## Solution

### 1. Added CORS Middleware to Risk Engine
**File**: `risk_engine/main.py`

Added CORS middleware to allow requests from the dashboard:
```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### 2. Added CORS Middleware to Blockchain Gateway
**File**: `blockchain/gateway.py`

Added CORS middleware since the dashboard may call it directly for verification:
```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

## What This Fixes

✅ Dashboard can now fetch incidents from Risk Engine  
✅ Dashboard can verify blockchain integrity  
✅ No more CORS errors in browser console  
✅ API calls work from dashboard  

## Testing

1. **Restart Risk Engine**:
   ```powershell
   cd risk_engine
   uvicorn main:app --port 9000
   ```

2. **Restart Blockchain Gateway** (if needed):
   ```powershell
   python -m uvicorn blockchain.gateway:app --port 8080
   ```

3. **Open Dashboard**: http://localhost:3000

4. **Check Browser Console**: Should see no CORS errors

5. **Verify**: Dashboard should display real incidents from API

## Production Note

For production, replace `allow_origins=["*"]` with specific origins:
```python
allow_origins=[
    "https://your-dashboard-domain.com",
    "https://www.your-dashboard-domain.com"
]
```

This prevents unauthorized websites from accessing your API.

## Services with CORS

| Service | CORS Status | Notes |
|---------|-------------|-------|
| Risk Engine | ✅ Added | Dashboard needs this |
| Blockchain Gateway | ✅ Added | Dashboard may call directly |
| Forensics | ✅ Already had | Was already configured |
| Response Engine | ❌ Not needed | Backend-to-backend only |
| Detectors | ❌ Not needed | Backend-to-backend only |
| Dispatcher | ❌ Not needed | Backend-to-backend only |

