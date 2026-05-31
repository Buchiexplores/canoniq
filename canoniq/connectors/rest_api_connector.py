"""Generic REST API source connector (placeholder; planned v0.4)."""

from __future__ import annotations

from canoniq.connectors._placeholder import PlaceholderConnector


class RestAPIConnector(PlaceholderConnector):
    """Samples records from a paginated REST/GraphQL endpoint. Planned: v0.4.

    Implementation plan: issue authenticated requests (auth via ``${ENV}`` tokens),
    follow pagination until ``limit`` records are gathered, and extract the record list
    via a configurable JSON path. Respects rate limits and never persists credentials.
    """

    source_type = "rest_api"
    target_version = "v0.4"
    extra = None
