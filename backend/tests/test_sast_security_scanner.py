"""Comprehensive test suite for Static Application Security Testing (SAST),
automated dependency vulnerability auditing, and multi-tenant database connection pool telemetry.
"""

import pytest
from fastapi.testclient import TestClient

from app.db.session import get_pool_metrics
from app.db.tenant_context import (
    apply_tenant_context_to_session,
    get_current_tenant_context,
    set_current_tenant_context,
)
from app.main import app
from app.schemas.security_scanner import (
    SecurityCategoryEnum,
    SecuritySeverityEnum,
    TenantContextParams,
)
from app.services.dependency_scanner import dependency_scanner_service
from app.services.security_scanner import security_scanner_service


@pytest.fixture
def test_client() -> TestClient:
    """FastAPI TestClient fixture."""
    return TestClient(app)


def test_sast_clean_code_passes():
    """Verify that secure, idiomatic Python code produces zero security findings and PASSED status."""
    clean_code = """
import hashlib
from sqlalchemy import text

def fetch_patient_summary(session, patient_id: str):
    # Parameterized query with bound parameters
    stmt = text("SELECT id, name FROM patients WHERE id = :patient_id")
    result = session.execute(stmt, {"patient_id": patient_id})
    return result.fetchall()

def compute_record_digest(payload: bytes) -> str:
    # Modern secure SHA-256 hash
    return hashlib.sha256(payload).hexdigest()
"""
    report = security_scanner_service.scan_snippet(clean_code)
    assert report.status == "PASSED"
    assert report.total_findings == 0
    assert report.critical_count == 0
    assert report.high_count == 0
    assert len(report.findings) == 0


def test_sast_detects_insecure_md5_sha1_hashes():
    """Verify that weak cryptographic algorithms MD5 and SHA-1 are flagged as HIGH severity."""
    insecure_code = """
import hashlib

def weak_hash(data: bytes):
    md5_hash = hashlib.md5(data).hexdigest()
    sha1_hash = hashlib.sha1(data).hexdigest()
    return md5_hash, sha1_hash
"""
    report = security_scanner_service.scan_snippet(insecure_code)
    assert report.status == "FAILED"
    assert report.total_findings == 2

    findings_rules = [f.rule_id for f in report.findings]
    assert findings_rules == ["NIRMAYA-SEC-001", "NIRMAYA-SEC-001"]
    for f in report.findings:
        assert f.category == SecurityCategoryEnum.INSECURE_CRYPTO
        assert f.severity == SecuritySeverityEnum.HIGH
        assert "MD5" in f.remediation or "SHA-256" in f.remediation


def test_sast_detects_sql_injection_fstrings():
    """Verify that unparameterized f-strings inside database execute calls are flagged as CRITICAL SQL injection."""
    sqli_code = """
def search_records(conn, user_input: str):
    # Direct f-string interpolation into execute call
    conn.execute(f"SELECT * FROM clinical_notes WHERE content LIKE '%{user_input}%'")
"""
    report = security_scanner_service.scan_snippet(sqli_code)
    assert report.status == "FAILED"
    assert report.critical_count == 1
    finding = report.findings[0]
    assert finding.rule_id == "NIRMAYA-SEC-002"
    assert finding.category == SecurityCategoryEnum.SQL_INJECTION
    assert finding.severity == SecuritySeverityEnum.CRITICAL
    assert "f-string" in finding.message


def test_sast_detects_sql_injection_modulo_and_format():
    """Verify that string modulo and str.format() calls in execute are flagged as CRITICAL SQL injection."""
    modulo_code = """
def query_facility(cursor, facility_id: str, dept: str):
    cursor.execute("SELECT * FROM facilities WHERE id = '%s'" % facility_id)
    cursor.execute("SELECT * FROM departments WHERE name = '{}'".format(dept))
"""
    report = security_scanner_service.scan_snippet(modulo_code)
    assert report.status == "FAILED"
    assert report.critical_count == 2
    for f in report.findings:
        assert f.rule_id == "NIRMAYA-SEC-002"
        assert f.category == SecurityCategoryEnum.SQL_INJECTION
        assert f.severity == SecuritySeverityEnum.CRITICAL


def test_sast_detects_dangerous_dynamic_execution():
    """Verify that eval and exec invocations are flagged as CRITICAL code execution risks."""
    eval_code = """
def evaluate_expression(user_formula: str):
    result = eval(user_formula)
    exec("admin_override = True")
    return result
"""
    report = security_scanner_service.scan_snippet(eval_code)
    assert report.status == "FAILED"
    assert report.critical_count == 2
    for f in report.findings:
        assert f.rule_id == "NIRMAYA-SEC-004"
        assert f.category == SecurityCategoryEnum.DANGEROUS_CALL
        assert f.severity == SecuritySeverityEnum.CRITICAL


def test_sast_detects_dangerous_subprocess_shell_true():
    """Verify that subprocess calls with shell=True and os.system are flagged as CRITICAL command injection risks."""
    cmd_code = """
import os
import subprocess

def run_backup(target_path: str):
    os.system(f"tar -czf backup.tar.gz {target_path}")
    subprocess.Popen(f"scp backup.tar.gz remote:{target_path}", shell=True)
"""
    report = security_scanner_service.scan_snippet(cmd_code)
    assert report.status == "FAILED"
    assert report.critical_count == 2
    for f in report.findings:
        assert f.rule_id == "NIRMAYA-SEC-004"
        assert f.category == SecurityCategoryEnum.DANGEROUS_CALL
        assert f.severity == SecuritySeverityEnum.CRITICAL


