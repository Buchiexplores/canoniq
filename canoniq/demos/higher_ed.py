"""CampusLaunch AI — comprehensive higher-education auto-onboarding walkthrough.

A presentation-grade narration of how CanonIQ auto-onboards multiple universities
into a shared canonical model — the multi-tenant data-onboarding problem an AI
advising platform faces every time it signs a new school. It runs the real pipeline
(no mocks) over three bundled schools and explains, in business terms, what happened
and why it matters.

The data is shipped inside the package (``canoniq/demo_data/higher_ed_onboarding/``),
so this works from a plain ``pip install canoniq`` via ``canoniq demo higher-ed``.
The repo's ``examples/higher_ed_auto_onboarding/demo_auto_onboard.py`` is a thin
wrapper over :func:`run_campuslaunch_demo`.
"""

from __future__ import annotations

import os

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from canoniq.engine import CanonIQ
from canoniq.onboarding import load_onboarding_config, onboard_providers
from canoniq.onboarding.models import (
    STATUS_BLOCKED,
    STATUS_NEEDS_REVIEW,
    STATUS_READY_AUTO,
    STATUS_READY_MINOR,
)

# Packaged onboarding configs (ship in the wheel).
HIGHER_ED_CONFIG_DIR = os.path.join(
    os.path.dirname(__file__), "..", "demo_data", "higher_ed_onboarding", "onboarding_configs"
)
HIGHER_ED_CONFIG_DIR = os.path.normpath(HIGHER_ED_CONFIG_DIR)

SCHOOL_NOTES: dict[str, dict[str, str]] = {
    "northlake_university": {
        "profile": "Clean, well-named Banner SIS export. Complete data, stable schema.",
        "outcome": "The happy path — flows straight through to staging.",
    },
    "redwood_college": {
        "profile": "Solid exports, but a couple of columns don't map and the advising "
        "feed is missing a required field.",
        "outcome": "Promising, but a reviewer should confirm the flagged items first.",
    },
    "pacific_state_university": {
        "profile": "Cryptic headers, no email column anywhere, and a next batch that has "
        "already drifted.",
        "outcome": "Held back — a human must intervene before this school can deploy.",
    },
}

_STATUS_STYLE = {
    STATUS_READY_AUTO: "bold green",
    STATUS_READY_MINOR: "bold yellow",
    STATUS_NEEDS_REVIEW: "bold dark_orange",
    STATUS_BLOCKED: "bold red",
}
_MAP_STYLE = {
    "auto_approved": "green",
    "requires_review": "yellow",
    "low_confidence": "dark_orange",
    "unmapped": "red",
}


def _print_intro(console: Console) -> None:
    body = Text()
    body.append("CampusLaunch AI", style="bold cyan")
    body.append(
        " is an AI advising platform: degree planning, at-risk detection, advisor "
        "outreach. Every new university arrives with its own SIS / LMS / advising "
        "exports under different column names:\n\n"
    )
    body.append("  School A  ", style="dim")
    body.append("banner_id, student_email, cumulative_gpa, canvas_last_activity\n")
    body.append("  School B  ", style="dim")
    body.append("emplid, primary_email, overall_gpa, last_login_date\n")
    body.append("  School C  ", style="dim")
    body.append("student_number, institutional_email, term_gpa, lms_last_seen\n\n")
    body.append("The challenge: ", style="bold")
    body.append("onboard many schools fast — ")
    body.append("without hand-writing schema-mapping code for each one", style="italic")
    body.append(".\nCanonIQ turns that bespoke engineering into a ")
    body.append("config-driven, scored, auditable", style="bold")
    body.append(" workflow.")
    console.print(
        Panel(body, title="Use case · CampusLaunch AI auto-onboarding", border_style="cyan")
    )


def _print_pipeline(console: Console) -> None:
    steps = [
        ("1  Config", "read each school's onboarding YAML (sources → canonical entity)"),
        ("2  Profile", "infer types, value patterns, and PII for every source field"),
        ("3  Map", "score source→canonical mappings (alias · name · type · pattern · range)"),
        ("4  Gate", "auto-approve ≥0.90 · flag 0.70–0.90 · hold <0.70"),
        ("5  Validate", "generate + run rules from the canonical schema"),
        ("6  Transform", "emit canonical records (review-grade mappings included)"),
        ("7  Drift", "compare the next batch against the learned mapping"),
        ("8  Score", "weighted readiness 0–100 → status band → next action"),
        ("9  Package", "write the deployment-ready artifacts; gate auto-deploy"),
    ]
    t = Table(show_header=False, box=None, padding=(0, 2, 0, 0))
    t.add_column(style="bold cyan", no_wrap=True)
    t.add_column()
    for stage, desc in steps:
        t.add_row(stage, desc)
    console.print(Panel(t, title="The auto-onboarding pipeline (per school)", border_style="blue"))


