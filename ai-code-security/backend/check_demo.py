"""Quick verification scan of the built-in demo project."""

from pathlib import Path

from analyzer.project_scanner import analyze_structure, run_scan

root = Path(__file__).resolve().parent / "demo_project"
structure = analyze_structure(root, "FairShare")
print(
    "files:",
    structure["files_found"],
    "| source:",
    structure["source_files"],
    "| by_language:",
    structure["by_language"],
    "| ignored:",
    structure["ignored"],
)

result = run_scan(root, "FairShare", "testscan", extracted=False)
project = result["project"]
stats = result["stats"]
print(
    "scanned:",
    project["files_scanned"],
    "| lines:",
    project["lines_analyzed"],
    "| rules:",
    stats["rules_executed"],
    "| duration:",
    stats["duration_seconds"],
)
print("summary:", result["summary"])
for finding in result["findings"]:
    print(
        finding["id"],
        finding["severity"],
        finding["cwe"],
        f"{finding['file']}:{finding['line']}",
        "|",
        finding["title"],
        "| conf",
        finding["confidence"],
    )
