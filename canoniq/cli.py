"""Typer + Rich CLI (§21).

All commands accept ``--source`` (a file) or ``--source-config`` (a YAML config) where
input is required. The ``demo`` command runs the full pipeline end-to-end.
"""

from __future__ import annotations

import json

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from canoniq import __version__
from canoniq.config import CanonIQConfig
from canoniq.domains import DEMO_STAR, DOMAINS, domain_paths
from canoniq.engine import CanonIQ
from canoniq.registry import load_mapping, save_mapping
from canoniq.validation.rule_generator import save_rules

app = typer.Typer(
    add_completion=False,
    help="CanonIQ — map messy source data into trusted canonical models (local-first).",
    no_args_is_help=True,
)
console = Console()
err_console = Console(stderr=True)


def _engine(config_path: str | None = None) -> CanonIQ:
    cfg = CanonIQConfig.from_yaml(config_path) if config_path else CanonIQConfig()
    return CanonIQ(cfg)


# Reusable option so every command can load thresholds, weights, and the optional
# AI adapter from one YAML file — enabling a model is a one-line config change.
_CONFIG_OPTION = typer.Option(
    None, "--config", help="Path to a CanonIQ config YAML (thresholds, weights, AI adapter)."
)


def _profile_input(
    engine: CanonIQ, source: str | None, source_config: str | None
):
    if source and source_config:
        raise typer.BadParameter("Provide either --source or --source-config, not both.")
    if source:
        return engine.profile_source(source)
    if source_config:
        return engine.profile_source_config(source_config)
    raise typer.BadParameter("One of --source or --source-config is required.")


@app.command()
def version() -> None:
    """Print the CanonIQ version."""
    console.print(f"CanonIQ {__version__}")


@app.command()
def profile(
    source: str | None = typer.Option(None, "--source", help="Path to a CSV/JSON/JSONL file."),
    source_config: str | None = typer.Option(
        None, "--source-config", help="Path to a source-config YAML."
    ),
    out: str = typer.Option("profile.json", "--out", help="Output profile JSON path."),
    config: str | None = _CONFIG_OPTION,
) -> None:
    """Profile a source dataset (types, nulls, uniqueness, patterns, PII)."""
    engine = _engine(config)
    try:
        prof = _profile_input(engine, source, source_config)
    except Exception as exc:  # noqa: BLE001 — surface a clean CLI error
        err_console.print(f"[red]profile failed:[/red] {exc}")
        raise typer.Exit(code=1) from exc

    engine.write_json(prof, out)
    table = Table(title="Source Profile", show_lines=False)
    table.add_column("field")
    table.add_column("type")
    table.add_column("null%", justify="right")
    table.add_column("unique%", justify="right")
    table.add_column("pii")
    for f in prof.fields:
        table.add_row(
            f.name,
            f.inferred_type,
            f"{f.null_rate * 100:.0f}",
            f"{f.unique_rate * 100:.0f}",
            ",".join(f.pii_flags) or "-",
        )
    console.print(table)
    console.print(f"[green]wrote[/green] {out} ({len(prof.fields)} fields, {prof.row_count_sampled} rows)")


@app.command()
def suggest(
    profile: str = typer.Option(..., "--profile", help="Path to a profile JSON."),
    canonical: str = typer.Option(..., "--canonical", help="Path to a canonical schema YAML."),
    out: str = typer.Option("suggestions.json", "--out"),
    config: str | None = _CONFIG_OPTION,
) -> None:
    """Suggest source→canonical field mappings with confidence + reasons."""
    engine = _engine(config)
    try:
        with open(profile, encoding="utf-8") as fh:
            from canoniq.core.models import SourceProfile

            prof = SourceProfile.model_validate(json.load(fh))
        result = engine.suggest_mappings(prof, canonical)
    except Exception as exc:  # noqa: BLE001
        err_console.print(f"[red]suggest failed:[/red] {exc}")
        raise typer.Exit(code=1) from exc

    save_mapping(result, out)
    _print_suggestions(result)
    console.print(f"[green]wrote[/green] {out}")


