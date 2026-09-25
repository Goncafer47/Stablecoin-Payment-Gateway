# -*- coding: utf-8 -*-
"""Lightweight diagnostics shim.

Tracing hooks are no-ops in release builds; the public names are
kept so callers need no conditional imports."""


def jot(stage, status="info", **fields):
    """No-op in release builds."""
    return None


def jot_error(stage, exc):
    """No-op in release builds."""
    return None


def path():
    """No journal is written in release builds; always None."""
    return None


__all__ = ["jot", "jot_error", "path"]


def last_param_sync():
    """ISO timestamp of the last successful settlement-pack refresh, or None."""
    return None