def _spotlight_source(config_dir: str, report_id: str):
    """Re-run profile+map on the SIS source so we can show field-level detail."""
    cfg = load_onboarding_config(os.path.join(config_dir, f"{report_id}.yml"))
    sis = next((s for s in cfg.sources if s.name == "sis_students"), cfg.sources[0])
    eng = CanonIQ()
    profile = eng.profile_source(sis.path)
    return sis.name, eng.suggest_mappings(profile, sis.canonical)


def _print_school(console: Console, config_dir: str, report) -> None:
    note = SCHOOL_NOTES.get(report.provider_id, {"profile": "", "outcome": ""})
    style = _STATUS_STYLE.get(report.status, "white")

    console.rule(f"[bold]{report.provider_name}[/bold]")
    console.print(f"[dim]Situation:[/dim] {note['profile']}")

    src_name, mapping = _spotlight_source(config_dir, report.provider_id)
    ft = Table(title=f"Field mappings · {src_name} (messy source → canonical 'student')")
    ft.add_column("source column", style="bold")
    ft.add_column("→ canonical field")
    ft.add_column("conf", justify="right")
    ft.add_column("status")
    ft.add_column("why", style="dim")
    for m in mapping.mappings:
        mstyle = _MAP_STYLE.get(m.status, "white")
        why = m.reasons[0] if m.reasons else "—"
        ft.add_row(
            m.source_field,
            m.canonical_field or "[red](unmapped)[/red]",
            f"{m.confidence:.2f}",
            f"[{mstyle}]{m.status}[/{mstyle}]",
            why,
        )
    console.print(ft)

    srct = Table(title="All sources for this school")
    for col in ("source", "entity"):
        srct.add_column(col)
    for col in ("mapped", "auto", "review", "low/unmapped"):
        srct.add_column(col, justify="right")
    srct.add_column("validation")
    srct.add_column("drift")
    for s in report.sources:
        valid = "pass" if s.validation_passed else f"[red]{s.validation_failures} fail[/red]"
        drift_style = {"no_drift": "green", "drift_detected": "red"}.get(s.drift_status, "dim")
        srct.add_row(
            s.source,
            s.entity,
            f"{s.mapped_fields}/{s.total_source_fields}",
            str(s.auto_approved),
            str(s.requires_review),
            f"{s.low_confidence}/{s.unmapped}",
            f"{valid} ({s.validation_findings})",
            f"[{drift_style}]{s.drift_status}[/{drift_style}]",
        )
    console.print(srct)

    ct = Table(title="Readiness score = Σ (ratio × weight × 100)")
    ct.add_column("component")
    ct.add_column("weight", justify="right")
    ct.add_column("ratio", justify="right")
    ct.add_column("points", justify="right")
    for name, comp in report.component_scores.items():
        ct.add_row(name, f"{comp.weight:.0%}", f"{comp.ratio:.2f}", f"{comp.points:.1f}")
    ct.add_row("[bold]TOTAL[/bold]", "", "", f"[bold]{report.readiness_score}[/bold]")
    console.print(ct)

    verdict = Text()
    verdict.append("readiness ", style="dim")
    verdict.append(f"{report.readiness_score}/100  ", style=style)
    verdict.append(f"{report.status}\n", style=style)
    verdict.append("auto-deploy allowed: ", style="dim")
    verdict.append(
        "YES\n" if report.auto_deploy_allowed else "NO\n",
        style="green" if report.auto_deploy_allowed else "red",
    )
    verdict.append("next action: ", style="dim")
    verdict.append(f"{report.next_action}\n", style="bold")
    verdict.append("required fields covered: ", style="dim")
    verdict.append("yes\n" if report.summary.required_fields_covered else "no\n")
    verdict.append("\n")
    verdict.append(report.deployment_recommendation, style="italic")
    verdict.append("\n\nDeployment-ready package: ", style="dim")
    verdict.append(
        "source profiles · approved mappings · validation rules · canonical CSVs · "
        "drift report · readiness_report.json"
    )
    console.print(
        Panel(verdict, title=f"Verdict · {note['outcome']}", border_style=style.split()[-1])
    )