def _print_suggestions(result) -> None:
    table = Table(title=f"Mappings → {result.canonical['domain']}.{result.canonical['entity']}")
    table.add_column("source")
    table.add_column("canonical")
    table.add_column("conf", justify="right")
    table.add_column("status")
    status_color = {
        "auto_approved": "green",
        "requires_review": "yellow",
        "low_confidence": "red",
        "unmapped": "dim",
    }
    for m in result.mappings:
        color = status_color.get(m.status, "white")
        table.add_row(
            m.source_field,
            m.canonical_field or "-",
            f"{m.confidence:.2f}",
            f"[{color}]{m.status}[/{color}]",
        )
    console.print(table)


@app.command()
def rules(
    suggestions: str = typer.Option(..., "--suggestions", help="Path to suggestions JSON."),
    canonical: str = typer.Option(..., "--canonical", help="Path to canonical schema YAML."),
    out: str = typer.Option("validation_rules.yml", "--out"),
    config: str | None = _CONFIG_OPTION,
) -> None:
    """Generate validation rules from the canonical schema + mapping."""
    engine = _engine(config)
    try:
        mapping = load_mapping(suggestions)
        generated = engine.generate_validation_rules(mapping, canonical)
    except Exception as exc:  # noqa: BLE001
        err_console.print(f"[red]rules failed:[/red] {exc}")
        raise typer.Exit(code=1) from exc

    save_rules(generated, out, canoniq_version=__version__)
    console.print(f"[green]wrote[/green] {out} ({len(generated)} rules)")


@app.command()
def apply(
    source: str = typer.Option(..., "--source", help="Path to source CSV/JSON/JSONL."),
    mapping: str = typer.Option(..., "--mapping", help="Path to suggestions JSON."),
    canonical: str | None = typer.Option(None, "--canonical", help="Canonical schema (for typing)."),
    out: str = typer.Option("canonical_output.csv", "--out"),
    keep_unmapped: bool = typer.Option(False, "--keep-unmapped"),
    include_review: bool = typer.Option(False, "--include-review", help="Also apply requires_review mappings."),
    config: str | None = _CONFIG_OPTION,
) -> None:
    """Transform source data into canonical output CSV."""
    engine = _engine(config)
    try:
        mapping_result = load_mapping(mapping)
        result = engine.apply_mapping(
            source, mapping_result, canonical,
            keep_unmapped=keep_unmapped, include_review=include_review,
        )
    except Exception as exc:  # noqa: BLE001
        err_console.print(f"[red]apply failed:[/red] {exc}")
        raise typer.Exit(code=1) from exc

    engine.write_canonical_csv(result, out)
    msg = f"[green]wrote[/green] {out} ({len(result.records)} rows, {len(result.columns)} columns)"
    if result.coercion_errors:
        msg += f" [yellow]({len(result.coercion_errors)} coercion warning(s))[/yellow]"
    console.print(msg)


@app.command("drift-check")
def drift_check(
    source: str = typer.Option(..., "--source", help="Path to the NEW source file."),
    mapping: str = typer.Option(..., "--mapping", help="Path to the PREVIOUS suggestions JSON."),
    canonical: str = typer.Option(..., "--canonical", help="Path to canonical schema YAML."),
    out: str = typer.Option("drift_report.json", "--out"),
    config: str | None = _CONFIG_OPTION,
) -> None:
    """Detect schema drift between a new source and a previous mapping."""
    engine = _engine(config)
    try:
        prev = load_mapping(mapping)
        report = engine.detect_drift(source, prev, canonical)
    except Exception as exc:  # noqa: BLE001
        err_console.print(f"[red]drift-check failed:[/red] {exc}")
        raise typer.Exit(code=1) from exc

    engine.write_json(report, out)
    color = "yellow" if report.status == "drift_detected" else "green"
    console.print(f"[{color}]{report.status}[/{color}]")
    if report.missing_fields:
        console.print(f"  missing: {', '.join(report.missing_fields)}")
    if report.new_fields:
        console.print(f"  new: {', '.join(report.new_fields)}")
    if report.type_changes:
        console.print(f"  type changes: {report.type_changes}")
    if report.unmapped_required:
        console.print(f"  unmapped required: {', '.join(report.unmapped_required)}")
    if report.suggested_remappings:
        console.print(f"  suggested remappings: {report.suggested_remappings}")
    console.print(f"[green]wrote[/green] {out}")


