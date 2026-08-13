"""Fixture import scaffolding for phased TDD implementation.

This module intentionally exposes stable API entrypoints before behavior is
implemented. The eventual importer is root-agnostic and treats incoming rows as
one graph, whether exported from one layer or multiple selected layers.
"""

from __future__ import annotations


def import_fixture_rows(
    rows,
    dry_run=False,
    associate_all_sites=True,
    missing_ref_policy="error",
    duplicate_uuid_policy="error",
):
    """Import fixture rows using UUID-first identity semantics.

    The engine is root-agnostic and processes a single graph composed from all
    rows in the fixture.

    Policy defaults are strict to keep behavior deterministic:
    - missing_ref_policy: "error" (unsupported: any other value)
    - duplicate_uuid_policy: "error" (unsupported: any other value)

    Planned coverage with shared graph engine:
    - PR05/PR06: layer import behavior
    - PR07: multilayer import behavior
    - PR09: theme import behavior
    """
    if missing_ref_policy != "error":
        raise ValueError("Unsupported missing_ref_policy: %s" % missing_ref_policy)
    if duplicate_uuid_policy != "error":
        raise ValueError("Unsupported duplicate_uuid_policy: %s" % duplicate_uuid_policy)

    raise NotImplementedError(
        "PR05 importer scaffold only: import_fixture_rows is not implemented yet"
    )


def import_layer_rows(
    rows,
    dry_run=False,
    associate_all_sites=True,
    missing_ref_policy="error",
    duplicate_uuid_policy="error",
):
    """Import only layers.layer fixture rows (UUID-first resolution)."""
    raise NotImplementedError(
        "Scaffold only: import_layer_rows is not implemented yet"
    )


def import_multilayer_rows(
    rows,
    dry_run=False,
    missing_ref_policy="error",
    duplicate_uuid_policy="error",
):
    """Import multilayer-related rows (dimensions, values, associations)."""
    raise NotImplementedError(
        "Scaffold only: import_multilayer_rows is not implemented yet"
    )


def import_theme_rows(
    rows,
    dry_run=False,
    associate_all_sites=True,
    missing_ref_policy="error",
    duplicate_uuid_policy="error",
):
    """Import theme-related rows and relations."""
    raise NotImplementedError(
        "Scaffold only: import_theme_rows is not implemented yet"
    )