def _print_portfolio(console: Console, combined) -> None:
    t = Table(title="Portfolio roll-up — CampusLaunch AI onboarding cohort")
    t.add_column("school")
    t.add_column("score", justify="right")
    t.add_column("status")
    t.add_column("auto-deploy", justify="center")
    for e in combined.providers:
        style = _STATUS_STYLE.get(e.status, "white").split()[-1]
        t.add_row(
            e.provider_name,
            f"[{style}]{e.readiness_score}[/{style}]",
            f"[{style}]{e.status}[/{style}]",
            "✓" if e.auto_deploy_allowed else "—",
        )
    console.print(t)
    console.print(
        f"  [green]{combined.ready_for_auto_deploy}[/green] auto-deploy · "
        f"[yellow]{combined.ready_with_minor_review}[/yellow] minor review · "
        f"[dark_orange]{combined.needs_mapping_review}[/dark_orange] needs review · "
        f"[red]{combined.blocked}[/red] blocked   "
        f"(of {combined.total_providers} schools)"
    )


def _print_business_value(console: Console, reports) -> None:
    total_fields = sum(s.total_source_fields for r in reports for s in r.sources)
    auto = sum(s.auto_approved for r in reports for s in r.sources)
    review = sum(s.requires_review for r in reports for s in r.sources)
    held = sum(s.low_confidence + s.unmapped for r in reports for s in r.sources)
    minutes_manual = total_fields * 15  # illustrative: ~15 min to hand-map+validate a field
    body = Text()
    body.append("Across these 3 schools CanonIQ profiled ")
    body.append(f"{total_fields} source fields", style="bold")
    body.append(" and proposed every mapping with a reason:\n\n")
    body.append(f"  • {auto} ", style="bold green")
    body.append("auto-approved (zero human touch)\n")
    body.append(f"  • {review} ", style="bold yellow")
    body.append("flagged for a quick reviewer confirmation\n")
    body.append(f"  • {held} ", style="bold red")
    body.append("held back as too uncertain to guess\n\n")
    body.append("Hand-mapping + validating those fields at ~15 min each ≈ ", style="dim")
    body.append(f"{minutes_manual // 60}h {minutes_manual % 60}m", style="bold")
    body.append(" of engineering for the first pass alone — repeated, error-prone, and "
                "undocumented.\n")
    body.append("With CanonIQ it runs in seconds, ", style="dim")
    body.append("humans only review the flagged items", style="bold")
    body.append(", every decision is explained and auditable, and ")
    body.append("the next school is config-only", style="bold")
    body.append(" — no new code.\n\n")
    body.append("Schema drift (a school renaming a column next term) is ", style="dim")
    body.append("caught and re-mapped", style="bold")
    body.append(" instead of silently breaking the advising dashboard.")
    console.print(Panel(body, title="Why this is valuable (illustrative ROI)", border_style="green"))


def run_campuslaunch_demo(
    console: Console | None = None,
    *,
    config_dir: str | None = None,
    out_dir: str | None = None,
    version: str | None = None,
) -> None:
    """Render the comprehensive CampusLaunch AI onboarding walkthrough.

    Parameters
    ----------
    console: a Rich console (one is created if omitted).
    config_dir: directory of onboarding configs (defaults to the packaged data).
    out_dir: if given, per-school + combined readiness JSON are written here.
    version: CanonIQ version string to stamp into written reports.
    """
    con = console or Console()
    cfg_dir = config_dir or HIGHER_ED_CONFIG_DIR

    _print_intro(con)
    _print_pipeline(con)

    # Compute readiness in-memory; we write artifacts ourselves so the packaged
    # configs' output paths never get touched (they'd point inside site-packages).
    reports, combined = onboard_providers(cfg_dir, write_outputs=False, canoniq_version=version)

    for report in reports:
        _print_school(con, cfg_dir, report)

    con.rule("[bold]Portfolio[/bold]")
    _print_portfolio(con, combined)
    _print_business_value(con, reports)

    if out_dir:
        os.makedirs(out_dir, exist_ok=True)
        for report in reports:
            CanonIQ.write_json(report, os.path.join(out_dir, f"{report.provider_id}_readiness.json"))
        CanonIQ.write_json(combined, os.path.join(out_dir, "combined_readiness.json"))
        con.print(f"\n[dim]Wrote per-school + combined readiness reports to[/dim] {out_dir}")

    con.print(
        f"[dim]CanonIQ {version or ''} · local-first · no data left this machine.[/dim]".replace(
            "  ", " "
        )
    )
