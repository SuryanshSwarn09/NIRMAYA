"""Distributed DoS Rate-Limiting Shield and Automated IP Jail Penalty Box for NIRMAYA.

Provides sliding-window rate tracking, attack signature tripping, and automated
temporary isolation of adversarial or abusive client IP addresses.
"""

import math
import threading
import time
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional, Tuple

from app.schemas.asvs_fuzzer import DoSShieldStatus, IPJailRecord
from app.services.asvs_fuzzer import asvs_fuzzer_service


class DoSShieldService:
    """Enterprise rate-limiting shield and IP jail manager."""

    DEFAULT_CAPACITY: int = 120  # requests per minute
    DEFAULT_PENALTY_SECONDS: int = 300  # 5 minutes jail
    MAX_INFRACTIONS_BEFORE_JAIL: int = 4

    def __init__(self):
        self._lock = threading.Lock()
        self._jails: Dict[str, IPJailRecord] = {}
        self._token_buckets: Dict[str, Dict[str, float]] = {}  # ip -> {tokens, last_updated}
        self._infraction_counters: Dict[str, Dict[str, any]] = {}  # ip -> {count, window_start}
        self._total_infractions_today: int = 0
        self._redis_connected: bool = False

    def clear(self) -> None:
        """Reset all active token buckets, infraction counters, and IP jails."""
        with self._lock:
            self._jails.clear()
            self._token_buckets.clear()
            self._infraction_counters.clear()
            self._total_infractions_today = 0

    def is_ip_jailed(self, ip_address: str) -> Tuple[bool, Optional[IPJailRecord]]:
        """Verify whether an IP address is currently restricted under an active jail penalty."""
        with self._lock:
            record = self._jails.get(ip_address)
            if not record:
                return False, None

            now = datetime.now(timezone.utc)
            if now > record.expires_at:
                # Ban has elapsed; automatically release
                del self._jails[ip_address]
                return False, None

            return True, record

    def jail_ip(
        self,
        ip_address: str,
        reason: str,
        penalty_seconds: Optional[int] = None,
    ) -> IPJailRecord:
        """Place a client IP address in the penalty box."""
        duration = penalty_seconds or self.DEFAULT_PENALTY_SECONDS
        now = datetime.now(timezone.utc)
        expires = now + timedelta(seconds=duration)

        with self._lock:
            existing = self._jails.get(ip_address)
            infractions = (existing.infraction_count + 1) if existing else 1
            self._total_infractions_today += 1

            record = IPJailRecord(
                ip_address=ip_address,
                jailed_at=now,
                expires_at=expires,
                penalty_seconds=duration,
                infraction_count=infractions,
                reason=reason,
                is_active=True,
            )
            self._jails[ip_address] = record
            return record

    def release_ip(self, ip_address: str) -> bool:
        """Manually unban and release an IP address from jail."""
        with self._lock:
            if ip_address in self._jails:
                del self._jails[ip_address]
                return True
            return False

    def check_request(
        self,
        ip_address: str,
        payload_sample: Optional[str] = None,
        capacity: Optional[int] = None,
    ) -> Tuple[bool, int, int, Optional[str]]:
        """Assess inbound request against IP jail and token-bucket capacity.

        Returns:
            Tuple of (is_allowed, remaining_tokens, retry_after_seconds, rejection_reason)
        """
        # 1. Check if IP is currently jailed
        is_jailed, jail_record = self.is_ip_jailed(ip_address)
        if is_jailed and jail_record:
            now = datetime.now(timezone.utc)
            retry_after = max(1, int((jail_record.expires_at - now).total_seconds()))
            return False, 0, retry_after, f"IP_JAILED: {jail_record.reason}"

        # 2. Inspect payload for high-severity exploit signatures (SQLi / XSS)
        if payload_sample:
            sqli_detected, sqli_match = asvs_fuzzer_service.detect_sqli(payload_sample)
            if sqli_detected:
                self.jail_ip(
                    ip_address,
                    reason=f"EXPLOIT_SIGNATURE_DETECTED: SQLi pattern '{sqli_match}'",
                )
                return False, 0, self.DEFAULT_PENALTY_SECONDS, "IP_JAILED: SQL Injection Exploit Attempt"

            xss_detected, xss_match = asvs_fuzzer_service.detect_xss(payload_sample)
            if xss_detected:
                self.jail_ip(
                    ip_address,
                    reason=f"EXPLOIT_SIGNATURE_DETECTED: XSS pattern '{xss_match}'",
                )
                return False, 0, self.DEFAULT_PENALTY_SECONDS, "IP_JAILED: Cross-Site Scripting Exploit Attempt"

        # 3. Token bucket rate evaluation
        max_tokens = float(capacity or self.DEFAULT_CAPACITY)
        refill_rate = max_tokens / 60.0  # tokens per second
        now_ts = time.time()

        with self._lock:
            if ip_address not in self._token_buckets:
                self._token_buckets[ip_address] = {
                    "tokens": max_tokens,
                    "last_updated": now_ts,
                }

            bucket = self._token_buckets[ip_address]
            elapsed = now_ts - bucket["last_updated"]
            bucket["last_updated"] = now_ts
            bucket["tokens"] = min(max_tokens, bucket["tokens"] + elapsed * refill_rate)

            if bucket["tokens"] >= 1.0:
                bucket["tokens"] -= 1.0
                remaining = int(bucket["tokens"])
                return True, remaining, 0, None
            else:
                deficit = 1.0 - bucket["tokens"]
                retry_after = max(1, math.ceil(deficit / refill_rate))

                # Track rate limit infractions for automated jail tripping
                self._record_infraction(ip_address)
                return False, 0, retry_after, "RATE_LIMIT_EXCEEDED"

    def _record_infraction(self, ip_address: str) -> None:
        """Record a rate limit violation and trip the IP jail if threshold is reached."""
        now_ts = time.time()
        tracker = self._infraction_counters.get(ip_address)

        if not tracker or (now_ts - tracker["window_start"]) > 60.0:
            self._infraction_counters[ip_address] = {
                "count": 1,
                "window_start": now_ts,
            }
        else:
            tracker["count"] += 1
            if tracker["count"] >= self.MAX_INFRACTIONS_BEFORE_JAIL:
                # Trip jail penalty
                self.jail_ip(
                    ip_address,
                    reason=f"REPEATED_RATE_LIMIT_ABUSE: {tracker['count']} violations within 60s",
                )
                # Reset counter
                del self._infraction_counters[ip_address]

    def get_active_jails(self) -> List[IPJailRecord]:
        """List all currently active IP jail penalty records."""
        with self._lock:
            now = datetime.now(timezone.utc)
            active: List[IPJailRecord] = []
            for ip, record in list(self._jails.items()):
                if now <= record.expires_at:
                    active.append(record)
                else:
                    del self._jails[ip]
            return active

    def get_status(self) -> DoSShieldStatus:
        """Collect operational telemetry for the DoS shield."""
        active_jails = self.get_active_jails()
        return DoSShieldStatus(
            shield_mode="DISTRIBUTED_TOKEN_BUCKET_WITH_IP_JAIL",
            redis_connected=self._redis_connected,
            total_active_jails=len(active_jails),
            total_infractions_today=self._total_infractions_today,
            jailed_ips=active_jails,
            status="UNDER_ATTACK" if len(active_jails) >= 5 else "PROTECTED",
        )


# Global singleton instance of DoS shield service
dos_shield_service = DoSShieldService()

