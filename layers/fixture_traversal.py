"""Traversal and dedupe helpers for fixture export graph construction.

PR02 introduces this module. Implementations are added in follow-up steps.
"""

from layers.fixture_contract import (
    NODE_MODEL_KEY,
    NODE_SOURCE_PK_KEY,
    NODE_UUID_KEY,
    normalize_uuid,
    validate_node_shape,
    validate_ref_shape,
)


class TraversalLimitExceeded(Exception):
    """Raised when traversal exceeds configured safety limits."""


def ref_identity_key(ref_obj):
    """Return a stable identity key for a fixture relation reference."""
    validate_ref_shape(ref_obj)

    uuid_value = normalize_uuid(ref_obj.get(NODE_UUID_KEY))
    if uuid_value is not None:
        return (ref_obj[NODE_MODEL_KEY], "uuid", uuid_value)

    return (ref_obj[NODE_MODEL_KEY], "source_pk", ref_obj.get(NODE_SOURCE_PK_KEY))


def node_identity_key(node_obj):
    """Return a stable identity key for a fixture node row."""
    validate_node_shape(node_obj)

    uuid_value = normalize_uuid(node_obj.get(NODE_UUID_KEY))
    if uuid_value is not None:
        return (node_obj[NODE_MODEL_KEY], "uuid", uuid_value)

    return (node_obj[NODE_MODEL_KEY], "source_pk", node_obj.get(NODE_SOURCE_PK_KEY))


def stable_dedupe_refs(refs):
    """Return refs with duplicates removed while preserving first-seen order."""
    deduped = []
    seen = set()
    for ref_obj in refs:
        key = ref_identity_key(ref_obj)
        if key in seen:
            continue
        seen.add(key)
        deduped.append(ref_obj)
    return deduped


def stable_dedupe_nodes(nodes):
    """Return nodes with duplicates removed while preserving first-seen order."""
    deduped = []
    seen = set()
    for node_obj in nodes:
        key = node_identity_key(node_obj)
        if key in seen:
            continue
        seen.add(key)
        deduped.append(node_obj)
    return deduped


def should_descend(depth, max_depth):
    """Return True when traversal should continue at the current depth."""
    if max_depth is None:
        return True
    return depth <= max_depth


def use_node_budget(current_count, max_nodes):
    """Consume one node from traversal budget and return the new count."""
    next_count = current_count + 1
    if max_nodes is not None and next_count > max_nodes:
        raise TraversalLimitExceeded(
            "Traversal node limit exceeded: {} > {}".format(next_count, max_nodes)
        )
    return next_count


def mark_visited(visited, identity_key):
    """Track visited identities; return True only for first-seen keys."""
    if identity_key in visited:
        return False
    visited.add(identity_key)
    return True
