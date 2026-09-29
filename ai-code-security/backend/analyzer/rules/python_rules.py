"""Security rules for Python source files."""

from __future__ import annotations

import re

from ..engine import RuleMatch, SecurityRule
from ..utils import first_identifier

SQL_KEYWORD = re.compile(
    r"\b(SELECT\s|INSERT\s+INTO|UPDATE\s+\w|DELETE\s+FROM|DROP\s+TABLE|FROM\s+\w|WHERE\s+\w)",
    re.IGNORECASE,
)
FSTRING = re.compile(r"""\bf(["'])""")


def _lines(code: str) -> list[str]:
    return code.splitlines()


def _call_window(lines: list[str], start: int, max_lines: int = 6) -> str:
    """Join a few lines starting at ``start`` until parentheses balance."""
    buffer = []
    depth = 0
    opened = False
    for text in lines[start : start + max_lines]:
        buffer.append(text)
        depth += text.count("(") - text.count(")")
        if "(" in text:
            opened = True
        if opened and depth <= 0:
            break
    return "\n".join(buffer)


def _is_plain_literal(argument: str) -> bool:
    argument = argument.strip()
    return bool(re.fullmatch(r"""["'][^"']*["']""", argument))


class SqlInjectionRule(SecurityRule):
    id = "PY-SQLI"
    name = "SQL Injection Rule"
    description = (
        "A SQL query is built by interpolating dynamic values instead of using "
        "parameterized queries."
    )
    cwe = "CWE-89"
    severity = "HIGH"
    confidence = 91
    language = "python"
    recommendation = "Use parameterized SQL queries."
    fix_vulnerable = (
        'query = f"SELECT * FROM users WHERE id={user_id}"\n'
        "cursor.execute(query)"
    )
    fix_secure = (
        "cursor.execute(\n"
        '    "SELECT * FROM users WHERE id=%s",\n'
        "    (user_id,)\n"
        ")"
    )
    fix_explanation = (
        "Parameterized queries keep user input separate from SQL instructions, "
        "so the database never treats input as executable SQL."
    )
    flow = ["User Input", "String Formatting", "SQL Query", "cursor.execute()"]

    def detect(self, code: str, file_path: str) -> list[RuleMatch]:
        lines = _lines(code)
        matches: list[RuleMatch] = []
        unsafe_vars: dict[str, tuple[int, str]] = {}

        def capture_assignment(line: str, index: int) -> None:
            assigned = re.match(r"""\s*([A-Za-z_]\w*)\s*=\s*(.+)$""", line)
            if assigned:
                unsafe_vars.setdefault(assigned.group(1), (index, line))

        # Pass 1: locate unsafe query construction (f-strings / concatenation).
        for index, line in enumerate(lines, start=1):
            if not SQL_KEYWORD.search(line):
                continue
            variable = None
            if FSTRING.search(line) and "{" in line:
                variable = first_identifier(line[line.find("{") + 1 :], {"str", "id"})
                matches.append(self._build_match(index, line, variable, "f-string"))
                capture_assignment(line, index)
            elif "+" in line and re.search(r"""["'].*["']\s*\+|\+\s*["']""", line):
                variable = first_identifier(line.split("+")[-1])
                matches.append(
                    self._build_match(index, line, variable, "string concatenation")
                )
                capture_assignment(line, index)
            elif ".format(" in line:
                variable = first_identifier(line)
                matches.append(self._build_match(index, line, variable, ".format()"))
                capture_assignment(line, index)
            # Plain literal assignments (parameterized queries) are NOT unsafe.

        # Pass 2: sink calls receiving an unsafe variable are preferred targets.
        sink_findings: list[RuleMatch] = []
        consumed_build_lines: set[int] = set()
        for index, line in enumerate(lines, start=1):
            if "execute" not in line:
                continue
            for variable, (build_line, _build_code) in unsafe_vars.items():
                if build_line == index:
                    continue
                if re.search(rf"\b{re.escape(variable)}\b", line):
                    sink_findings.append(
                        self._build_match(index, line, variable, "unsafe query variable")
                    )
                    consumed_build_lines.add(build_line)
                    break

        sink_lines = {match.line for match in sink_findings}
        kept = [
            m
            for m in matches
            if m.line not in sink_lines and m.line not in consumed_build_lines
        ] + sink_findings
        seen: set[int] = set()
        unique: list[RuleMatch] = []
        for match in sorted(kept, key=lambda m: m.line):
            if match.line in seen:
                continue
            seen.add(match.line)
            unique.append(match)
        return unique

    def _build_match(
        self, line: int, code: str, variable: str | None, technique: str
    ) -> RuleMatch:
        variable = variable or "input"
        return RuleMatch(
            line=line,
            code=code.strip(),
            description=(
                "User-controlled input appears to reach SQL execution without "
                "safe parameterization."
            ),
            evidence=(
                f"The SQL query is constructed using {technique}"
                + (f" around `{variable}`" if variable else "")
                + " instead of bound parameters."
            ),
            flow=[
                "User Input",
                variable,
                "String Formatting",
                "SQL Query",
                "cursor.execute()",
            ],
        )