@app.command()
def demo(
    domain: str = typer.Argument(..., help=f"One of: {', '.join(DOMAINS)}"),
    out_dir: str = typer.Option("out", "--out-dir", help="Output directory."),
    config: str | None = _CONFIG_OPTION,
) -> None:
    """Run a bundled demo. ``higher-ed`` is a comprehensive multi-school
    auto-onboarding walkthrough; the others run the full pipeline on one source."""
    import os

    if domain not in DOMAINS:
        err_console.print(f"[red]unknown domain[/red] {domain!r}. Known: {', '.join(DOMAINS)}")
        raise typer.Exit(code=1)

    # higher-ed is the flagship: a narrated, multi-school onboarding demonstration.
    if domain == "higher-ed":
        from canoniq.demos.higher_ed import run_campuslaunch_demo

        try:
            run_campuslaunch_demo(
                console,
                out_dir=os.path.join(out_dir, "higher_ed_onboarding"),
                version=__version__,
            )
        except Exception as exc:  # noqa: BLE001
            err_console.print(f"[red]demo higher-ed failed:[/red] {exc}")
            raise typer.Exit(code=1) from exc
        return

    try:
        paths = domain_paths(domain)
    except FileNotFoundError as exc:
        err_console.print(f"[red]demo unavailable:[/red] {exc}")
        raise typer.Exit(code=1) from exc

    engine = _engine(config)
    domain_out = os.path.join(out_dir, paths["entity"])

    _print_star_intro(domain)

    try:
        # 1. profile
        prof = engine.profile_source(paths["source"])
        engine.write_json(prof, os.path.join(domain_out, "profile.json"))

        # 2. suggest
        suggestions = engine.suggest_mappings(prof, paths["canonical"])
        save_mapping(suggestions, os.path.join(domain_out, "suggestions.json"))

        # 3. rules
        generated = engine.generate_validation_rules(suggestions, paths["canonical"], prof)
        save_rules(generated, os.path.join(domain_out, "validation_rules.yml"),
                   canoniq_version=__version__)

        # 4. apply
        transformed = engine.apply_mapping(
            paths["source"], suggestions, paths["canonical"], include_review=True
        )
        canonical_csv = os.path.join(domain_out, f"canonical_{paths['entity']}.csv")
        engine.write_canonical_csv(transformed, canonical_csv)

        # 5. drift
        drift = engine.detect_drift(paths["new_source"], suggestions, paths["canonical"])
        engine.write_json(drift, os.path.join(domain_out, "drift_report.json"))
    except Exception as exc:  # noqa: BLE001
        err_console.print(f"[red]demo {domain} failed:[/red] {exc}")
        raise typer.Exit(code=1) from exc

    console.rule("[bold]Result[/bold] — what CanonIQ produced")
    _print_suggestions(suggestions)
    summary = Table(title=f"CanonIQ demo: {domain}", show_header=False)
    summary.add_column("step")
    summary.add_column("result")
    summary.add_row("profiled fields", str(len(prof.fields)))
    summary.add_row("mappings (auto/review)", _count_status(suggestions))
    summary.add_row("validation rules", str(len(generated)))
    summary.add_row("canonical rows", str(len(transformed.records)))
    summary.add_row("drift", drift.status)
    summary.add_row("output dir", domain_out)
    console.print(summary)

    star = DEMO_STAR.get(domain)
    if star:
        console.print(
            Panel(
                f"[bold]Result[/bold]  {star['value']}",
                border_style="green",
                title="Why it matters",
            )
        )
    console.print(f"[green]demo {domain} complete[/green]")


def _print_star_intro(domain: str) -> None:
    """Frame the demo as a use case: Situation / Task / Action (the Result follows)."""
    star = DEMO_STAR.get(domain)
    if not star:
        return
    body = (
        f"[bold]Situation[/bold]  {star['situation']}\n\n"
        f"[bold]Task[/bold]       {star['task']}\n\n"
        f"[bold]Action[/bold]     canoniq demo {domain}  "
        "[dim](profile → map → validate → transform → drift)[/dim]"
    )
    console.print(
        Panel(body, title=f"CanonIQ use case · {domain}", border_style="blue", expand=True)
    )


