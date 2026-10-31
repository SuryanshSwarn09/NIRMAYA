"""Comprehensive test suite for OWASP ASVS v4.0.3 Level 2 compliance verification,
adversarial SQLi/XSS defensive fuzzing benchmarks, and distributed DoS shield with IP jail.
"""

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.schemas.asvs_fuzzer import (
    ASVSControlFamily,
    FuzzingAttackType,
    FuzzTestRequest,
)
from app.services.asvs_audit_service import asvs_audit_service
from app.services.asvs_fuzzer import asvs_fuzzer_service
from app.services.dos_shield import dos_shield_service

client = TestClient(app)


@pytest.fixture(autouse=True)
def reset_shield():
    """Reset DoS shield and IP jail state before and after each test."""
    dos_shield_service.clear()
    yield
    dos_shield_service.clear()


def test_asvs_compliance_report_certification():
    """Verify that ASVS audit service yields 100% compliance across all evaluated Level 2 controls."""
    report = asvs_audit_service.generate_compliance_report()
    assert report.status == "CERTIFIED"
    assert report.total_controls >= 18
    assert report.compliant_controls == report.total_controls
    assert report.compliance_percentage == 100.0
    assert report.asvs_version == "4.0.3"


def test_asvs_control_families_covered():
    """Verify that all major ASVS control families (V1 through V14) are evaluated in the audit."""
    report = asvs_audit_service.generate_compliance_report()
    families_present = {item.family for item in report.items}

    expected_families = {
        ASVSControlFamily.V1_ARCHITECTURE,
        ASVSControlFamily.V2_AUTHENTICATION,
        ASVSControlFamily.V3_SESSION_MANAGEMENT,
        ASVSControlFamily.V4_ACCESS_CONTROL,
        ASVSControlFamily.V5_MALICIOUS_INPUT,
        ASVSControlFamily.V6_CRYPTOGRAPHY,
        ASVSControlFamily.V7_ERROR_LOGGING,
        ASVSControlFamily.V8_DATA_PROTECTION,
        ASVSControlFamily.V9_COMMUNICATIONS,
        ASVSControlFamily.V10_MALICIOUS_CODE,
        ASVSControlFamily.V11_BUSINESS_LOGIC,
        ASVSControlFamily.V13_API_WEB_SERVICES,
        ASVSControlFamily.V14_CONFIGURATION,
    }
    for fam in expected_families:
        assert fam in families_present, f"Missing ASVS family {fam.value} in compliance audit"


def test_sqli_fuzzing_blocks_tautologies():
    """Verify that tautological boolean SQL injection attacks are recognized and blocked."""
    report = asvs_fuzzer_service.test_sqli_defenses(custom_input="' OR '1'='1")
    assert report.total_vectors_tested == 1
    assert report.blocked_count == 1
    assert report.bypass_count == 0
    assert report.results[0].defense_action == "BLOCKED"
    assert report.results[0].was_detected is True

    # Test double quote variant
    report2 = asvs_fuzzer_service.test_sqli_defenses(custom_input='" OR ""="')
    assert report2.blocked_count == 1
    assert report2.results[0].defense_action == "BLOCKED"


def test_sqli_fuzzing_blocks_stacked_and_union():
    """Verify that union-based information disclosure and stacked execution payloads are blocked."""
    union_payload = "' UNION SELECT null, null, username, password FROM users --"
    report_union = asvs_fuzzer_service.test_sqli_defenses(custom_input=union_payload)
    assert report_union.blocked_count == 1
    assert report_union.results[0].defense_action == "BLOCKED"

    stacked_payload = "'; DROP TABLE patients; --"
    report_stacked = asvs_fuzzer_service.test_sqli_defenses(custom_input=stacked_payload)
    assert report_stacked.blocked_count == 1
    assert report_stacked.results[0].defense_action == "BLOCKED"


def test_sqli_fuzzing_blocks_time_delays():
    """Verify that database sleep and timing delay injection attacks are blocked."""
    sleep_payload = "' OR pg_sleep(5) --"
    report_sleep = asvs_fuzzer_service.test_sqli_defenses(custom_input=sleep_payload)
    assert report_sleep.blocked_count == 1
    assert report_sleep.results[0].defense_action == "BLOCKED"


def test_xss_fuzzing_neutralizes_script_tags():
    """Verify that raw HTML script tags are neutralized to harmless HTML entities."""
    script_payload = "<script>alert('xss_test')</script>"
    report = asvs_fuzzer_service.test_xss_defenses(custom_input=script_payload)
    assert report.neutralized_count == 1
    assert report.bypass_count == 0
    res = report.results[0]
    assert res.defense_action == "NEUTRALIZED"
    assert "<script>" not in res.sanitized_output
    assert "&lt;script&gt;" in res.sanitized_output


def test_xss_fuzzing_neutralizes_event_handlers():
    """Verify that DOM inline event handlers (onerror, onload) are safely sanitized."""
    img_payload = "<img src=x onerror=alert(document.cookie)>"
    report_img = asvs_fuzzer_service.test_xss_defenses(custom_input=img_payload)
    assert report_img.neutralized_count == 1
    assert "<img" not in report_img.results[0].sanitized_output
    assert "&lt;img" in report_img.results[0].sanitized_output

    svg_payload = "<svg onload=alert(1)>"
    report_svg = asvs_fuzzer_service.test_xss_defenses(custom_input=svg_payload)
    assert report_svg.neutralized_count == 1


