"""Comprehensive single-source pipeline walkthrough for a bundled domain.

Powers ``canoniq demo <retail|healthcare|finance|logistics>`` — a narrated,
presentation-grade run of the full CanonIQ pipeline against one domain's bundled
synthetic data. Like the higher-education walkthrough, it explains the use case,
shows the pipeline, then surfaces the field-level mappings (with reasons), the
validation findings, the transform result, and the drift detected on the next batch
— ending with a "why it matters" takeaway.

Ships in the package, so it works straight from ``pip install canoniq``.
"""

from __future__ import annotations

import os

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from canoniq.domains import DEMO_STAR, domain_paths
from canoniq.engine import CanonIQ

_MAP_STYLE = {
    "auto_approved": "green",
    "requires_review": "yellow",
    "low_confidence": "dark_orange",
    "unmapped": "red",
}


def _print_intro(console: Console, domain: str, entity: str) -> None:
    star = DEMO_STAR.get(domain, {})
    body = Text()
    if star.get("situation"):
        body.append("Situation  ", style="bold")
        body.append(star["situation"] + "\n\n")
    if star.get("task"):
        body.append("Task       ", style="bold")
        body.append(star["task"] + "\n\n")
    body.append("Action     ", style="bold")
    body.append(f"canoniq demo {domain}  ")
    body.append("(profile → map → validate → transform → drift)", style="dim")
    console.print(
        Panel(body, title=f"Use case · {domain} → canonical '{entity}'", border_style="cyan")
    )


def _print_pipeline(console: Console) -> None:
    steps = [
        ("1  Profile", "infer types, value patterns, and PII for every source field"),
        ("2  Map", "score source→canonical mappings (alias · name · type · pattern · range)"),
        ("3  Validate", "generate rules from the canonical schema and run them on the data"),
        ("4  Transform", "emit canonical records (review-grade mappings included)"),
        ("5  Drift", "compare the next batch against the learned mapping"),
    ]
    t = Table(show_header=False, box=None, padding=(0, 2, 0, 0))
    t.add_column(style="bold cyan", no_wrap=True)
    t.add_column()
    for stage, desc in steps:
        t.add_row(stage, desc)
    console.print(Panel(t, title="The pipeline", border_style="blue"))


def _print_mappings(console: Console, entity: str, mapping) -> None:
    t = Table(title=f"Field mappings · messy source → canonical '{entity}'")
    t.add_column("source column", style="bold")
    t.add_column("→ canonical field")
    t.add_column("conf", justify="right")
    t.add_column("status")
    t.add_column("why", style="dim")
    for m in mapping.mappings:
        mstyle = _MAP_STYLE.get(m.status, "white")
        t.add_row(
            m.source_field,
            m.canonical_field or "[red](unmapped)[/red]",
            f"{m.confidence:.2f}",
            f"[{mstyle}]{m.status}[/{mstyle}]",
            m.reasons[0] if m.reasons else "—",
        )
    console.print(t)


def _print_validation(console: Console, rules, report) -> None:
    t = Table(title=f"Validation · {len(rules)} rules generated from the canonical schema")
    t.add_column("field")
    t.add_column("rule")
    t.add_column("severity")
    t.add_column("result")
    # Show the findings (what actually ran against the data).
    shown = report.findings[:12]
    for f in shown:
        ok = "[green]pass[/green]" if f.passed else f"[red]fail ({f.failed_count})[/red]"
        t.add_row(f.field, f.rule, f.severity, ok)
    if len(report.findings) > len(shown):
        t.add_row("…", f"+{len(report.findings) - len(shown)} more", "", "")
    console.print(t)
    overall = "[green]PASSED[/green]" if report.passed else "[red]FAILED[/red]"
    console.print(f"  overall validation: {overall}  ·  rows checked: {report.row_count}")


def _print_transform(console: Console, entity: str, transformed) -> None:
    n = len(transformed.records)
    sample = transformed.records[0] if transformed.records else {}
    preview = ", ".join(f"{k}={v!r}" for k, v in list(sample.items())[:4])
    body = Text()
    body.append(f"{n} rows", style="bold")
    body.append(f" transformed into canonical '{entity}' records.\n")
    if preview:
        body.append("first row: ", style="dim")
        body.append(preview + (" …" if len(sample) > 4 else ""))
    console.print(Panel(body, title="Transform", border_style="blue"))


