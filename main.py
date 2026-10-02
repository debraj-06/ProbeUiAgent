from __future__ import annotations

import argparse
import asyncio
import json
from pathlib import Path

from app.analyzer import analyze_viewport
from app.auditor import audit_url


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Local UI/UX + frontend bug detection agent")
    parser.add_argument("url", help="Website URL, e.g. https://example.com")
    parser.add_argument("--output", default="reports/run.json", help="Output JSON report path")
    return parser.parse_args()


def dedupe(bugs: list[dict]) -> list[dict]:
    merged: dict[tuple[str, str], dict] = {}
    for bug in bugs:
        key = (bug["category"], bug["title"].strip().lower())
        if key not in merged:
            merged[key] = bug
            continue
        current = merged[key]
        existing_viewports = {current["viewport"]}
        if current["viewport"] != "all":
            existing_viewports.add(current["viewport"])
        if bug["viewport"] not in existing_viewports:
            current["viewport"] = "all"
        if bug["confidence"] > current["confidence"]:
            current["confidence"] = bug["confidence"]
        if bug["severity"] == "critical":
            current["severity"] = "critical"
        elif bug["severity"] == "high" and current["severity"] not in {"critical"}:
            current["severity"] = "high"
    return list(merged.values())


def main() -> None:
    args = parse_args()
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    print(f"\n[1/3] Auditing: {args.url}")
    audit_results = asyncio.run(audit_url(args.url, "."))

    print("[2/3] Running local vision model...")
    all_bugs: list[dict] = []
    summaries: list[str] = []

    for result in audit_results:
        print(f"  -> {result['viewport']}")
        try:
            analysis = analyze_viewport(result)
            summaries.append(f"{result['viewport']}: {analysis.summary}")
            all_bugs.extend([bug.model_dump() for bug in analysis.bugs])
        except Exception as exc:
            print(f"  !! Model analysis failed for {result['viewport']}: {exc}")

    report = {
        "url": args.url,
        "agent": "ui-ux-frontend",
        "summary": " | ".join(summaries),
        "bug_count": len(dedupe(all_bugs)),
        "bugs": dedupe(all_bugs),
        "browser_audit": audit_results,
    }

    output_path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")

    print("[3/3] Done")
    print(f"Report: {output_path}")
    print(f"Bugs found: {report['bug_count']}")
    print(json.dumps(report["bugs"], indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