class CommandInjectionRule(SecurityRule):
    id = "PY-CMDI"
    name = "Command Injection Rule"
    description = "Shell commands are executed with data that is not a fixed literal."
    cwe = "CWE-78"
    severity = "CRITICAL"
    confidence = 94
    language = "python"
    recommendation = "Avoid shell execution; pass argument lists to subprocess without shell=True."
    fix_vulnerable = 'os.system("ping -c 1 " + host)'
    fix_secure = 'subprocess.run(["ping", "-c", "1", host], check=True)'
    fix_explanation = (
        "Running commands through a shell with concatenated input lets an attacker "
        "append arbitrary commands. Argument lists are passed to the OS verbatim."
    )
    flow = ["User Input", "Command String", "Shell", "Command Execution"]

    _SHELL_CALLS = re.compile(r"\b(os\.system|os\.popen|commands\.getoutput)\s*\(")
    _SUBPROCESS = re.compile(
        r"\bsubprocess\.(run|call|Popen|check_output|check_call)\s*\("
    )

    def detect(self, code: str, file_path: str) -> list[RuleMatch]:
        matches: list[RuleMatch] = []
        lines = _lines(code)
        for index, line in enumerate(lines, start=1):
            window = _call_window(lines, index - 1)
            if self._SHELL_CALLS.search(line):
                argument = window[window.find("(") + 1 : window.rfind(")")]
                if _is_plain_literal(argument):
                    continue  # fixed literal command: nothing dynamic to flag
                matches.append(self._match(index, line, "shell call"))
            elif self._SUBPROCESS.search(line) and re.search(
                r"shell\s*=\s*True", window
            ):
                matches.append(self._match(index, line, "subprocess with shell=True"))
        return matches

    def _match(self, line: int, code: str, technique: str) -> RuleMatch:
        return RuleMatch(
            line=line,
            code=code.strip(),
            description="A shell command is executed using dynamically built input.",
            evidence=f"Dangerous {technique} allows the operating system shell to interpret input.",
        )


class EvalRule(SecurityRule):
    id = "PY-EVAL"
    name = "Dangerous eval/exec Rule"
    description = "eval() or exec() executes dynamically constructed code."
    cwe = "CWE-95"
    severity = "CRITICAL"
    confidence = 96
    language = "python"
    recommendation = "Never pass untrusted data to eval/exec; use explicit parsers instead."
    fix_vulnerable = "result = eval(user_expression)"
    fix_secure = "result = ast.literal_eval(user_expression)"
    fix_explanation = (
        "eval/exec run arbitrary Python code from a string. An attacker controlling "
        "the string gains full code execution."
    )
    flow = ["User Input", "Code String", "eval()", "Code Execution"]

    _PATTERN = re.compile(r"(?<![\w.])(eval|exec)\s*\(")

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
                    description="Dynamic input is executed as Python code.",
                    evidence=(
                        f"{found.group(1)}() evaluates a string at runtime, "
                        "allowing arbitrary code execution."
                    ),
                )
            )
        return matches