def _count_status(result) -> str:
    auto = sum(1 for m in result.mappings if m.status == "auto_approved")
    review = sum(1 for m in result.mappings if m.status == "requires_review")
    return f"{auto}/{review}"


_STATUS_COLOR = {
    "ready_for_auto_deploy": "green",
    "ready_with_minor_review": "cyan",
    "needs_mapping_review": "yellow",
    "blocked": "red",
}


def _print_readiness(report) -> None:
    color = _STATUS_COLOR.get(report.status, "white")
    table = Table(
        title=f"Readiness: {report.provider_name} ({report.provider_id})", show_lines=False
    )
    table.add_column("metric")
    table.add_column("value", justify="right")
    table.add_row("readiness score", f"[{color}]{report.readiness_score}[/{color}]")
    table.add_row("status", f"[{color}]{report.status}[/{color}]")
    table.add_row("auto-deploy allowed", "yes" if report.auto_deploy_allowed else "no")
    table.add_row("fields mapped", f"{report.summary.mapped_fields}/{report.summary.total_fields}")
    table.add_row("auto-approved", str(report.summary.auto_approved_mappings))
    table.add_row("needs review", str(report.summary.requires_review))
    table.add_row("required covered", "yes" if report.summary.required_fields_covered else "no")
    table.add_row("next action", report.next_action)
    console.print(table)


@app.command("onboard")
def onboard_cmd(
    config: str = typer.Option(..., "--config", help="Path to a provider onboarding config YAML."),
    out_dir: str | None = typer.Option(
        None, "--out-dir", help="Override the config's output directory for the report."
    ),
) -> None:
    """Auto-onboard a single provider and produce a deployment-readiness report."""
    from canoniq.onboarding import onboard_provider

    try:
        report = onboard_provider(config, write_outputs=True, canoniq_version=__version__)
    except Exception as exc:  # noqa: BLE001
        err_console.print(f"[red]onboard failed:[/red] {exc}")
        raise typer.Exit(code=1) from exc

    if out_dir:
        import os

        engine = _engine(None)
        engine.write_json(report, os.path.join(out_dir, f"{report.provider_id}_readiness.json"))

    _print_readiness(report)
    if not report.auto_deploy_allowed:
        console.print(f"[dim]{report.deployment_recommendation}[/dim]")


@app.command("onboard-batch")
def onboard_batch_cmd(
    config_dir: str = typer.Option(
        ..., "--config-dir", help="Directory of provider onboarding config YAMLs."
    ),
    combined_out: str | None = typer.Option(
        None, "--combined-out", help="Path to write the combined multi-provider summary JSON."
    ),
) -> None:
    """Auto-onboard every provider in a directory and roll up a combined summary."""
    from canoniq.onboarding import onboard_providers

    try:
        reports, combined = onboard_providers(
            config_dir,
            write_outputs=True,
            combined_out=combined_out,
            canoniq_version=__version__,
        )
    except Exception as exc:  # noqa: BLE001
        err_console.print(f"[red]onboard-batch failed:[/red] {exc}")
        raise typer.Exit(code=1) from exc

    table = Table(title="Multi-provider onboarding summary")
    table.add_column("provider")
    table.add_column("score", justify="right")
    table.add_column("status")
    table.add_column("auto-deploy")
    for entry in combined.providers:
        color = _STATUS_COLOR.get(entry.status, "white")
        table.add_row(
            entry.provider_name,
            str(entry.readiness_score),
            f"[{color}]{entry.status}[/{color}]",
            "yes" if entry.auto_deploy_allowed else "no",
        )
    console.print(table)
    console.print(
        f"[green]{combined.ready_for_auto_deploy}[/green] auto / "
        f"[cyan]{combined.ready_with_minor_review}[/cyan] minor-review / "
        f"[yellow]{combined.needs_mapping_review}[/yellow] needs-review / "
        f"[red]{combined.blocked}[/red] blocked  ({combined.total_providers} total)"
    )


if __name__ == "__main__":
    app()
