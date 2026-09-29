"""Detection tests for JavaScript/TypeScript and Java rules."""

from __future__ import annotations

from analyzer.scanner import scan_source


def titles(code: str, path: str = "app.js") -> list[str]:
    return [finding.title for finding in scan_source(path, code)]


def test_xss_inner_html() -> None:
    findings = scan_source("app.js", "element.innerHTML = userInput;\n")
    assert len(findings) == 1
    assert findings[0].title == "Cross-Site Scripting"
    assert findings[0].cwe == "CWE-79"
    assert findings[0].severity == "HIGH"


def test_xss_static_markup_not_flagged() -> None:
    assert titles('element.innerHTML = "<b>hello</b>";\n') == []


def test_xss_react_dangerous_html() -> None:
    code = '<div dangerouslySetInnerHTML={{ __html: comment }} />\n'
    findings = scan_source("App.tsx", code)
    assert len(findings) == 1
    assert findings[0].cwe == "CWE-79"


def test_js_command_injection() -> None:
    findings = scan_source("job.js", "exec(userInput);\n")
    assert len(findings) == 1
    assert findings[0].title == "Command Injection"
    assert findings[0].severity == "CRITICAL"


def test_regexp_exec_not_flagged() -> None:
    assert titles("const match = pattern.exec(input);\n") == []


def test_js_hardcoded_secret() -> None:
    code = 'const apiKey = "sk_live_51H8xY";\n'
    findings = scan_source("config.js", code)
    assert len(findings) == 1
    assert findings[0].cwe == "CWE-798"


def test_js_secret_from_env_not_flagged() -> None:
    assert titles("const apiKey = process.env.API_KEY;\n") == []


def test_js_eval_detected() -> None:
    findings = scan_source("run.js", "eval(userInput);\n")
    assert len(findings) == 1
    assert findings[0].cwe == "CWE-95"


def test_cleartext_http_low() -> None:
    findings = scan_source("api.ts", 'fetch("http://example.com/data");\n')
    assert len(findings) == 1
    assert findings[0].severity == "LOW"
    assert findings[0].cwe == "CWE-319"


def test_localhost_http_not_flagged() -> None:
    assert titles('fetch("http://localhost:8000/api");\n') == []


def test_java_sql_injection() -> None:
    code = 'stmt.executeQuery("SELECT * FROM users WHERE id=" + id);\n'
    findings = scan_source("Query.java", code)
    assert len(findings) == 1
    assert findings[0].cwe == "CWE-89"
    assert findings[0].severity == "HIGH"


def test_java_command_injection() -> None:
    code = 'Runtime.getRuntime().exec("ls " + dir);\n'
    findings = scan_source("Shell.java", code)
    assert len(findings) == 1
    assert findings[0].severity == "CRITICAL"


def test_java_hardcoded_credentials() -> None:
    code = 'private static final String API_KEY = "abcd1234secret";\n'
    findings = scan_source("Config.java", code)
    assert len(findings) == 1
    assert findings[0].cwe == "CWE-798"


def test_java_unsafe_deserialization() -> None:
    code = "Object obj = ois.readObject();\n"
    findings = scan_source("Loader.java", code)
    assert len(findings) == 1
    assert findings[0].cwe == "CWE-502"


def test_unsupported_extension_ignored() -> None:
    assert titles("password = 'hunter2secret'", path="notes.txt") == []
