#!/usr/bin/env python3
"""CampusLaunch AI — comprehensive auto-onboarding demonstration.

A presentation-grade walkthrough of how **CanonIQ** auto-onboards multiple
universities into a shared canonical data model — the kind of multi-tenant data
onboarding an AI advising platform (here, the fictional *CampusLaunch AI*) faces
every time it signs a new school.

It runs the real CanonIQ pipeline (no mocks) over three schools and narrates, in
business terms, exactly what happened and why it matters:

  • the messy → canonical field mappings each school needs (with confidence + reasons)
  • a per-source breakdown (profiled, mapped, auto-approved, flagged, drift)
  • the weighted readiness score and what drove it
  • the deployment-ready package CanonIQ emits
  • a portfolio roll-up across all schools
  • an illustrative business-value / ROI summary

Run it (no arguments, no network)::

    python examples/higher_ed_auto_onboarding/demo_auto_onboard.py

Equivalent CLI::

    canoniq onboard-batch \
        --config-dir examples/higher_ed_auto_onboarding/onboarding_configs \
        --combined-out examples/higher_ed_auto_onboarding/output/combined_readiness.json
"""

from __future__ import annotations

import os

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from canoniq import __version__
from canoniq.engine import CanonIQ
from canoniq.onboarding import load_onboarding_config, onboard_providers
from canoniq.onboarding.models import (
    STATUS_BLOCKED,
    STATUS_NEEDS_REVIEW,
    STATUS_READY_AUTO,
    STATUS_READY_MINOR,
)

HERE = os.path.dirname(os.path.abspath(__file__))
CONFIG_DIR = os.path.join(HERE, "onboarding_configs")
COMBINED_OUT = os.path.join(HERE, "output", "combined_readiness.json")

console = Console()

# Per-school narrative + the headline source to spotlight at field level.
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


def print_intro() -> None:
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
    console.print(Panel(body, title="Use case · CampusLaunch AI auto-onboarding", border_style="cyan"))


def print_pipeline() -> None:
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


def _spotlight_source(report_id: str):
    """Re-run profile+map on the SIS source so we can show field-level detail."""
    cfg = load_onboarding_config(os.path.join(CONFIG_DIR, f"{report_id}.yml"))
    sis = next((s for s in cfg.sources if s.name == "sis_students"), cfg.sources[0])
    eng = CanonIQ()
    profile = eng.profile_source(sis.path)
    mapping = eng.suggest_mappings(profile, sis.canonical)
    return sis.name, mapping


def print_school(report) -> None:
    note = SCHOOL_NOTES.get(report.provider_id, {"profile": "", "outcome": ""})
    style = _STATUS_STYLE.get(report.status, "white")

    console.rule(f"[bold]{report.provider_name}[/bold]")
    console.print(f"[dim]Situation:[/dim] {note['profile']}")

    # --- field-level mappings on the spotlight (SIS) source ---
    src_name, mapping = _spotlight_source(report.provider_id)
    ft = Table(title=f"Field mappings · {src_name} (messy source → canonical 'student')")
    ft.add_column("source column", style="bold")
    ft.add_column("→ canonical field")
    ft.add_column("conf", justify="right")
    ft.add_column("status")
    ft.add_column("why", style="dim")
    for m in mapping.mappings:
        st = _MAP_STYLE.get(m.status, "white")
        why = m.reasons[0] if m.reasons else "—"
        ft.add_row(
            m.source_field,
            m.canonical_field or "[red](unmapped)[/red]",
            f"{m.confidence:.2f}",
            f"[{st}]{m.status}[/{st}]",
            why,
        )
    console.print(ft)

    # --- per-source summary across all of the school's feeds ---
    st = Table(title="All sources for this school")
    st.add_column("source")
    st.add_column("entity")
    st.add_column("mapped", justify="right")
    st.add_column("auto", justify="right")
    st.add_column("review", justify="right")
    st.add_column("low/unmapped", justify="right")
    st.add_column("validation")
    st.add_column("drift")
    for s in report.sources:
        valid = "pass" if s.validation_passed else f"[red]{s.validation_failures} fail[/red]"
        drift_style = {"no_drift": "green", "drift_detected": "red"}.get(s.drift_status, "dim")
        st.add_row(
            s.source,
            s.entity,
            f"{s.mapped_fields}/{s.total_source_fields}",
            str(s.auto_approved),
            str(s.requires_review),
            f"{s.low_confidence}/{s.unmapped}",
            f"{valid} ({s.validation_findings})",
            f"[{drift_style}]{s.drift_status}[/{drift_style}]",
        )
    console.print(st)

    # --- readiness component breakdown ---
    ct = Table(title="Readiness score = Σ (ratio × weight × 100)")
    ct.add_column("component")
    ct.add_column("weight", justify="right")
    ct.add_column("ratio", justify="right")
    ct.add_column("points", justify="right")
    for name, comp in report.component_scores.items():
        ct.add_row(name, f"{comp.weight:.0%}", f"{comp.ratio:.2f}", f"{comp.points:.1f}")
    ct.add_row("[bold]TOTAL[/bold]", "", "", f"[bold]{report.readiness_score}[/bold]")
    console.print(ct)

    # --- verdict + deployment package ---
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
    verdict.append("source profiles · approved mappings · validation rules · "
                   "canonical CSVs · drift report · readiness_report.json")
    console.print(Panel(verdict, title=f"Verdict · {note['outcome']}", border_style=style.split()[-1]))


def print_portfolio(combined) -> None:
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


def print_business_value(reports) -> None:
    total_fields = sum(s.total_source_fields for r in reports for s in r.sources)
    auto = sum(s.auto_approved for r in reports for s in r.sources)
    review = sum(s.requires_review for r in reports for s in r.sources)
    held = sum(s.low_confidence + s.unmapped for r in reports for s in r.sources)
    # Illustrative: hand-mapping + validating a cross-system field ~15 min.
    minutes_manual = total_fields * 15
    body = Text()
    body.append("Across these 3 schools CanonIQ profiled ", )
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


def main() -> None:
    print_intro()
    print_pipeline()

    reports, combined = onboard_providers(
        CONFIG_DIR, write_outputs=True, combined_out=COMBINED_OUT, canoniq_version=__version__
    )

    for report in reports:
        print_school(report)

    console.rule("[bold]Portfolio[/bold]")
    print_portfolio(combined)
    print_business_value(reports)
    console.print(
        f"\n[dim]CanonIQ {__version__} · local-first · no data left this machine. "
        f"Per-school reports + combined summary written under[/dim] output/."
    )


if __name__ == "__main__":
    main()