def _print_drift(console: Console, drift) -> None:
    style = "red" if drift.status == "drift_detected" else "green"
    body = Text()
    body.append("status: ", style="dim")
    body.append(f"{drift.status}\n", style=style)
    if drift.missing_fields:
        body.append("missing in next batch: ", style="dim")
        body.append(", ".join(drift.missing_fields) + "\n")
    if drift.new_fields:
        body.append("new in next batch: ", style="dim")
        body.append(", ".join(drift.new_fields) + "\n")
    if drift.type_changes:
        body.append(f"type changes: {len(drift.type_changes)}\n", style="dim")
    if drift.suggested_remappings:
        body.append("suggested remappings:\n", style="dim")
        for r in drift.suggested_remappings[:5]:
            body.append(
                f"  • {r.get('source_field')} → {r.get('canonical_field')} "
                f"({r.get('confidence', 0):.2f})\n"
            )
    if not (drift.missing_fields or drift.new_fields or drift.suggested_remappings):
        body.append("no schema changes — the learned mapping still fits.", style="dim")
    console.print(Panel(body, title="Drift detection (next ingestion)", border_style=style))


def _print_value(console: Console, domain: str, mapping) -> None:
    star = DEMO_STAR.get(domain, {})
    auto = sum(1 for m in mapping.mappings if m.status == "auto_approved")
    review = sum(1 for m in mapping.mappings if m.status == "requires_review")
    held = sum(1 for m in mapping.mappings if m.status in ("low_confidence", "unmapped"))
    body = Text()
    body.append(f"{len(mapping.mappings)} source fields", style="bold")
    body.append(" profiled, every mapping proposed with a reason:\n")
    body.append(f"  • {auto} ", style="bold green")
    body.append("auto-approved   ")
    body.append(f"• {review} ", style="bold yellow")
    body.append("need review   ")
    body.append(f"• {held} ", style="bold red")
    body.append("held back\n\n")
    if star.get("value"):
        body.append(star["value"])
    console.print(Panel(body, title="Why it matters", border_style="green"))


def run_pipeline_demo(
    console: Console,
    domain: str,
    *,
    out_dir: str | None = None,
    config_path: str | None = None,
    version: str | None = None,
) -> None:
    """Render the comprehensive single-source pipeline walkthrough for ``domain``."""
    from canoniq.config import CanonIQConfig

    paths = domain_paths(domain)
    entity = paths["entity"]
    engine = CanonIQ(CanonIQConfig.from_yaml(config_path) if config_path else CanonIQConfig())

    _print_intro(console, domain, entity)
    _print_pipeline(console)

    profile = engine.profile_source(paths["source"])
    mapping = engine.suggest_mappings(profile, paths["canonical"])
    rules = engine.generate_validation_rules(mapping, paths["canonical"], profile)
    transformed = engine.apply_mapping(
        paths["source"], mapping, paths["canonical"], include_review=True
    )
    report = engine.validate(transformed.records, rules)
    drift = engine.detect_drift(paths["new_source"], mapping, paths["canonical"])

    console.rule("[bold]Result[/bold] — what CanonIQ produced")
    _print_mappings(console, entity, mapping)
    _print_validation(console, rules, report)
    _print_transform(console, entity, transformed)
    _print_drift(console, drift)
    _print_value(console, domain, mapping)

    if out_dir:
        from canoniq.registry import save_mapping
        from canoniq.validation.rule_generator import save_rules

        dest = os.path.join(out_dir, entity)
        os.makedirs(dest, exist_ok=True)
        engine.write_json(profile, os.path.join(dest, "profile.json"))
        save_mapping(mapping, os.path.join(dest, "suggestions.json"))
        save_rules(rules, os.path.join(dest, "validation_rules.yml"), canoniq_version=version)
        engine.write_canonical_csv(transformed, os.path.join(dest, f"canonical_{entity}.csv"))
        engine.write_json(drift, os.path.join(dest, "drift_report.json"))
        console.print(f"\n[dim]Wrote artifacts to[/dim] {dest}")
