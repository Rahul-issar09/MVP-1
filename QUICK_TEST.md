# Quick Test - 5 Minute Verification

## Fastest Way to Test Everything

### Step 1: Start Services (2 minutes)

Open 8 terminals and run:

```powershell
# Terminal 1
cd detectors && uvicorn dispatcher:app --port 8000

# Terminal 2
cd detectors/network && uvicorn main:app --port 8001

# Terminal 3
cd detectors/app && uvicorn main:app --port 8002

# Terminal 4
cd detectors/visual && uvicorn main:app --port 8003

# Terminal 5
cd risk_engine && uvicorn main:app --port 9000

# Terminal 6
cd response_engine && uvicorn main:app --port 9200

# Terminal 7
cd forensics && uvicorn main:app --port 9100

# Terminal 8
python -m uvicorn blockchain.gateway:app --port 8080

# Terminal 9 (Optional)
cd dashboard && npm run dev
```

### Step 2: Run Automated Test (30 seconds)

```powershell
python scripts/test_demo_flow.py
```

**Expected:** All ✓ green, incident created

### Step 3: Check Dashboard (30 seconds)

Open: http://localhost:3000

**Expected:** See incidents with risk scores

### Step 4: Verify API (30 seconds)

```powershell
curl http://localhost:9000/incidents
```

**Expected:** JSON array with at least 1 incident

---

## ✅ Success = Ready for Demo!

If all steps pass, your system is working end-to-end.

