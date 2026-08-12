"""Traversal and dedupe helpers for fixture export graph construction.

PR02 introduces this module. Implementations are added in follow-up steps.
"""


class TraversalLimitExceeded(Exception):
    """Raised when traversal exceeds configured safety limits."""


def ref_identity_key(ref_obj):
    """Return a stable identity key for a fixture relation reference."""
    raise NotImplementedError()


def node_identity_key(node_obj):
    """Return a stable identity key for a fixture node row."""
    raise NotImplementedError()


def stable_dedupe_refs(refs):
    """Return refs with duplicates removed while preserving first-seen order."""
    raise NotImplementedError()


def stable_dedupe_nodes(nodes):
    """Return nodes with duplicates removed while preserving first-seen order."""
    raise NotImplementedError()


def should_descend(depth, max_depth):
    """Return True when traversal should continue at the current depth."""
    raise NotImplementedError()


def use_node_budget(current_count, max_nodes):
    """Consume one node from traversal budget and return the new count."""
    raise NotImplementedError()


def mark_visited(visited, identity_key):
    """Track visited identities; return True only for first-seen keys."""
    raise NotImplementedError()
