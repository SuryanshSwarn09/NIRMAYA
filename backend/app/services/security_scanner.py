"""AST-based Static Application Security Testing (SAST) Scanner for NIRMAYA.

Inspects Python Abstract Syntax Trees (AST) for insecure cryptographic algorithms,
SQL injection vulnerabilities, hardcoded credentials, dangerous system calls,
and unsafe deserialization routines.
"""

import ast
import os
import re
import time
import uuid
from typing import List, Optional, Tuple, Set
from datetime import datetime, timezone

from app.schemas.security_scanner import (
    SASTFinding,
    SecurityCategoryEnum,
    SecurityScanReport,
    SecuritySeverityEnum,
)


class SASTASTVisitor(ast.NodeVisitor):
    """AST NodeVisitor that inspects syntax tree nodes for security anti-patterns."""

    # Patterns for potential hardcoded secret variable names
    SECRET_VAR_PATTERN = re.compile(
        r"(SECRET|PASSWORD|PASSWD|API_KEY|APIKEY|PRIVATE_KEY|AUTH_TOKEN|JWT_SECRET)",
        re.IGNORECASE,
    )

    # Values that are harmless or conventional placeholders
    PLACEHOLDER_PATTERN = re.compile(
        r"(placeholder|change-in-production|default|example|test|dummy|none|null|sample)",
        re.IGNORECASE,
    )

    def __init__(self, source_code: str, file_path: Optional[str] = None):
        self.source_code = source_code
        self.lines = source_code.splitlines()
        self.file_path = file_path
        self.findings: List[SASTFinding] = []

    def _get_snippet(self, line_no: int) -> Optional[str]:
        """Safely extract line text for context snippet."""
        if 1 <= line_no <= len(self.lines):
            return self.lines[line_no - 1].strip()
        return None

    def visit_Call(self, node: ast.Call) -> None:
        """Inspect function calls for insecure cryptographic algorithms, SQLi, and dangerous built-ins."""
        func_name = ""

        # Extract function call identifier
        if isinstance(node.func, ast.Name):
            func_name = node.func.id
        elif isinstance(node.func, ast.Attribute):
            func_name = node.func.attr
            # Check module.function form (e.g. hashlib.md5, os.system)
            if isinstance(node.func.value, ast.Name):
                full_func = f"{node.func.value.id}.{node.func.attr}"
                self._check_module_call(node, node.func.value.id, node.func.attr, full_func)
            elif isinstance(node.func.value, ast.Attribute):
                # e.g., subprocess.Popen
                val_attr = node.func.value.attr
                self._check_module_call(node, val_attr, node.func.attr, f"{val_attr}.{node.func.attr}")

        # Rule NIRMAYA-SEC-004: Dangerous built-in execution calls (eval, exec)
        if func_name in ("eval", "exec", "__import__"):
            self.findings.append(
                SASTFinding(
                    rule_id="NIRMAYA-SEC-004",
                    category=SecurityCategoryEnum.DANGEROUS_CALL,
                    severity=SecuritySeverityEnum.CRITICAL,
                    file_path=self.file_path,
                    line_number=node.lineno,
                    col_offset=node.col_offset,
                    code_snippet=self._get_snippet(node.lineno),
                    message=f"Use of dangerous dynamic execution primitive '{func_name}' permits arbitrary code execution.",
                    remediation="Eliminate dynamic execution. Replace with typed parsers, dispatch maps, or literal_eval where strictly necessary.",
                )
            )

        # Rule NIRMAYA-SEC-002: SQL Injection checks on database execute calls
        if func_name in ("execute", "executemany"):
            self._check_sql_injection(node)

        # Continue traversing child AST nodes
        self.generic_visit(node)

    def _check_module_call(self, node: ast.Call, module: str, func: str, full_name: str) -> None:
        """Evaluate calls on imported modules like hashlib, subprocess, pickle, os."""
        # Rule NIRMAYA-SEC-001: Insecure Cryptography
        if module == "hashlib" and func.lower() in ("md5", "sha1"):
            # Check if used for non-security checksum by checking keyword args (usedforsecurity=False in py3.9+)
            is_non_sec = any(
                kw.arg == "usedforsecurity"
                and isinstance(kw.value, ast.Constant)
                and kw.value.value is False
                for kw in node.keywords
            )
            if not is_non_sec:
                self.findings.append(
                    SASTFinding(
                        rule_id="NIRMAYA-SEC-001",
                        category=SecurityCategoryEnum.INSECURE_CRYPTO,
                        severity=SecuritySeverityEnum.HIGH,
                        file_path=self.file_path,
                        line_number=node.lineno,
                        col_offset=node.col_offset,
                        code_snippet=self._get_snippet(node.lineno),
                        message=f"Cryptographically weak hash algorithm '{full_name}' detected. MD5 and SHA-1 are vulnerable to collision attacks.",
                        remediation="Migrate to SHA-256 (hashlib.sha256), SHA-384, or SHA-512. For password hashing or key derivation, utilize Argon2id.",
                    )
                )

        # Rule NIRMAYA-SEC-004: Subprocess with shell=True or os.system
        if module == "subprocess" and func in ("Popen", "run", "call", "check_call", "check_output"):
            has_shell_true = any(
                kw.arg == "shell"
                and isinstance(kw.value, ast.Constant)
                and kw.value.value is True
                for kw in node.keywords
            )
            if has_shell_true:
                self.findings.append(
                    SASTFinding(
                        rule_id="NIRMAYA-SEC-004",
                        category=SecurityCategoryEnum.DANGEROUS_CALL,
                        severity=SecuritySeverityEnum.CRITICAL,
                        file_path=self.file_path,
                        line_number=node.lineno,
                        col_offset=node.col_offset,
                        code_snippet=self._get_snippet(node.lineno),
                        message=f"Subprocess call '{full_name}' invoked with shell=True opens command injection vulnerabilities.",
                        remediation="Set shell=False and pass arguments as a structured list of strings without invoking the shell interpreter.",
                    )
                )

        if module == "os" and func in ("system", "popen"):
            self.findings.append(
                SASTFinding(
                    rule_id="NIRMAYA-SEC-004",
                    category=SecurityCategoryEnum.DANGEROUS_CALL,
                    severity=SecuritySeverityEnum.CRITICAL,
                    file_path=self.file_path,
                    line_number=node.lineno,
                    col_offset=node.col_offset,
                    code_snippet=self._get_snippet(node.lineno),
                    message=f"Use of '{full_name}' exposes the application to command injection vulnerabilities.",
                    remediation="Replace os.system with subprocess.run(..., shell=False) passing discrete, sanitized arguments.",
                )
            )

        # Rule NIRMAYA-SEC-005: Insecure Deserialization (pickle, yaml.load)
        if (module in ("pickle", "_pickle") and func in ("load", "loads")) or (
            module == "yaml" and func == "load"
        ):
            # If yaml.load without SafeLoader
            is_unsafe_yaml = False
            if module == "yaml" and func == "load":
                has_safe_loader = any(
                    kw.arg == "Loader"
                    and (
                        (isinstance(kw.value, ast.Attribute) and "SafeLoader" in kw.value.attr)
                        or (isinstance(kw.value, ast.Name) and "SafeLoader" in kw.value.id)
                    )
                    for kw in node.keywords
                )
                if not has_safe_loader:
                    is_unsafe_yaml = True

            if module in ("pickle", "_pickle") or is_unsafe_yaml:
                self.findings.append(
                    SASTFinding(
                        rule_id="NIRMAYA-SEC-005",
                        category=SecurityCategoryEnum.INSECURE_DESERIALIZATION,
                        severity=SecuritySeverityEnum.CRITICAL,
                        file_path=self.file_path,
                        line_number=node.lineno,
                        col_offset=node.col_offset,
                        code_snippet=self._get_snippet(node.lineno),
                        message=f"Insecure deserialization via '{full_name}' allows remote code execution through manipulated object payloads.",
                        remediation="Utilize safe serializers such as JSON (json.loads) or yaml.safe_load. Do not deserialize untrusted binary streams.",
                    )
                )

    def _check_sql_injection(self, node: ast.Call) -> None:
        """Detect formatted strings or string concatenation passed to database execution routines."""
        if not node.args:
            return

        first_arg = node.args[0]

        # Case 1: f-string passed directly: conn.execute(f"SELECT ... WHERE id = {user_id}")
        if isinstance(first_arg, ast.JoinedStr):
            self.findings.append(
                SASTFinding(
                    rule_id="NIRMAYA-SEC-002",
                    category=SecurityCategoryEnum.SQL_INJECTION,
                    severity=SecuritySeverityEnum.CRITICAL,
                    file_path=self.file_path,
                    line_number=node.lineno,
                    col_offset=node.col_offset,
                    code_snippet=self._get_snippet(node.lineno),
                    message="Dynamic SQL query built via f-string interpolation detected in execute call. High SQL injection risk.",
                    remediation="Use parameterized queries with SQLAlchemy text(:param) or ORM models. Never interpolate variables into SQL strings.",
                )
            )

        # Case 2: String modulo formatting: conn.execute("SELECT ... %s" % user_id)
        elif isinstance(first_arg, ast.BinOp) and isinstance(first_arg.op, ast.Mod):
            self.findings.append(
                SASTFinding(
                    rule_id="NIRMAYA-SEC-002",
                    category=SecurityCategoryEnum.SQL_INJECTION,
                    severity=SecuritySeverityEnum.CRITICAL,
                    file_path=self.file_path,
                    line_number=node.lineno,
                    col_offset=node.col_offset,
                    code_snippet=self._get_snippet(node.lineno),
                    message="Dynamic SQL query built via string formatting '%' operator in execute call. High SQL injection risk.",
                    remediation="Use bound parameters with SQLAlchemy text(:param) or ORM filters instead of string modulo operations.",
                )
            )

        # Case 3: str.format() call: conn.execute("SELECT ... {}".format(user_id))
        elif isinstance(first_arg, ast.Call) and isinstance(first_arg.func, ast.Attribute) and first_arg.func.attr == "format":
            self.findings.append(
                SASTFinding(
                    rule_id="NIRMAYA-SEC-002",
                    category=SecurityCategoryEnum.SQL_INJECTION,
                    severity=SecuritySeverityEnum.CRITICAL,
                    file_path=self.file_path,
                    line_number=node.lineno,
                    col_offset=node.col_offset,
                    code_snippet=self._get_snippet(node.lineno),
                    message="Dynamic SQL query built via str.format() method in execute call. High SQL injection risk.",
                    remediation="Bind SQL parameters explicitly via bindparams dictionary. Avoid string format substitutions.",
                )
            )

    def visit_Assign(self, node: ast.Assign) -> None:
        """Detect hardcoded secrets or API tokens in variable assignments."""
        for target in node.targets:
            target_name = None
            if isinstance(target, ast.Name):
                target_name = target.id
            elif isinstance(target, ast.Attribute):
                target_name = target.attr

            if target_name and self.SECRET_VAR_PATTERN.search(target_name):
                # Verify if assigned value is a non-empty string literal
                if isinstance(node.value, ast.Constant) and isinstance(node.value.value, str):
                    val = node.value.value.strip()
                    # Exclude empty strings, short strings, placeholders, or known test patterns
                    if len(val) >= 12 and not self.PLACEHOLDER_PATTERN.search(val):
                        self.findings.append(
                            SASTFinding(
                                rule_id="NIRMAYA-SEC-003",
                                category=SecurityCategoryEnum.HARDCODED_SECRET,
                                severity=SecuritySeverityEnum.HIGH,
                                file_path=self.file_path,
                                line_number=node.lineno,
                                col_offset=node.col_offset,
                                code_snippet=self._get_snippet(node.lineno),
                                message=f"Potential hardcoded secret or token detected in variable assignment '{target_name}'.",
                                remediation="Retrieve credentials dynamically from environment variables (os.environ, pydantic-settings) or secret vault.",
                            )
                        )

        self.generic_visit(node)


