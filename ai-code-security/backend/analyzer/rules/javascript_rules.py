"""Security rules for JavaScript and TypeScript source files."""

from __future__ import annotations

import re

from ..engine import RuleMatch, SecurityRule


def _lines(code: str) -> list[str]:
    return code.splitlines()


def _is_plain_literal(argument: str) -> bool:
    return bool(re.fullmatch(r"""["'`][^"'`]*["'`]""", argument.strip()))


class XssRule(SecurityRule):
    id = "JS-XSS"
    name = "Cross-Site Scripting Rule"
    description = "Untrusted data is inserted into the DOM as executable HTML."
    cwe = "CWE-79"
    severity = "HIGH"
    confidence = 92
    language = "javascript"
    recommendation = "Use textContent or framework auto-escaping instead of raw HTML sinks."
    fix_vulnerable = "element.innerHTML = userInput;"
    fix_secure = "element.textContent = userInput;"
    fix_explanation = (
        "Assigning untrusted data to innerHTML lets an attacker inject markup and "
        "scripts that run in the victim's session."
    )
    flow = ["User Input", "HTML Sink", "DOM Injection", "Script Execution"]

    _SINK = re.compile(
        r"\.\s*(inner|outer)HTML\s*="
        r"|document\.write\s*\("
        r"|dangerouslySetInnerHTML"
        r"|insertAdjacentHTML\s*\("
        r"|\.html\s*\("
    )

    def detect(self, code: str, file_path: str) -> list[RuleMatch]:
        matches = []
        for index, line in enumerate(_lines(code), start=1):
            found = self._SINK.search(line)
            if not found:
                continue
            # Ignore sinks assigned a pure string literal (static markup only).
            after = line[found.end() :].strip()
            if after and _is_plain_literal(after.split(",")[0].rstrip(";")):
                continue
            if "dangerouslySetInnerHTML" in line and "__html" in line:
                value = line.split("__html", 1)[1]
                if _is_plain_literal(value.lstrip(" :=,{}").split("}")[0]):
                    continue
            matches.append(
                RuleMatch(
                    line=index,
                    code=line.strip(),
                    description="Dynamic data reaches an HTML sink without encoding.",
                    evidence="HTML sinks interpret markup, so injected scripts execute in the page.",
                )
            )
        return matches


class CommandInjectionRule(SecurityRule):
    id = "JS-CMDI"
    name = "Command Injection Rule"
    description = "A shell command is executed with dynamically built input."
    cwe = "CWE-78"
    severity = "CRITICAL"
    confidence = 94
    language = "javascript"
    recommendation = "Avoid child_process shell calls; validate input or use execFile with an argument array."
    fix_vulnerable = "exec(`ping -c 1 ${host}`);"
    fix_secure = 'execFile("ping", ["-c", "1", host]);'
    fix_explanation = (
        "Shell interpretation of concatenated input lets an attacker append "
        "arbitrary commands."
    )
    flow = ["User Input", "Command String", "Shell", "Command Execution"]

    _BARE_EXEC = re.compile(r"(?<![\w.$])exec(Sync)?\s*\(")
    _CHILD_PROCESS = re.compile(r"child_process")
    _SPAWN_SHELL = re.compile(r"\.spawn\s*\([^)]*shell\s*:\s*true", re.IGNORECASE)

    def detect(self, code: str, file_path: str) -> list[RuleMatch]:
        matches = []
        for index, line in enumerate(_lines(code), start=1):
            flagged = bool(self._BARE_EXEC.search(line) or self._SPAWN_SHELL.search(line))
            if not flagged and self._CHILD_PROCESS.search(line) and re.search(
                r"\bexec(Sync)?\s*\(", line
            ):
                flagged = True
            if not flagged:
                continue
            matches.append(
                RuleMatch(
                    line=index,
                    code=line.strip(),
                    description="A shell command is executed using dynamically built input.",
                    evidence="child_process exec runs the string through /bin/sh, enabling command injection.",
                )
            )
        return matches