class InsecureDeserializationRule(SecurityRule):
    id = "PY-DESER"
    name = "Insecure Deserialization Rule"
    description = "Untrusted data is deserialized with a format that can execute code."
    cwe = "CWE-502"
    severity = "HIGH"
    confidence = 89
    language = "python"
    recommendation = "Use safe data formats such as JSON; never unpickle untrusted data."
    fix_vulnerable = "data = pickle.loads(payload)"
    fix_secure = 'data = json.loads(payload.decode("utf-8"))'
    fix_explanation = (
        "Pickle payloads can contain malicious objects that run code while loading."
    )
    flow = ["Untrusted Data", "Serialized Blob", "pickle.loads()", "Object Creation"]

    _PATTERN = re.compile(
        r"\b(pickle|dill|marshal)\.loads?\s*\("
        r"|(?<![\w.])(yaml\.load|jsonpickle\.decode)\s*\("
    )

    def detect(self, code: str, file_path: str) -> list[RuleMatch]:
        matches = []
        for index, line in enumerate(_lines(code), start=1):
            if "safe_load" in line:
                continue
            if self._PATTERN.search(line):
                matches.append(
                    RuleMatch(
                        line=index,
                        code=line.strip(),
                        description="Serialized data is deserialized without integrity protection.",
                        evidence="Deserializing untrusted blobs can instantiate arbitrary objects and run code.",
                    )
                )
        return matches


class HardcodedCredentialsRule(SecurityRule):
    id = "PY-SECRETS"
    name = "Hardcoded Credentials Rule"
    description = "Credentials or API secrets are embedded directly in the source."
    cwe = "CWE-798"
    severity = "HIGH"
    confidence = 97
    language = "python"
    recommendation = "Load secrets from environment variables or a secrets manager."
    fix_vulnerable = 'SECRET_KEY = "super-secret-key-123"'
    fix_secure = 'SECRET_KEY = os.environ["SECRET_KEY"]'
    fix_explanation = (
        "Hardcoded secrets leak through repositories, builds and logs and "
        "cannot be rotated safely."
    )
    flow = ["Source Code", "Literal Assignment", "Secret Value", "Repository Leak"]

    _PATTERN = re.compile(
        r"""(?i)\b(?P<name>password|passwd|pwd|api_key|apikey|secret_key|secret_token|"""
        r"""token|access_token|auth_token|refresh_token|client_secret|private_key)"""
        r"""\b\s*[:=]\s*(?P<q>["'])(?P<value>[^"']{4,})(?P=q)"""
    )
    _IGNORE_VALUES = {"none", "null", "undefined", "true", "false", "changeme"}

    def detect(self, code: str, file_path: str) -> list[RuleMatch]:
        matches = []
        for index, line in enumerate(_lines(code), start=1):
            stripped = line.strip()
            if stripped.startswith("#") or stripped.startswith("*"):
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


