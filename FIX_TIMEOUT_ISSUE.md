# Fix: Timeout Issue in Attack Simulator

## Problem
The attack simulator was timing out when sending events to the dispatcher. The dispatcher was blocking while waiting for the full detection chain (detector → risk engine) to complete.

## Root Cause
1. **Dispatcher was blocking**: Waiting for detector response before returning
2. **Detector was blocking**: Waiting for Risk Engine response
3. **Chain timeout**: Full chain could take >2 seconds, causing timeouts

## Solution

### 1. Made Dispatcher Fire-and-Forget
- Dispatcher now returns immediately after queuing event to detector
- Uses `asyncio.create_task()` to forward in background
- Prevents blocking on the full detection chain

**File**: `detectors/dispatcher.py`
```python
# Fire-and-forget: Don't wait for detector response
async def forward_to_detector():
    # ... forward logic ...
    
# Start forwarding in background, don't await
asyncio.create_task(forward_to_detector())

# Return immediately
return {"status": "ok", "routed_to": detector_name}
```

### 2. Increased Timeouts
- Attack simulator timeout: 2.0s → 5.0s
- Dispatcher detector timeout: 2.0s → 5.0s
- Better error handling for timeout exceptions

**File**: `scripts/demo_attack_simulator.py`

### 3. Improved Error Handling
- Better error messages
- Continues on errors (doesn't fail completely)
- Shows success count vs total attempts

## Testing

After these fixes, the attack simulator should:
1. ✅ Send events without timing out
2. ✅ Return quickly (dispatcher responds immediately)
3. ✅ Process events in background
4. ✅ Show progress even if some events fail

## How to Test

```powershell
# Make sure all services are running, then:
python scripts/demo_attack_simulator.py --attack clipboard --intensity high
```

Expected output:
```
🔴 [ATTACK] Clipboard Exfiltration Attack
   Session: abc12345...
   Intensity: high
   Performing 15 clipboard operations...
   ✓ Operation 1/15 - 3000 bytes
   ✓ Operation 5/15 - 3000 bytes
   ...
   ✓ Completed 15/15 operations successfully
   ✅ Attack complete!
```

## Notes

- Events are still processed fully (detector → risk engine → response)
- Dispatcher just doesn't wait for the full chain
- This matches the proxy's fire-and-forget pattern
- Better for high-throughput scenarios

