"""Detection tests for Python security rules."""

from __future__ import annotations

from analyzer.scanner import scan_source

SQL_FSTRING = (
    'def get_user(user_id):\n'
    '    query = f"SELECT * FROM users WHERE id = {user_id}"\n'
    "    cursor.execute(query)\n"
)
SQL_CONCAT = (
    'query = "SELECT * FROM users WHERE id=" + user_id\n'
    "cursor.execute(query)\n"
)
SQL_SAFE = (
    'cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))\n'
)


def titles(code: str) -> list[str]:
    return [finding.title for finding in scan_source("app.py", code)]


def test_sql_injection_fstring() -> None:
    findings = scan_source("backend/users.py", SQL_FSTRING)
    assert len(findings) == 1
    finding = findings[0]
    assert finding.title == "SQL Injection"
    assert finding.cwe == "CWE-89"
    assert finding.severity == "HIGH"
    assert finding.line == 3  # reported at the execute sink
    assert finding.context, "context lines must be included"


def test_sql_injection_concat() -> None:
    findings = scan_source("app.py", SQL_CONCAT)
    assert len(findings) == 1
    assert findings[0].cwe == "CWE-89"


def test_parameterized_query_not_flagged() -> None:
    assert titles(SQL_SAFE) == []


def test_command_injection_variants() -> None:
    cases = [
        "os.system(user_input)\n",
        "os.popen(user_input)\n",
        "subprocess.run(user_input, shell=True)\n",
        "subprocess.call(cmd, shell=True)\n",
    ]
    for code in cases:
        findings = scan_source("job.py", code)
        assert len(findings) == 1, code
        assert findings[0].title == "Command Injection"
        assert findings[0].cwe == "CWE-78"
        assert findings[0].severity == "CRITICAL"


def test_literal_os_system_not_flagged() -> None:
    assert titles('os.system("ls -la")\n') == []


def test_eval_detected() -> None:
    findings = scan_source("calc.py", "result = eval(user_input)\n")
    assert len(findings) == 1
    assert findings[0].title == "Code Injection"
    assert findings[0].cwe == "CWE-95"
    assert findings[0].severity == "CRITICAL"


def test_pickle_loads_detected() -> None:
    findings = scan_source("cache.py", "data = pickle.loads(payload)\n")
    assert len(findings) == 1
    assert findings[0].cwe == "CWE-502"


def test_hardcoded_credential_detected() -> None:
    findings = scan_source(
        "settings.py", 'password = "admin123"\napi_key = "AKIA12345678"\n'
    )
    assert len(findings) == 2
    assert all(f.cwe == "CWE-798" for f in findings)
    assert all(f.severity == "HIGH" for f in findings)


def test_normal_string_not_flagged_as_secret() -> None:
    code = 'name = "FairShare"\nlabel = "choose a password hint"\n'
    assert titles(code) == []


def test_env_secret_not_flagged() -> None:
    code = 'password = os.environ["DB_PASSWORD"]\n'
    assert titles(code) == []


def test_path_traversal_detected() -> None:
    findings = scan_source("views.py", 'handle = open("/uploads/" + filename)\n')
    assert len(findings) == 1
    assert findings[0].title == "Path Traversal"
    assert findings[0].cwe == "CWE-22"


def test_path_traversal_via_variable() -> None:
    code = (
        'file_path = base_path + user_input\n'
        "open(file_path)\n"
    )
    findings = scan_source("views.py", code)
    assert len(findings) == 1
    assert findings[0].cwe == "CWE-22"


def test_safe_open_not_flagged() -> None:
    assert titles('with open("data.json", "r") as handle:\n    pass\n') == []
