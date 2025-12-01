#!/usr/bin/env python3
"""Quick script to check if all services are running and accessible."""
import httpx
import sys

SERVICES = [
    ("Dispatcher", "http://localhost:8000/health"),
    ("Network Detector", "http://localhost:8001/health"),
    ("App Detector", "http://localhost:8002/health"),
    ("Visual Detector", "http://localhost:8003/health"),
    ("Risk Engine", "http://localhost:9000/health"),
    ("Response Engine", "http://localhost:9200/health"),
    ("Forensics", "http://localhost:9100/health"),
    ("Blockchain Gateway", "http://localhost:8080/health"),
]

def check_service(name, url):
    try:
        resp = httpx.get(url, timeout=2)
        if resp.status_code == 200:
            return True, "✓ Running"
        else:
            return False, f"✗ Status {resp.status_code}"
    except httpx.ConnectError:
        return False, "✗ Not running (connection refused)"
    except httpx.TimeoutException:
        return False, "✗ Timeout (not responding)"
    except Exception as e:
        return False, f"✗ Error: {type(e).__name__}"

def main():
    print("=" * 60)
    print("SentinelVNC Service Status Check")
    print("=" * 60)
    print()
    
    all_ok = True
    for name, url in SERVICES:
        ok, status = check_service(name, url)
        print(f"{name:25} {status}")
        if not ok:
            all_ok = False
    
    print()
    print("=" * 60)
    if all_ok:
        print("✅ All services are running!")
    else:
        print("❌ Some services are not running!")
        print("\nTo start services, run:")
        print("  cd detectors/dispatcher && uvicorn dispatcher:app --host 0.0.0.0 --port 8000")
        print("  cd detectors/network && uvicorn main:app --host 0.0.0.0 --port 8001")
        print("  cd detectors/app && uvicorn main:app --host 0.0.0.0 --port 8002")
        print("  cd detectors/visual && uvicorn main:app --host 0.0.0.0 --port 8003")
        print("  cd risk_engine && uvicorn main:app --host 0.0.0.0 --port 9000")
        print("  cd response_engine && uvicorn main:app --host 0.0.0.0 --port 9200")
        print("  cd forensics && uvicorn main:app --host 0.0.0.0 --port 9100")
        print("  python -m uvicorn blockchain.gateway:app --host 0.0.0.0 --port 8080")
    print("=" * 60)
    
    return 0 if all_ok else 1

if __name__ == "__main__":
    sys.exit(main())