class PathTraversalRule(SecurityRule):
    id = "PY-PATH"
    name = "Path Traversal Rule"
    description = "File paths are built by concatenating untrusted values."
    cwe = "CWE-22"
    severity = "HIGH"
    confidence = 88
    language = "python"
    recommendation = "Resolve paths against a fixed base directory and reject escapes."
    fix_vulnerable = 'open("/uploads/" + filename)'
    fix_secure = (
        'base = Path("/uploads").resolve()\n'
        "target = (base / filename).resolve()\n"
        'if not target.is_relative_to(base):\n'
        '    raise ValueError("Invalid path")\n'
        "open(target)"
    )
    fix_explanation = (
        "Concatenated paths let an attacker escape the intended directory with "
        "sequences such as ../../. Resolving against a whitelisted base prevents it."
    )
    flow = ["User Input", "Path Concatenation", "Filesystem Path", "open()"]

    _OPEN = re.compile(
        r"\b(open|Path|send_file|send_from_directory|read_text|write_text)\s*\("
    )
    _PATHY = re.compile(r"path|file|dir|name|upload|folder|target", re.IGNORECASE)
    _SUSPICIOUS_VALUE = re.compile(
        r"request\.|input\(|args\.|form\.|params\.|user_?\w*|filename|\w+_input",
        re.IGNORECASE,
    )

    def detect(self, code: str, file_path: str) -> list[RuleMatch]:
        lines = _lines(code)
        matches: list[RuleMatch] = []
        suspicious_vars: dict[str, int] = {}

        for index, line in enumerate(lines, start=1):
            # Assignment building a path from concatenated values.
            assign = re.match(r"""\s*([A-Za-z_]\w*)\s*=\s*(.+)$""", line)
            if assign and " + " in assign.group(2):
                name, value = assign.group(1), assign.group(2)
                literal_path = re.search(r"""["'][^"']*[/\\][^"']*["']""", value)
                if self._PATHY.search(name) and (
                    literal_path or self._SUSPICIOUS_VALUE.search(value)
                ):
                    suspicious_vars[name] = index

            if not self._OPEN.search(line):
                continue

            window = _call_window(lines, index - 1)
            argument = window[window.find("(") + 1 : window.rfind(")")]
            flag_line = None
            if " + " in argument:
                has_path_literal = re.search(r"""["'][^"']*[/\\][^"']*["']""", argument)
                has_variable = re.search(r"[A-Za-z_]\w*\s*$|\+\s*[A-Za-z_]\w*", argument)
                if has_path_literal or has_variable:
                    flag_line = index
            else:
                for name, assign_line in suspicious_vars.items():
                    if re.search(rf"\b{re.escape(name)}\b", argument):
                        flag_line = assign_line
                        break
            if flag_line is None:
                continue
            if any(match.line == flag_line for match in matches):
                continue
            target = lines[flag_line - 1]
            matches.append(
                RuleMatch(
                    line=flag_line,
                    code=target.strip(),
                    description="A file path is assembled from concatenated input.",
                    evidence="Untrusted values flow into a filesystem path, allowing directory traversal.",
                )
            )
        return matches


class WeakCryptographyRule(SecurityRule):
    id = "PY-WEAKHASH"
    name = "Weak Cryptography Rule"
    description = "A broken hash algorithm (MD5/SHA1) is used."
    cwe = "CWE-327"
    severity = "MEDIUM"
    confidence = 90
    language = "python"
    recommendation = "Use SHA-256+ for integrity and bcrypt/argon2 for passwords."
    fix_vulnerable = "hashed = hashlib.md5(password.encode()).hexdigest()"
    fix_secure = "hashed = hashlib.sha256(password.encode()).hexdigest()"
    fix_explanation = (
        "MD5 and SHA-1 are collision-broken and unsuitable for security decisions."
    )
    flow = ["Sensitive Data", "Weak Hash", "Digest", "Security Decision"]

    _PATTERN = re.compile(r"hashlib\.(md5|sha1)\s*\(")

    def detect(self, code: str, file_path: str) -> list[RuleMatch]:
        matches = []
        for index, line in enumerate(_lines(code), start=1):
            found = self._PATTERN.search(line)
            if not found:
                continue
            matches.append(
                RuleMatch(
                    line=index,
                    code=line.strip(),
                    description=f"Broken hash algorithm {found.group(1).upper()} is used.",
                    evidence="MD5/SHA-1 can be collided or brute-forced cheaply.",
                )
            )
        return matches


class DebugModeRule(SecurityRule):
    id = "PY-DEBUG"
    name = "Debug Mode Enabled Rule"
    description = "The application runs with debugging enabled."
    cwe = "CWE-489"
    severity = "MEDIUM"
    confidence = 86
    language = "python"
    recommendation = "Disable debug mode in production builds."
    fix_vulnerable = "app.run(debug=True)"
    fix_secure = 'app.run(debug=os.environ.get("FLASK_DEBUG") == "1")'
    fix_explanation = (
        "Debug mode exposes an interactive console and stack traces to attackers."
    )
    flow = ["Configuration", "Debug Flag", "Interactive Console", "Code Execution"]

    _PATTERN = re.compile(
        r"app\.run\s*\([^)]*debug\s*=\s*True"
        r"|\bDEBUG\s*=\s*True"
        r"|config\[[\"']DEBUG[\"']\]\s*=\s*True"
    )

    def detect(self, code: str, file_path: str) -> list[RuleMatch]:
        matches = []
        for index, line in enumerate(_lines(code), start=1):
            if self._PATTERN.search(line):
                matches.append(
                    RuleMatch(
                        line=index,
                        code=line.strip(),
                        description="Debug mode is explicitly enabled.",
                        evidence="debug=True exposes the interactive debugger and detailed tracebacks.",
                    )
                )
        return matches


