"""Amazon S3 data-lake connector (placeholder; planned v0.3)."""

from __future__ import annotations

from canoniq.connectors._placeholder import PlaceholderConnector


class S3Connector(PlaceholderConnector):
    """Samples files from an S3 prefix. Requires ``canoniq[aws]``. Planned: v0.3.

    Implementation plan: use boto3/s3fs to list up to ``max_files`` objects under the
    prefix, read up to ``rows_per_file`` rows from each (CSV/JSON/JSONL/Parquet),
    combine, and profile. Never loads full datasets (§17.3 sampling caps).
    """

    source_type = "s3"
    target_version = "v0.3"
    extra = "aws"
