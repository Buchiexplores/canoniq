"""Google Cloud Storage data-lake connector (placeholder; planned v0.3)."""

from __future__ import annotations

from canoniq.connectors._placeholder import PlaceholderConnector


class GCSConnector(PlaceholderConnector):
    """Samples files from a GCS prefix. Requires ``canoniq[gcp]``. Planned: v0.3.

    Implementation plan: use ``google-cloud-storage`` to list up to ``max_files`` blobs
    under the prefix, read up to ``rows_per_file`` rows each, combine, and profile.
    Honors the §17.3 sampling caps; never loads full datasets.
    """

    source_type = "gcs"
    target_version = "v0.3"
    extra = "gcp"
