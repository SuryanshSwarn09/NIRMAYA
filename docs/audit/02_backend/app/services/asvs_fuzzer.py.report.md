# Technical Audit Report: backend/app/services/asvs_fuzzer.py

## Layer A: Executive TL;DR & Architectural Roster

### Executive Summary
`backend/app/services/asvs_fuzzer.py` implements an automated defensive fuzzing, pattern detection, and sanitization engine for SQL Injection (SQLi) and Cross-Site Scripting (XSS), aligned with OWASP ASVS Level 2 requirements. It maintains a curated corpus of adversarial attack payloads (tautologies, stacked queries, UNION selects, reflected script tags, event handlers, JavaScript URIs) and evaluates incoming strings against compiled regex signatures. The audit revealed two primary vulnerabilities: an overly aggressive SQLi regex pattern (`--|#|\/\*`) that causes severe false positives on benign clinical notes (e.g. bullet points or medication `#1 tab` notation), and an incomplete XSS protocol filter that fails against encoded URIs and data protocols.

### Architectural Roster
- **Module Name:** `backend/app/services/asvs_fuzzer.py`
- **Primary Responsibility:** Defensive evaluation of text payloads against SQLi and XSS attack patterns and HTML output sanitization.
- **Upstream Dependencies:**
  - `html`, `re`, `time`, `uuid`
  - `app.schemas.asvs_fuzzer` (`FuzzingAttackType`, `FuzzingReport`, `FuzzingResultItem`)
- **Downstream Consumers:**
  - `backend/app/api/v1/endpoints/asvs_audit.py`
  - Input validation middleware / pre-persistence sanitizers
- **Exported Symbols:**
  - `ASVSFuzzerService`
  - `asvs_fuzzer_service`

```
+-----------------------------------------------------------------------------------+
|                        ASVS Defensive Fuzzing & Sanitization                      |
|                                                                                   |
|  [Fuzzing Client / Request Input]                                                 |
|          |                                                                        |
|          +--> [detect_sqli(raw_input)]                                            |
|          |         +--> Evaluates 9 regex patterns (UNION, stacked, comment markers) |
|          |                                                                        |
|          +--> [detect_xss(raw_input)]                                             |
|          |         +--> Evaluates script tags, onload/onerror, javascript:         |
|          |                                                                        |
|          +--> [sanitize_clinical_input(raw_text)]                                 |
|          |         |-- Replace 'javascript:' with 'blocked-scheme:'               |
|          |         +--> html.escape(cleaned, quote=True)                          |
|          |                                                                        |
|          +--> [run_comprehensive_fuzz_suite()]                                    |
|                    +--> Compiles FuzzingReport (Effectiveness % & Status)         |
+-----------------------------------------------------------------------------------+
```

---

## Layer B: Plain-Language Developer Walkthrough

This module tests and demonstrates how NIRMAYA repels common web application injection attacks:

1. **Adversarial Payload Corpora (`SQLI_PAYLOADS`, `XSS_PAYLOADS`):** Contains curated offensive vectors covering tautologies (`' OR '1'='1`), UNION extraction (`' UNION SELECT null, null, username, password FROM users --`), destructive stacked queries (`'; DROP TABLE patients; --`), reflected script injection (`<script>alert('xss')</script>`), and payload-carrying image tags (`<img src=x onerror=alert(document.cookie)>`).
2. **SQLi Detection (`detect_sqli`):** Scans candidate text against compiled regular expressions looking for common SQL injection idioms, including SQL comment markers (`--`, `#`, `/*`), time delays (`pg_sleep`), and boolean tautologies.
3. **XSS Detection & Sanitization (`detect_xss`, `sanitize_clinical_input`):** Detects script tags, inline event handlers (`onload`, `onerror`), and `javascript:` pseudo-protocols. `sanitize_clinical_input` neutralizes dangerous schemes and converts characters (`<`, `>`, `&`, `"`, `'`) into harmless HTML entities via `html.escape`.
4. **Benchmark Suite Execution (`run_comprehensive_fuzz_suite`):** Iterates over the entire corpus, recording whether each payload was detected, blocked, or neutralized, and calculates an overall defense effectiveness rate (e.g. 100% with status `SECURE`).

---

## Layer C: Technical Deep Dive & Invariant Analysis