class SecurityScannerService:
    """Service orchestrating AST security scanning across code snippets, files, and repositories."""

    # Default ignored directories for codebase scanning
    IGNORED_DIRS: Set[str] = {
        ".git",
        ".venv",
        "venv",
        "__pycache__",
        "node_modules",
        ".next",
        ".pytest_cache",
        ".idea",
        ".vscode",
    }

    def scan_snippet(
        self,
        code_snippet: str,
        file_path: Optional[str] = "snippet.py",
        include_severities: Optional[List[SecuritySeverityEnum]] = None,
    ) -> SecurityScanReport:
        """Scan raw Python source code snippet and return structured report."""
        start_time = time.perf_counter()
        findings: List[SASTFinding] = []

        try:
            tree = ast.parse(code_snippet, filename=file_path or "snippet.py")
            visitor = SASTASTVisitor(source_code=code_snippet, file_path=file_path)
            visitor.visit(tree)
            findings = visitor.findings
        except SyntaxError as exc:
            findings.append(
                SASTFinding(
                    rule_id="NIRMAYA-SEC-PARSE",
                    category=SecurityCategoryEnum.DANGEROUS_CALL,
                    severity=SecuritySeverityEnum.MEDIUM,
                    file_path=file_path,
                    line_number=exc.lineno,
                    col_offset=exc.offset,
                    code_snippet=exc.text.strip() if exc.text else None,
                    message=f"Syntax parsing failure: {str(exc)}",
                    remediation="Correct syntax error before performing static AST analysis.",
                )
            )

        duration_ms = round((time.perf_counter() - start_time) * 1000, 2)
        return self._build_report(
            target_type="snippet",
            files_scanned=1,
            findings=findings,
            duration_ms=duration_ms,
            include_severities=include_severities,
        )

    def scan_file(
        self,
        file_path: str,
        include_severities: Optional[List[SecuritySeverityEnum]] = None,
    ) -> SecurityScanReport:
        """Scan a single Python file on disk."""
        start_time = time.perf_counter()
        findings: List[SASTFinding] = []

        if not os.path.isfile(file_path):
            duration_ms = round((time.perf_counter() - start_time) * 1000, 2)
            return self._build_report(
                target_type="file",
                files_scanned=0,
                findings=[],
                duration_ms=duration_ms,
                status="FAILED",
            )

        try:
            with open(file_path, "r", encoding="utf-8", errors="replace") as f:
                code_content = f.read()
            tree = ast.parse(code_content, filename=file_path)
            visitor = SASTASTVisitor(source_code=code_content, file_path=file_path)
            visitor.visit(tree)
            findings = visitor.findings
        except Exception as exc:
            findings.append(
                SASTFinding(
                    rule_id="NIRMAYA-SEC-PARSE",
                    category=SecurityCategoryEnum.DANGEROUS_CALL,
                    severity=SecuritySeverityEnum.LOW,
                    file_path=file_path,
                    line_number=None,
                    col_offset=None,
                    code_snippet=None,
                    message=f"Failed to parse source file: {str(exc)}",
                    remediation="Verify file readability and UTF-8 encoding.",
                )
            )

        duration_ms = round((time.perf_counter() - start_time) * 1000, 2)
        return self._build_report(
            target_type="file",
            files_scanned=1,
            findings=findings,
            duration_ms=duration_ms,
            include_severities=include_severities,
        )

    def scan_directory(
        self,
        directory_path: str,
        include_severities: Optional[List[SecuritySeverityEnum]] = None,
        max_files: int = 250,
    ) -> SecurityScanReport:
        """Traverse a directory scanning all Python source files."""
        start_time = time.perf_counter()
        all_findings: List[SASTFinding] = []
        files_scanned = 0

        for root, dirs, files in os.walk(directory_path):
            # Prune ignored directories in-place
            dirs[:] = [d for d in dirs if d not in self.IGNORED_DIRS and not d.startswith(".")]

            for file in files:
                if file.endswith(".py"):
                    if files_scanned >= max_files:
                        break
                    full_path = os.path.join(root, file)
                    rel_path = os.path.relpath(full_path, directory_path)
                    try:
                        with open(full_path, "r", encoding="utf-8", errors="replace") as f:
                            content = f.read()
                        tree = ast.parse(content, filename=rel_path)
                        visitor = SASTASTVisitor(source_code=content, file_path=rel_path)
                        visitor.visit(tree)
                        all_findings.extend(visitor.findings)
                        files_scanned += 1
                    except Exception:
                        continue

        duration_ms = round((time.perf_counter() - start_time) * 1000, 2)
        return self._build_report(
            target_type="directory",
            files_scanned=files_scanned,
            findings=all_findings,
            duration_ms=duration_ms,
            include_severities=include_severities,
        )

    def _build_report(
        self,
        target_type: str,
        files_scanned: int,
        findings: List[SASTFinding],
        duration_ms: float,
        include_severities: Optional[List[SecuritySeverityEnum]] = None,
        status: Optional[str] = None,
    ) -> SecurityScanReport:
        """Aggregate findings into a structured SecurityScanReport."""
        filtered_findings = findings
        if include_severities:
            allowed = set(include_severities)
            filtered_findings = [f for f in findings if f.severity in allowed]

        critical_count = sum(1 for f in filtered_findings if f.severity == SecuritySeverityEnum.CRITICAL)
        high_count = sum(1 for f in filtered_findings if f.severity == SecuritySeverityEnum.HIGH)
        medium_count = sum(1 for f in filtered_findings if f.severity == SecuritySeverityEnum.MEDIUM)
        low_count = sum(1 for f in filtered_findings if f.severity == SecuritySeverityEnum.LOW)

        if status is None:
            if critical_count > 0 or high_count > 0:
                calc_status = "FAILED"
            elif medium_count > 0:
                calc_status = "WARNING"
            else:
                calc_status = "PASSED"
        else:
            calc_status = status

        return SecurityScanReport(
            scan_id=f"scan_{uuid.uuid4().hex[:12]}",
            scanned_at=datetime.now(timezone.utc),
            target_type=target_type,
            files_scanned=files_scanned,
            total_findings=len(filtered_findings),
            critical_count=critical_count,
            high_count=high_count,
            medium_count=medium_count,
            low_count=low_count,
            findings=filtered_findings,
            dependency_findings=[],
            scan_duration_ms=duration_ms,
            status=calc_status,
        )


# Global singleton instance of SAST scanner service
security_scanner_service = SecurityScannerService()
