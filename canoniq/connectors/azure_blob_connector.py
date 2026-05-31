"""Azure Blob Storage data-lake connector (placeholder; planned v0.3)."""

from __future__ import annotations

from canoniq.connectors._placeholder import PlaceholderConnector


class AzureBlobConnector(PlaceholderConnector):
    """Samples blobs from an Azure container prefix. Requires ``canoniq[azure]``. Planned: v0.3.

    Implementation plan: use ``azure-storage-blob`` to list up to ``max_files`` blobs
    under the prefix, read up to ``rows_per_file`` rows each, combine, and profile.
    Honors §17.3 sampling caps.
    """

    source_type = "azure_blob"
    target_version = "v0.3"
    extra = "azure"