class HardcodedCredentialsRule(SecurityRule):
    id = "JS-SECRETS"
    name = "Hardcoded Secrets Rule"
    description = "API keys, passwords or tokens are embedded in the client source."
    cwe = "CWE-798"
    severity = "HIGH"
    confidence = 97
    language = "javascript"
    recommendation = "Load secrets from environment variables or a server-side secret store."
    fix_vulnerable = 'const apiKey = "sk_live_51H8xY...";'
    fix_secure = 'const apiKey = process.env.API_KEY;'
    fix_explanation = (
        "Anything shipped in client code is public; hardcoded secrets must be "
        "revoked and moved server-side."
    )
    flow = ["Source Code", "Literal Assignment", "Secret Value", "Repository Leak"]

    _PATTERN = re.compile(
        r"""(?i)\b(?P<name>apiKey|api_key|password|passwd|secret|token|authToken|"""
        r"""accessToken|clientSecret|accessKey)\b\s*[:=]\s*(?P<q>["'`])"""
        r"""(?P<value>[^"'`]{4,})(?P=q)"""
    )
    _IGNORE_VALUES = {"none", "null", "undefined", "true", "false", "changeme"}

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
            if value.startswith(("<", "{{", "$", "%", "your-", "YOUR_")):
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


class EvalRule(SecurityRule):
    id = "JS-EVAL"
    name = "Dangerous eval Rule"
    description = "eval() or Function() executes dynamically constructed code."
    cwe = "CWE-95"
    severity = "CRITICAL"
    confidence = 96
    language = "javascript"
    recommendation = "Never eval untrusted strings; use JSON.parse or explicit logic instead."
    fix_vulnerable = "const result = eval(userInput);"
    fix_secure = "const result = JSON.parse(userInput);"
    fix_explanation = (
        "eval runs arbitrary JavaScript with the page's privileges, giving an "
        "attacker full control of the session."
    )
    flow = ["User Input", "Code String", "eval()", "Code Execution"]

    _PATTERN = re.compile(r"(?<![\w.$])eval\s*\(|new\s+Function\s*\(")

    def detect(self, code: str, file_path: str) -> list[RuleMatch]:
        matches = []
        for index, line in enumerate(_lines(code), start=1):
            found = self._PATTERN.search(line)
            if not found:
                continue
            argument = line[found.end() :]
            if _is_plain_literal(argument.split(")")[0]):
                continue
            matches.append(
                RuleMatch(
                    line=index,
                    code=line.strip(),
                    description="Dynamic input is executed as JavaScript.",
                    evidence="eval/Function compile a string as code at runtime.",
                )
            )
        return matches


class InsecureTransportRule(SecurityRule):
    id = "JS-HTTP"
    name = "Cleartext HTTP Rule"
    description = "Data is transmitted over unencrypted HTTP."
    cwe = "CWE-319"
    severity = "LOW"
    confidence = 80
    language = "javascript"
    recommendation = "Use HTTPS for all network communication."
    fix_vulnerable = 'fetch("http://api.example.com/users")'
    fix_secure = 'fetch("https://api.example.com/users")'
    fix_explanation = "Cleartext traffic can be read and modified by anyone on the path."
    flow = ["Outbound Request", "http://", "Cleartext Channel", "Eavesdropping"]

    _PATTERN = re.compile(
        r"""["']http://(?!localhost|127\.0\.0\.1|0\.0\.0\.0|www\.w3\.org|schemas\.)"""
    )

    def detect(self, code: str, file_path: str) -> list[RuleMatch]:
        matches = []
        for index, line in enumerate(_lines(code), start=1):
            if self._PATTERN.search(line):
                matches.append(
                    RuleMatch(
                        line=index,
                        code=line.strip(),
                        description="A cleartext HTTP endpoint is used.",
                        evidence="Plain http:// URLs expose data to interception.",
                    )
                )
        return matches


JAVASCRIPT_RULES = [
    XssRule,
    CommandInjectionRule,
    HardcodedCredentialsRule,
    EvalRule,
    InsecureTransportRule,
]

