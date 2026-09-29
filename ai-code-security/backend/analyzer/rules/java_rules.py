"""Security rules for Java source files."""

from __future__ import annotations

import re

from ..engine import RuleMatch, SecurityRule

SQL_KEYWORD = re.compile(
    r"\b(SELECT\s|INSERT\s+INTO|UPDATE\s+\w|DELETE\s+FROM|DROP\s+TABLE|WHERE\s+\w)",
    re.IGNORECASE,
)


def _lines(code: str) -> list[str]:
    return code.splitlines()


class SqlInjectionRule(SecurityRule):
    id = "JAVA-SQLI"
    name = "SQL Injection Rule"
    description = "A SQL query is built by concatenating dynamic values."
    cwe = "CWE-89"
    severity = "HIGH"
    confidence = 90
    language = "java"
    recommendation = "Use PreparedStatement with bound parameters (? placeholders)."
    fix_vulnerable = 'stmt.executeQuery("SELECT * FROM users WHERE id=" + userId);'
    fix_secure = (
        'PreparedStatement ps = conn.prepareStatement(\n'
        '    "SELECT * FROM users WHERE id = ?");\n'
        "ps.setString(1, userId);"
    )
    fix_explanation = (
        "Bound parameters are sent to the database separately from the query "
        "structure, so input can never alter the statement."
    )
    flow = ["User Input", "String Concatenation", "SQL Query", "Statement.execute"]

    def detect(self, code: str, file_path: str) -> list[RuleMatch]:
        matches = []
        for index, line in enumerate(_lines(code), start=1):
            sql_and_concat = (
                SQL_KEYWORD.search(line)
                and "+" in line
                and re.search(r"""["'].*["']\s*\+|\+\s*["']""", line)
            )
            sink_concat = re.search(
                r"\.execute(Query|Update|LargeUpdate)?\s*\([^)]*\+", line
            )
            if sql_and_concat or sink_concat:
                matches.append(
                    RuleMatch(
                        line=index,
                        code=line.strip(),
                        description="A SQL query is built by concatenating dynamic input.",
                        evidence="Concatenated SQL lets input change the statement structure.",
                    )
                )
        return matches


class CommandInjectionRule(SecurityRule):
    id = "JAVA-CMDI"
    name = "Command Injection Rule"
    description = "An OS command is executed through Runtime.exec or ProcessBuilder."
    cwe = "CWE-78"
    severity = "CRITICAL"
    confidence = 93
    language = "java"
    recommendation = "Avoid shell execution; validate input against a strict allow-list."
    fix_vulnerable = 'Runtime.getRuntime().exec("ls " + dir);'
    fix_secure = 'new ProcessBuilder("ls", dir).start();'
    fix_explanation = (
        "Concatenated commands let an attacker append arbitrary OS commands."
    )
    flow = ["User Input", "Command String", "Runtime.exec", "Command Execution"]

    _PATTERN = re.compile(r"Runtime\.getRuntime\(\)\.exec\s*\(|new\s+ProcessBuilder\s*\(")

    def detect(self, code: str, file_path: str) -> list[RuleMatch]:
        matches = []
        for index, line in enumerate(_lines(code), start=1):
            if self._PATTERN.search(line):
                matches.append(
                    RuleMatch(
                        line=index,
                        code=line.strip(),
                        description="An operating-system command is executed from data.",
                        evidence="Runtime.exec/ProcessBuilder interpret command strings at runtime.",
                    )
                )
        return matches


class HardcodedCredentialsRule(SecurityRule):
    id = "JAVA-SECRETS"
    name = "Hardcoded Credentials Rule"
    description = "Credentials or API secrets are embedded directly in the source."
    cwe = "CWE-798"
    severity = "HIGH"
    confidence = 97
    language = "java"
    recommendation = "Load secrets from environment variables or a secrets manager."
    fix_vulnerable = 'private static final String API_KEY = "abcd1234secret";'
    fix_secure = 'private static final String API_KEY = System.getenv("API_KEY");'
    fix_explanation = (
        "Hardcoded secrets leak through repositories, builds and logs and "
        "cannot be rotated safely."
    )
    flow = ["Source Code", "Literal Assignment", "Secret Value", "Repository Leak"]

    _PATTERN = re.compile(
        r"""(?i)\b(?P<name>password|passwd|api[_-]?key|secret[_-]?key|token|"""
        r"""access[_-]?token|auth[_-]?token|client[_-]?secret|private[_-]?key)"""
        r"""\b\s*=\s*(?P<q>["'])(?P<value>[^"']{4,})(?P=q)"""
    )
    _IGNORE_VALUES = {"none", "null", "true", "false", "changeme"}

    def detect(self, code: str, file_path: str) -> list[RuleMatch]:
        matches = []
        for index, line in enumerate(_lines(code), start=1):
            stripped = line.strip()
            if stripped.startswith("//") or stripped.startswith("*"):
                continue
            found = self._PATTERN.search(line)
            if not found:
                continue
            value = found.group("value")
            if value.lower() in self._IGNORE_VALUES:
                continue
            if value.startswith(("<", "${", "%", "your-", "YOUR_")):
                continue
            matches.append(
                RuleMatch(
                    line=index,
                    code=stripped,
                    description=f"Hardcoded credential detected for `{found.group('name')}`.",
                    evidence="A literal secret value is stored in the source code.",
                )
            )
        return matches


class UnsafeDeserializationRule(SecurityRule):
    id = "JAVA-DESER"
    name = "Unsafe Deserialization Rule"
    description = "Object streams or XML decoders deserialize untrusted data."
    cwe = "CWE-502"
    severity = "HIGH"
    confidence = 88
    language = "java"
    recommendation = "Avoid native serialization; validate schema-bound formats such as JSON."
    fix_vulnerable = "Object obj = ois.readObject();"
    fix_secure = 'User user = objectMapper.readValue(json, User.class);'
    fix_explanation = (
        "Java deserialization of untrusted data can instantiate gadget classes "
        "that execute code during loading."
    )
    flow = ["Untrusted Data", "ObjectInputStream", "readObject()", "Object Creation"]

    _PATTERN = re.compile(r"\.readObject\s*\(|new\s+ObjectInputStream\s*\(|new\s+XMLDecoder\s*\(")

    def detect(self, code: str, file_path: str) -> list[RuleMatch]:
        matches = []
        for index, line in enumerate(_lines(code), start=1):
            found = self._PATTERN.search(line)
            if not found:
                continue
            # One finding per deserialization site: prefer the readObject call.
            if "new ObjectInputStream" in line and ".readObject" not in line:
                continue
            matches.append(
                RuleMatch(
                    line=index,
                    code=line.strip(),
                    description="Untrusted bytes are deserialized into Java objects.",
                    evidence="ObjectInputStream/XMLDecoder can trigger gadget chains on hostile input.",
                )
            )
        return matches


JAVA_RULES = [
    SqlInjectionRule,
    CommandInjectionRule,
    HardcodedCredentialsRule,
    UnsafeDeserializationRule,
]

