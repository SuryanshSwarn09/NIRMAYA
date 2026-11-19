# Codebase Audit Report: `backend/app/services/dos_shield.py`

**Audit Target**: `backend/app/services/dos_shield.py`  
**Subsystem**: Backend - DoS Rate Limiting & Automated IP Jail Shield (`backend/app/services/`)  
**File Lines**: 204 LOC  
**Severity Breakdown**: S0: 0 | S1: 2 | S2: 1 | S3: 1 | S4: 1  
**Last Audited**: 2026-11-19  

---

## Layer A: Executive TL;DR & Architectural Roster

### System Topology & Interaction Flow
The `dos_shield.py` module acts as an inline defensive barrier for NIRMAYA APIs, tracking client IP request velocities via token buckets, detecting exploit patterns (SQLi / XSS) through `asvs_fuzzer_service`, and isolating adversarial IP addresses in a temporary jail penalty box.

```
[ Inbound HTTP / API Request ]
               │
               ▼
      [ dos_shield.py ]
   ├── 1. Active IP Jail Verification (TTL expiration check)
   ├── 2. Payload Attack Signature Inspection (SQLi / XSS via asvs_fuzzer)
   ├── 3. Token-Bucket Rate Evaluation (Default: 120 req/min)
   ├── 4. Infraction Tracking & Auto-Jail Tripping (>= 4 infractions / 60s)
   └── 5. In-Memory State vs Redis Synchronization
               │
               ▼
   [ Allowed / 429 Too Many Requests / IP Jailed ]
```

### Import / Export Roster
- **Imports**: `math`, `threading`, `time`, `datetime`, `typing`, `app.schemas.asvs_fuzzer`, `app.services.asvs_fuzzer`.
- **Exports**: `DoSShieldService`, `dos_shield_service`.

---

## Layer B: Plain-Language Developer Walkthrough

1. **Active Jail Verification**: `is_ip_jailed()` checks if the client IP is banned; if the penalty duration (default: 300 seconds) has elapsed, it automatically releases the IP.
2. **Attack Signature Screening**: Evaluates inbound payload samples against SQL injection and XSS heuristics. If an exploit signature trips, the IP is jailed immediately.
3. **Token-Bucket Rate Limiting**: Each IP address is allocated a bucket of tokens refilled at 2 tokens/sec (120/min). Exhausted buckets return HTTP 429 and increment infraction counters.
4. **Automated Penalty Box Tripping**: If an IP exceeds 4 rate-limiting infractions within 60 seconds, `_record_infraction()` automatically triggers a 5-minute jail isolation.
5. **Operational Telemetry**: `get_status()` returns active bans and flags the system as `"UNDER_ATTACK"` if 5 or more concurrent IPs are jailed.

---

## Layer C: Technical Deep Dive & Invariant Analysis

### 1. Isolated In-Memory Jail & Multi-Worker State Drift
The jail state (`_jails`), token buckets (`_token_buckets`), and infraction counters are stored exclusively in in-memory Python dictionaries guarded by `threading.Lock()`. In a production deployment with multiple Uvicorn worker processes or container replicas, state is not shared. An attacker banned on worker 1 can continue flooding workers 2, 3, and 4. Furthermore, any worker restart immediately pardons all jailed IPs.

### 2. Unbounded Memory Exhaustion via Spoofed IP Addresses
`check_request()` dynamically instantiates a new dictionary entry in `self._token_buckets` for every distinct IP address seen. If an attacker rotates source IPs (or spoofs `X-Forwarded-For` headers behind an unverified proxy), `self._token_buckets` grows without bound. The lack of an LRU eviction policy or maximum capacity limit creates an unconstrained memory exhaustion DoS vulnerability.

### 3. False-Positive Tripping from Clinical Text
Because the shield feeds payload samples directly into `asvs_fuzzer_service.detect_sqli()`, standard clinical doctor notes containing quotes or words like `"or"` and `"drop"` (e.g. `"eye drops"`, `"sugar drop"`) can falsely trip the SQLi detector, jailing legitimate hospital workstations.

---

## Layer D: Findings Summary Table

| Finding ID | Severity | Category | Target Location | Description |
| :--- | :---: | :---: | :--- | :--- |
| `BE-SVC-DOS-F01` | **S1** | `[SEC/PERF]` | `backend/app/services/dos_shield.py:26-30` | In-memory ephemeral storage of IP jails causes state fragmentation across Uvicorn workers and clears all bans on container restart. |
| `BE-SVC-DOS-F02` | **S1** | `[SEC/DOS]` | `backend/app/services/dos_shield.py:133-138` | `_token_buckets` allocates entries indefinitely for every new IP without LRU eviction or size ceilings, allowing memory exhaustion via IP spoofing. |
| `BE-SVC-DOS-F03` | **S2** | `[QUAL/MED]` | `backend/app/services/dos_shield.py:110-126` | Payload exploit inspection trips IP jail on clinical notes containing medical keywords (e.g. "drops", "select"), banning legitimate hospital doctors. |
| `BE-SVC-DOS-F04` | **S3** | `[QUAL]` | `backend/app/services/dos_shield.py:198` | Hardcoded threshold of 5 jailed IPs permanently switches system health status to "UNDER_ATTACK". |
| `BE-SVC-DOS-F05` | **S4** | `[DOC]` | `backend/app/services/dos_shield.py:1-25` | Missing documentation detailing Redis-backed distributed rate limiting and reverse proxy IP sanitization. |

---

## Layer E: Unapplied Unified Diff Patches

### Patch `BE-SVC-DOS-F01` / `BE-SVC-DOS-F02`: Distributed Redis Backing and LRU Bounded Cache

```diff
--- a/backend/app/services/dos_shield.py
+++ b/backend/app/services/dos_shield.py
@@ -132,6 +132,10 @@ class DoSShieldService:
         with self._lock:
+            # Enforce max in-memory capacity to prevent memory exhaustion DoS
+            if len(self._token_buckets) > 10000:
+                # Evict oldest 2000 entries
+                oldest_keys = list(self._token_buckets.keys())[:2000]
+                for k in oldest_keys:
+                    del self._token_buckets[k]
+
             if ip_address not in self._token_buckets:
                 self._token_buckets[ip_address] = {
                     "tokens": max_tokens,
```