### Invariant & Security Standards
- **Output Encoding:** Any text containing HTML markup must be escaped prior to rendering in client contexts to prevent DOM-based XSS.
- **Fail-Secure Defense:** Any vector presenting an unneutralized high-risk attack must transition the report status from `SECURE` to `VULNERABLE`.

### Vulnerabilities & Operational Risks
- **High False-Positive Rate on Medical Data:** Pattern 9 in `_SQLI_PATTERNS` (line 77) matches `r"(--|#|\/\*)"`. In clinical practice, physicians routinely write `--` (dashes for bullet lists, horizontal dividers, or negative findings) and `#` (e.g. `#1 Tab Paracetamol`, `#2 Fracture Left Femur`). Flagging these valid clinical notes as malicious SQL injection disrupts doctor workflow and risks rejecting vital medical documentation.
- **Incomplete Protocol Sanitization:** Line 116 performs a naive regex substitution `re.sub(r"javascript\s*:", "blocked-scheme:", raw_text)`. This does not account for `data:text/html;base64,...` URIs, vbscript protocols, or Unicode-obfuscated characters that bypass simple regex matchers.
- **Unused Latency Timing:** `test_sqli_defenses`, `test_xss_defenses`, and `run_comprehensive_fuzz_suite` record `start = time.perf_counter()`, but the elapsed duration is never passed to `_build_report` or included in the returned `FuzzingReport` schema.

---

## Layer D: Findings Summary Table

| Finding ID | Severity | Category | Target | Description |
|:---|:---:|:---:|:---|:---|
| `BE-SVC-FUZ-F01` | **S2** | `[QUAL]` | `asvs_fuzzer.py:77` | SQLi pattern `(--\|#\|\/\*)` triggers severe false positives on valid medical notes containing bullet dashes or prescription pound signs (#). |
| `BE-SVC-FUZ-F02` | **S2** | `[SEC]` | `asvs_fuzzer.py:116` | Naive regex neutralization of `javascript:` fails against `data:text/html` schemes and encoded URI bypasses. |
| `BE-SVC-FUZ-F03` | **S3** | `[PERF]` | `asvs_fuzzer.py:161, 186, 211, 222` | Execution latency measured via `time.perf_counter()` is discarded and never reported in `FuzzingReport`. |
| `BE-SVC-FUZ-F04` | **S4** | `[QUAL]` | `asvs_fuzzer.py:134-140` | Fuzzer states SQLi is "BLOCKED" based on regex detection, whereas real SQLi defense relies on SQLAlchemy parameter binding. |

---

## Layer E: Unapplied Unified Diff Patches

### Patch: Contextual SQLi Comment Regex & Data Scheme Sanitization (`BE-SVC-FUZ-F01`, `BE-SVC-FUZ-F02`)

```diff
--- a/backend/app/services/asvs_fuzzer.py
+++ b/backend/app/services/asvs_fuzzer.py
@@ -74,7 +74,8 @@ class ASVSFuzzerService:
         re.compile(r"(;\s*UPDATE\s+[a-zA-Z0-9_]+\s+SET)", re.IGNORECASE),
         re.compile(r"(pg_sleep\s*\(\s*\d+\s*\))", re.IGNORECASE),
         re.compile(r"(WAITFOR\s+DELAY)", re.IGNORECASE),
-        re.compile(r"(--|#|\/\*)", re.IGNORECASE),
+        # Context-aware comment matching (requires quote or statement terminator prefix)
+        re.compile(r"(['\"];\s*(--|#|\/\*)|['\"]\s*(--|#|\/\*))", re.IGNORECASE),
     ]
 
     # Compiled XSS detection signatures
@@ -113,8 +114,8 @@ class ASVSFuzzerService:
         if not raw_text:
             return raw_text, False
 
-        # First neutralize dangerous script protocols
-        cleaned = re.sub(r"javascript\s*:", "blocked-scheme:", raw_text, flags=re.IGNORECASE)
+        # First neutralize dangerous script and data protocols
+        cleaned = re.sub(r"(javascript|data|vbscript)\s*:", "blocked-scheme:", raw_text, flags=re.IGNORECASE)
 
         # Standard HTML entity escape
         escaped = html.escape(cleaned, quote=True)
```
