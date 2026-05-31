"""Shared pytest fixtures and a hard network-isolation guard (§28).

CanonIQ is local-first; tests must make ZERO external network calls. We block
``socket.socket`` for the whole test session so any accidental network access fails
loudly instead of reaching out.
"""

from __future__ import annotations

import os
import socket

import pytest

_REAL_SOCKET = socket.socket


class _NoNetworkSocket(socket.socket):
    def __init__(self, *args, **kwargs):  # noqa: D401
        raise RuntimeError(
            "Network access is disabled during tests (CanonIQ is local-first)."
        )


@pytest.fixture(autouse=True, scope="session")
def _block_network():
    socket.socket = _NoNetworkSocket  # type: ignore[misc,assignment]
    try:
        yield
    finally:
        socket.socket = _REAL_SOCKET  # type: ignore[misc,assignment]


@pytest.fixture(scope="session")
def repo_root() -> str:
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


@pytest.fixture(scope="session")
def examples_dir(repo_root: str) -> str:
    return os.path.join(repo_root, "examples")