class InsecureTlsRule(SecurityRule):
    id = "PY-TLS"
    name = "Disabled TLS Verification Rule"
    description = "TLS/SSL certificate verification is disabled."
    cwe = "CWE-295"
    severity = "MEDIUM"
    confidence = 92
    language = "python"
    recommendation = "Keep certificate verification enabled; fix the certificate chain instead."
    fix_vulnerable = "requests.get(url, verify=False)"
    fix_secure = "requests.get(url, verify=True)"
    fix_explanation = (
        "Disabling verification enables man-in-the-middle interception of the connection."
    )
    flow = ["Outbound Request", "verify=False", "Unverified TLS", "MITM Exposure"]

    _PATTERN = re.compile(r"verify\s*=\s*False")

    def detect(self, code: str, file_path: str) -> list[RuleMatch]:
        matches = []
        for index, line in enumerate(_lines(code), start=1):
            if self._PATTERN.search(line):
                matches.append(
                    RuleMatch(
                        line=index,
                        code=line.strip(),
                        description="Certificate verification is switched off.",
                        evidence="verify=False accepts any server certificate, including forged ones.",
                    )
                )
        return matches


class WeakRandomRule(SecurityRule):
    id = "PY-WEAKRNG"
    name = "Weak Random Token Rule"
    description = "A non-cryptographic RNG generates security-sensitive values."
    cwe = "CWE-338"
    severity = "MEDIUM"
    confidence = 84
    language = "python"
    recommendation = "Use secrets or os.urandom for tokens, nonces and session identifiers."
    fix_vulnerable = "session_token = random.randint(100000, 999999)"
    fix_secure = "session_token = secrets.token_hex(32)"
    fix_explanation = (
        "PRNG output is predictable, so generated tokens can be guessed or replayed."
    )
    flow = ["Security Token", "random.*", "Predictable PRNG", "Token Guessing"]

    _PATTERN = re.compile(
        r"""(?i)\b\w*(token|secret|session|nonce|otp|password|csrf)\w*\s*=\s*"""
        r"""[^#\n]*\brandom\.(random|randint|randrange|choice|choices|getrandbits)\s*\("""
    )

    def detect(self, code: str, file_path: str) -> list[RuleMatch]:
        matches = []
        for index, line in enumerate(_lines(code), start=1):
            if self._PATTERN.search(line):
                matches.append(
                    RuleMatch(
                        line=index,
                        code=line.strip(),
                        description="A security-sensitive value comes from a predictable RNG.",
                        evidence="random.* is predictable and must not protect secrets.",
                    )
                )
        return matches


class InsecureTransportRule(SecurityRule):
    id = "PY-HTTP"
    name = "Cleartext HTTP Rule"
    description = "Data is transmitted over unencrypted HTTP."
    cwe = "CWE-319"
    severity = "LOW"
    confidence = 80
    language = "python"
    recommendation = "Use HTTPS for all network communication."
    fix_vulnerable = 'requests.get("http://api.example.com/users")'
    fix_secure = 'requests.get("https://api.example.com/users")'
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


PYTHON_RULES = [
    SqlInjectionRule,
    CommandInjectionRule,
    EvalRule,
    InsecureDeserializationRule,
    HardcodedCredentialsRule,
    PathTraversalRule,
    WeakCryptographyRule,
    DebugModeRule,
    InsecureTlsRule,
    WeakRandomRule,
    InsecureTransportRule,
]




