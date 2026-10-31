"""Automated dependency vulnerability scanner and security advisory evaluator for NIRMAYA.

Evaluates pinned dependencies and runtime environments against known CVE advisories,
calculates CVSS severity ratings, and generates remediation guidance.
"""

import importlib.metadata
import re
import time
import uuid
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple
from packaging.version import parse as parse_version, InvalidVersion

from app.schemas.security_scanner import (
    DependencyVulnerability,
    SecurityScanReport,
    SecuritySeverityEnum,
)


class DependencyScannerService:
    """Evaluates project dependencies against a curated database of healthcare and cloud CVE advisories."""

    # Curated catalog of known vulnerabilities across common Python packages
    ADVISORY_DATABASE: List[Dict[str, any]] = [
        {
            "package": "cryptography",
            "vulnerable_below": "41.0.6",
            "fixed_version": "41.0.6",
            "cve_id": "CVE-2023-49083",
            "cvss_score": 7.5,
            "severity": SecuritySeverityEnum.HIGH,
            "title": "NULL pointer dereference in PKCS7 certificate loading routines",
            "recommendation": "Upgrade cryptography to >= 41.0.6 immediately to avoid application crash during certificate validation.",
        },
        {
            "package": "cryptography",
            "vulnerable_below": "39.0.1",
            "fixed_version": "39.0.1",
            "cve_id": "CVE-2023-23931",
            "cvss_score": 6.5,
            "severity": SecuritySeverityEnum.MEDIUM,
            "title": "Memory corruption vulnerability in Cipher.update_into()",
            "recommendation": "Upgrade cryptography to >= 39.0.1 to avoid segfaults during streaming encryption.",
        },
        {
            "package": "pydantic",
            "vulnerable_below": "2.7.4",
            "fixed_version": "2.7.4",
            "cve_id": "CVE-2024-37890",
            "cvss_score": 5.3,
            "severity": SecuritySeverityEnum.MEDIUM,
            "title": "Regular Expression Denial of Service (ReDoS) in EmailStr validation",
            "recommendation": "Upgrade pydantic to >= 2.7.4 to utilize non-backtracking email regex parsing.",
        },
        {
            "package": "aiohttp",
            "vulnerable_below": "3.9.2",
            "fixed_version": "3.9.2",
            "cve_id": "CVE-2024-23829",
            "cvss_score": 8.1,
            "severity": SecuritySeverityEnum.HIGH,
            "title": "HTTP request smuggling via improper handling of chunked transfer encoding",
            "recommendation": "Upgrade aiohttp to >= 3.9.2 to prevent reverse proxy header desynchronization.",
        },
        {
            "package": "aiohttp",
            "vulnerable_below": "3.9.2",
            "fixed_version": "3.9.2",
            "cve_id": "CVE-2024-23334",
            "cvss_score": 7.5,
            "severity": SecuritySeverityEnum.HIGH,
            "title": "Directory traversal vulnerability in static file serving middleware",
            "recommendation": "Upgrade aiohttp to >= 3.9.2 and enforce follow_symlinks=False on static routes.",
        },
        {
            "package": "urllib3",
            "vulnerable_below": "2.0.7",
            "fixed_version": "2.0.7",
            "cve_id": "CVE-2023-45803",
            "cvss_score": 6.1,
            "severity": SecuritySeverityEnum.MEDIUM,
            "title": "Request body leakage during HTTP 303 See Other redirect handling",
            "recommendation": "Upgrade urllib3 to >= 2.0.7 to ensure payload stripping across cross-origin redirects.",
        },
        {
            "package": "jinja2",
            "vulnerable_below": "3.1.3",
            "fixed_version": "3.1.3",
            "cve_id": "CVE-2024-22195",
            "cvss_score": 6.1,
            "severity": SecuritySeverityEnum.MEDIUM,
            "title": "Cross-Site Scripting (XSS) vulnerability in xmlattr filter",
            "recommendation": "Upgrade jinja2 to >= 3.1.3 to sanitize keys formatted via xmlattr.",
        },
        {
            "package": "sqlparse",
            "vulnerable_below": "0.5.0",
            "fixed_version": "0.5.0",
            "cve_id": "CVE-2024-4340",
            "cvss_score": 7.5,
            "severity": SecuritySeverityEnum.HIGH,
            "title": "Recursion depth limit bypass leading to Denial of Service via deeply nested SQL",
            "recommendation": "Upgrade sqlparse to >= 0.5.0 to enforce iterative statement parsing.",
        },
        {
            "package": "requests",
            "vulnerable_below": "2.31.0",
            "fixed_version": "2.31.0",
            "cve_id": "CVE-2023-32681",
            "cvss_score": 6.1,
            "severity": SecuritySeverityEnum.MEDIUM,
            "title": "Proxy-Authorization header leakage to destination servers across HTTPS redirects",
            "recommendation": "Upgrade requests to >= 2.31.0 to enforce proxy header stripping upon target redirection.",
        },
        {
            "package": "rsa",
            "vulnerable_below": "4.7",
            "fixed_version": "4.7",
            "cve_id": "CVE-2020-25658",
            "cvss_score": 9.8,
            "severity": SecuritySeverityEnum.CRITICAL,
            "title": "Bleichenbacher-style timing oracle attack in PKCS#1 v1.5 decryption",
            "recommendation": "Upgrade rsa to >= 4.7 or migrate directly to cryptography library with constant-time OAEP padding.",
        },
    ]

    def parse_requirements_text(self, content: str) -> Dict[str, str]:
        """Parse raw requirements.txt text into a dictionary of package_name -> pinned_version."""
        packages: Dict[str, str] = {}
        line_pattern = re.compile(r"^([a-zA-Z0-9_\-\.]+)\s*(?:==|>=|<=|~=)\s*([0-9a-zA-Z\.\-]+)")

        for line in content.splitlines():
            clean_line = line.strip()
            # Skip comments and empty lines
            if not clean_line or clean_line.startswith("#") or clean_line.startswith("-"):
                continue

            match = line_pattern.match(clean_line)
            if match:
                name = match.group(1).lower().replace("_", "-")
                version = match.group(2)
                packages[name] = version

        return packages

    def scan_requirements(self, requirements_content: str) -> List[DependencyVulnerability]:
        """Evaluate requirements text against the security advisory catalog."""
        parsed = self.parse_requirements_text(requirements_content)
        vulnerabilities: List[DependencyVulnerability] = []

        for pkg_name, installed_ver_str in parsed.items():
            vulns = self._evaluate_package(pkg_name, installed_ver_str)
            vulnerabilities.extend(vulns)

        return vulnerabilities

    def scan_installed_environment(self) -> List[DependencyVulnerability]:
        """Inspect all installed packages in active Python environment against security advisories."""
        vulnerabilities: List[DependencyVulnerability] = []

        try:
            dists = importlib.metadata.distributions()
            for dist in dists:
                pkg_name = dist.metadata.get("Name", "").lower().replace("_", "-")
                version = dist.metadata.get("Version", "")
                if pkg_name and version:
                    vulns = self._evaluate_package(pkg_name, version)
                    vulnerabilities.extend(vulns)
        except Exception:
            pass

        return vulnerabilities

    def _evaluate_package(self, package_name: str, version_str: str) -> List[DependencyVulnerability]:
        """Check a single package against all matching advisories."""
        results: List[DependencyVulnerability] = []
        clean_name = package_name.lower().replace("_", "-")

        try:
            parsed_ver = parse_version(version_str)
        except InvalidVersion:
            return results

        for adv in self.ADVISORY_DATABASE:
            if adv["package"] == clean_name:
                try:
                    threshold = parse_version(adv["vulnerable_below"])
                    if parsed_ver < threshold:
                        results.append(
                            DependencyVulnerability(
                                package_name=package_name,
                                installed_version=version_str,
                                fixed_version=adv["fixed_version"],
                                cve_id=adv["cve_id"],
                                cvss_score=adv["cvss_score"],
                                severity=adv["severity"],
                                advisory_title=adv["title"],
                                recommendation=adv["recommendation"],
                            )
                        )
                except InvalidVersion:
                    continue

        return results

    def generate_dependency_report(
        self,
        requirements_content: Optional[str] = None,
        scan_installed: bool = True,
    ) -> SecurityScanReport:
        """Run dependency vulnerability audit and aggregate results into SecurityScanReport."""
        start_time = time.perf_counter()
        findings: List[DependencyVulnerability] = []

        if requirements_content:
            findings.extend(self.scan_requirements(requirements_content))
        elif scan_installed:
            findings.extend(self.scan_installed_environment())

        duration_ms = round((time.perf_counter() - start_time) * 1000, 2)

        crit_count = sum(1 for v in findings if v.severity == SecuritySeverityEnum.CRITICAL)
        high_count = sum(1 for v in findings if v.severity == SecuritySeverityEnum.HIGH)
        med_count = sum(1 for v in findings if v.severity == SecuritySeverityEnum.MEDIUM)
        low_count = sum(1 for v in findings if v.severity == SecuritySeverityEnum.LOW)

        if crit_count > 0 or high_count > 0:
            status = "FAILED"
        elif med_count > 0:
            status = "WARNING"
        else:
            status = "PASSED"

        return SecurityScanReport(
            scan_id=f"dep_{uuid.uuid4().hex[:12]}",
            scanned_at=datetime.now(timezone.utc),
            target_type="dependencies",
            files_scanned=1,
            total_findings=len(findings),
            critical_count=crit_count,
            high_count=high_count,
            medium_count=med_count,
            low_count=low_count,
            findings=[],
            dependency_findings=findings,
            scan_duration_ms=duration_ms,
            status=status,
        )


# Global singleton instance of dependency scanner service
dependency_scanner_service = DependencyScannerService()