def test_sast_detects_insecure_deserialization_pickle():
    """Verify that pickle.loads is flagged as CRITICAL insecure deserialization."""
    pickle_code = """
import pickle

def load_session(raw_token: bytes):
    return pickle.loads(raw_token)
"""
    report = security_scanner_service.scan_snippet(pickle_code)
    assert report.status == "FAILED"
    assert report.critical_count == 1
    finding = report.findings[0]
    assert finding.rule_id == "NIRMAYA-SEC-005"
    assert finding.category == SecurityCategoryEnum.INSECURE_DESERIALIZATION
    assert finding.severity == SecuritySeverityEnum.CRITICAL


def test_sast_detects_hardcoded_secrets():
    """Verify that hardcoded credentials and private keys are flagged while benign placeholders are ignored."""
    secret_code = """
# Real credential leak
JWT_SECRET = "sk_live_94819481948194819481"
API_KEY = "live_cloud_api_key_production_vault_992"

# Safe placeholder patterns that must NOT trigger false positives
DEFAULT_PASSWORD = "change-in-production"
MOCK_API_KEY = "test-placeholder-key"
"""
    report = security_scanner_service.scan_snippet(secret_code)
    assert report.total_findings == 2
    for f in report.findings:
        assert f.rule_id == "NIRMAYA-SEC-003"
        assert f.category == SecurityCategoryEnum.HARDCODED_SECRET
        assert f.severity == SecuritySeverityEnum.HIGH


def test_dependency_scanner_parses_requirements_and_flags_cve():
    """Verify that dependency scanner parses requirements text and identifies known CVE advisories."""
    reqs_text = """
# Pinned dependencies with legacy vulnerabilities
cryptography==40.0.1
pydantic==2.6.0
rsa==4.5
fastapi==0.110.0
"""
    report = dependency_scanner_service.generate_dependency_report(requirements_content=reqs_text)
    assert report.status == "FAILED"
    assert report.total_findings >= 3

    cve_ids = [v.cve_id for v in report.dependency_findings]
    assert "CVE-2023-49083" in cve_ids  # cryptography
    assert "CVE-2024-37890" in cve_ids  # pydantic
    assert "CVE-2020-25658" in cve_ids  # rsa

    rsa_vuln = next(v for v in report.dependency_findings if v.package_name == "rsa")
    assert rsa_vuln.severity == SecuritySeverityEnum.CRITICAL
    assert rsa_vuln.cvss_score == 9.8


def test_dependency_scanner_clean_environment_passes():
    """Verify that up-to-date dependency specifications pass with zero critical or high vulnerabilities."""
    clean_reqs = """
cryptography==42.0.8
pydantic==2.8.2
fastapi==0.111.0
jinja2==3.1.4
"""
    report = dependency_scanner_service.generate_dependency_report(requirements_content=clean_reqs)
    assert report.critical_count == 0
    assert report.high_count == 0


def test_tenant_context_manager_and_db_pool_metrics():
    """Verify that database pool telemetry gathers accurate metrics and tenant context functions properly."""
    metrics = get_pool_metrics()
    assert metrics.pool_size >= 1
    assert metrics.status in ("HEALTHY", "WARNING", "SATURATED")
    assert metrics.utilization_rate_percent >= 0.0
    assert metrics.pre_ping_enabled is True

    # Test Tenant Context storage
    params = TenantContextParams(
        tenant_id="facility-apollo-492",
        user_id="doc-sharma-123",
        jurisdiction_path="india.27.492",
        role="SURGEON",
    )
    set_current_tenant_context(params)
    retrieved = get_current_tenant_context()
    assert retrieved is not None
    assert retrieved.tenant_id == "facility-apollo-492"
    assert retrieved.jurisdiction_path == "india.27.492"
    assert retrieved.role == "SURGEON"

    # Reset context
    set_current_tenant_context(None)
    assert get_current_tenant_context() is None


def test_security_rest_api_endpoints(test_client: TestClient):
    """Verify that security REST API routes expose valid responses for SAST, dependencies, and pool status."""
    # 1. Pool status
    res_pool = test_client.get("/api/v1/security/pool/status")
    assert res_pool.status_code == 200
    pool_data = res_pool.json()
    assert "pool_size" in pool_data
    assert "utilization_rate_percent" in pool_data
    assert pool_data["status"] in ("HEALTHY", "WARNING", "SATURATED")

    # 2. SAST snippet scan
    res_sast = test_client.post(
        "/api/v1/security/scan/sast",
        json={"code_snippet": "import hashlib\ndef bad(): return hashlib.md5(b'x').hexdigest()"},
    )
    assert res_sast.status_code == 200
    sast_data = res_sast.json()
    assert sast_data["status"] == "FAILED"
    assert sast_data["high_count"] >= 1
    assert len(sast_data["findings"]) >= 1
    assert sast_data["findings"][0]["rule_id"] == "NIRMAYA-SEC-001"

    # 3. Dependency scan
    res_dep = test_client.post(
        "/api/v1/security/scan/dependencies",
        json={"requirements_text": "rsa==4.5"},
    )
    assert res_dep.status_code == 200
    dep_data = res_dep.json()
    assert dep_data["status"] == "FAILED"
    assert dep_data["critical_count"] >= 1
    assert dep_data["dependency_findings"][0]["cve_id"] == "CVE-2020-25658"