def test_xss_fuzzing_neutralizes_javascript_uri():
    """Verify that javascript: pseudo-protocols are stripped or rendered inert."""
    js_uri_payload = "javascript:alert('malicious')"
    sanitized, was_modified = asvs_fuzzer_service.sanitize_clinical_input(js_uri_payload)
    assert was_modified is True
    assert "javascript:" not in sanitized.lower()
    assert "blocked-scheme:" in sanitized


def test_sanitizer_preserves_legitimate_medical_text():
    """Verify that clinical SOAP notes containing valid comparison symbols (< and >) are safely escaped without losing medical semantics."""
    clinical_note = "Patient O2 sat > 95%, HbA1c < 6.5%, BP 120/80 mmHg, pain score 2/10."
    sanitized, was_modified = asvs_fuzzer_service.sanitize_clinical_input(clinical_note)
    assert was_modified is True
    assert "&gt; 95%" in sanitized
    assert "&lt; 6.5%" in sanitized
    assert "BP 120/80 mmHg" in sanitized


def test_dos_shield_normal_request_consumption():
    """Verify that legitimate inbound traffic consumes tokens correctly within configured capacity."""
    ip = "192.168.1.100"
    allowed, rem, retry, reason = dos_shield_service.check_request(ip, capacity=100)
    assert allowed is True
    assert rem == 99
    assert retry == 0
    assert reason is None


def test_dos_shield_trips_ip_jail_on_exploit_payload():
    """Verify that injecting an adversarial exploit payload immediately trips the IP Jail penalty box."""
    attacker_ip = "198.51.100.42"
    sqli_attack = "'; DROP TABLE facilities; --"

    # Inbound attack request
    allowed, rem, retry, reason = dos_shield_service.check_request(attacker_ip, payload_sample=sqli_attack)
    assert allowed is False
    assert retry == 300
    assert "IP_JAILED" in reason

    # Subsequent request from same host should immediately be rejected
    is_jailed, jail_rec = dos_shield_service.is_ip_jailed(attacker_ip)
    assert is_jailed is True
    assert jail_rec.ip_address == attacker_ip
    assert "SQL Injection" in jail_rec.reason or "DROP TABLE" in jail_rec.reason

    # Clean request from jailed host is still blocked
    allowed_next, _, retry_next, _ = dos_shield_service.check_request(attacker_ip)
    assert allowed_next is False
    assert retry_next > 0


def test_dos_shield_ip_jail_unban_and_clear():
    """Verify that administrative release and clear actions restore host access."""
    attacker_ip = "203.0.113.88"
    dos_shield_service.jail_ip(attacker_ip, reason="MANUAL_TEST_BAN", penalty_seconds=60)

    is_jailed, _ = dos_shield_service.is_ip_jailed(attacker_ip)
    assert is_jailed is True

    # Release single host
    released = dos_shield_service.release_ip(attacker_ip)
    assert released is True
    is_jailed_after, _ = dos_shield_service.is_ip_jailed(attacker_ip)
    assert is_jailed_after is False


def test_asvs_and_dos_shield_rest_api_endpoints():
    """Verify that all ASVS, fuzzing, and DoS shield REST endpoints return valid HTTP 200 responses."""
    # 1. ASVS Checklist
    res_asvs = client.get("/api/v1/security/asvs/checklist")
    assert res_asvs.status_code == 200
    asvs_data = res_asvs.json()
    assert asvs_data["status"] == "CERTIFIED"
    assert asvs_data["compliance_percentage"] == 100.0

    # 2. SQLi Fuzzing endpoint
    res_sqli = client.post(
        "/api/v1/security/fuzz/sqli",
        json={"input_text": "' OR '1'='1"},
    )
    assert res_sqli.status_code == 200
    sqli_data = res_sqli.json()
    assert sqli_data["blocked_count"] == 1

    # 3. XSS Fuzzing endpoint
    res_xss = client.post(
        "/api/v1/security/fuzz/xss",
        json={"input_text": "<script>alert(1)</script>"},
    )
    assert res_xss.status_code == 200
    xss_data = res_xss.json()
    assert xss_data["neutralized_count"] == 1

    # 4. Comprehensive Fuzz endpoint
    res_all = client.post("/api/v1/security/fuzz/all")
    assert res_all.status_code == 200
    all_data = res_all.json()
    assert all_data["status"] == "SECURE"
    assert all_data["effectiveness_rate_percent"] == 100.0

    # 5. DoS Shield status endpoint
    res_jail = client.get("/api/v1/security/shield/jail")
    assert res_jail.status_code == 200
    jail_data = res_jail.json()
    assert jail_data["status"] in ("PROTECTED", "UNDER_ATTACK")

    # 6. Clear Jails endpoint
    res_clear = client.post("/api/v1/security/shield/jail/clear")
    assert res_clear.status_code == 200
    assert res_clear.json()["success"] is True

