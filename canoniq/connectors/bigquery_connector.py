"""BigQuery source connector (placeholder; planned v0.3)."""

from __future__ import annotations

from canoniq.connectors._placeholder import PlaceholderConnector


class BigQueryConnector(PlaceholderConnector):
    """Samples rows from a BigQuery table. Requires ``canoniq[bigquery]``. Planned: v0.3.

    Implementation plan: use ``google-cloud-bigquery`` with ADC or a service-account
    file; ``sample`` runs a ``SELECT * FROM `project.dataset.table` LIMIT <n>`` query;
    ``get_metadata`` reads the table schema (field names, types, modes, descriptions).
    """

    source_type = "bigquery"
    target_version = "v0.3"
    extra = "bigquery"
