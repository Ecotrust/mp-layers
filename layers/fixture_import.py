"""Fixture import scaffolding for phased TDD implementation.

This module intentionally exposes stable API entrypoints before behavior is
implemented. The eventual importer is root-agnostic and treats incoming rows as
one graph, whether exported from one layer or multiple selected layers.
"""

from __future__ import annotations

from django.apps import apps
from django.contrib.sites.models import Site
from django.db import transaction

from .fixture_contract import (
    NODE_FIELDS_KEY,
    NODE_MODEL_KEY,
    NODE_RELATIONS_KEY,
    NODE_UUID_KEY,
    normalize_uuid,
)


LAYER_MODEL = "layers.layer"
MULTILAYER_ASSOCIATION_MODEL = "layers.multilayerassociation"
ATTRIBUTE_INFO_MODEL = "layers.attributeinfo"
LOOKUP_INFO_MODEL = "layers.lookupinfo"
COMPANIONSHIP_MODEL = "layers.companionship"
SPECIFIC_LAYER_MODELS = {
    "layers.layerwms",
    "layers.layerarcrest",
    "layers.layerxyz",
    "layers.layerarcfeatureservice",
    "layers.layervector",
}


def _model_manager(model_class):
    """Return an unscoped manager for import-time identity resolution."""
    if hasattr(model_class, "all_objects"):
        return model_class.all_objects
    return model_class._base_manager


def _assert_strict_policies(missing_ref_policy, duplicate_uuid_policy):
    if missing_ref_policy != "error":
        raise ValueError("Unsupported missing_ref_policy: %s" % missing_ref_policy)
    if duplicate_uuid_policy != "error":
        raise ValueError("Unsupported duplicate_uuid_policy: %s" % duplicate_uuid_policy)


def _row_identity_key(row):
    model_label = row.get(NODE_MODEL_KEY)
    uuid_value = normalize_uuid(row.get(NODE_UUID_KEY))
    return (model_label, uuid_value)


def _assert_no_duplicate_uuid_conflicts(rows):
    seen = {}
    for row in rows:
        model_label, uuid_value = _row_identity_key(row)
        if uuid_value is None:
            continue

        key = (model_label, uuid_value)
        signature = {
            NODE_FIELDS_KEY: row.get(NODE_FIELDS_KEY, {}),
            NODE_RELATIONS_KEY: row.get(NODE_RELATIONS_KEY, {}),
        }
        previous = seen.get(key)
        if previous is None:
            seen[key] = signature
            continue

        if previous != signature:
            raise ValueError(
                "Conflicting duplicate UUID rows for %s (%s)" % (model_label, uuid_value)
            )


def _apply_fields(instance, fields):
    for field_name, field_value in fields.items():
        if hasattr(instance, field_name):
            setattr(instance, field_name, field_value)


def _resolve_ref_instance(ref_obj, missing_ref_policy):
    ref_model_label = ref_obj.get(NODE_MODEL_KEY)
    ref_uuid_value = normalize_uuid(ref_obj.get(NODE_UUID_KEY))
    if not ref_uuid_value:
        if missing_ref_policy == "error":
            raise ValueError("Missing UUID in relation ref for model %s" % ref_model_label)
        return None

    model_class = apps.get_model(ref_model_label)
    manager = _model_manager(model_class)
    try:
        return manager.get(uuid=ref_uuid_value)
    except model_class.DoesNotExist:
        if missing_ref_policy == "error":
            raise ValueError(
                "Missing related object for %s UUID %s" % (ref_model_label, ref_uuid_value)
            )
        return None


def _resolve_ref_list(ref_list, missing_ref_policy):
    resolved = []
    for ref_obj in ref_list or []:
        resolved.append(_resolve_ref_instance(ref_obj, missing_ref_policy))
    return resolved


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
    _assert_strict_policies(missing_ref_policy, duplicate_uuid_policy)
    rows = rows or []
    _assert_no_duplicate_uuid_conflicts(rows)

    Layer = apps.get_model(LAYER_MODEL)
    MultilayerAssociation = apps.get_model(MULTILAYER_ASSOCIATION_MODEL)
    layer_manager = _model_manager(Layer)
    association_manager = _model_manager(MultilayerAssociation)

    def _execute_import():
        # First pass: upsert UUID-keyed rows that do not require relation remaps.
        for row in rows:
            model_label = row.get(NODE_MODEL_KEY)
            if model_label not in {LAYER_MODEL, ATTRIBUTE_INFO_MODEL, LOOKUP_INFO_MODEL}:
                continue

            row_uuid = normalize_uuid(row.get(NODE_UUID_KEY))
            if not row_uuid:
                raise ValueError("%s row missing UUID" % model_label)

            model_class = apps.get_model(model_label)
            model_manager = _model_manager(model_class)
            row_fields = dict(row.get(NODE_FIELDS_KEY, {}))
            row_obj = model_manager.filter(uuid=row_uuid).first()
            is_new = row_obj is None
            if is_new:
                row_obj = model_class(uuid=row_uuid)

            _apply_fields(row_obj, row_fields)
            row_obj.save()

            if model_label == LAYER_MODEL and associate_all_sites:
                row_obj.site.set(Site.objects.all())

        # Second pass: resolve layer m2m attribute refs by UUID.
        for row in rows:
            if row.get(NODE_MODEL_KEY) != LAYER_MODEL:
                continue

            layer_uuid = normalize_uuid(row.get(NODE_UUID_KEY))
            layer_obj = layer_manager.filter(uuid=layer_uuid).first()
            if layer_obj is None:
                raise ValueError("Missing layer object for UUID %s" % layer_uuid)

            relations = row.get(NODE_RELATIONS_KEY, {})
            if "attribute_fields" in relations:
                resolved_attributes = _resolve_ref_list(
                    relations.get("attribute_fields") or [],
                    missing_ref_policy,
                )
                layer_obj.attribute_fields.set(resolved_attributes)

        # Second pass: upsert multilayer associations and resolve FKs by UUID refs.
        for row in rows:
            if row.get(NODE_MODEL_KEY) != MULTILAYER_ASSOCIATION_MODEL:
                continue

            assoc_uuid = normalize_uuid(row.get(NODE_UUID_KEY))
            if not assoc_uuid:
                raise ValueError("MultilayerAssociation row missing UUID")

            relations = row.get(NODE_RELATIONS_KEY, {})
            parent_ref = relations.get("parentLayer")
            layer_ref = relations.get("layer")

            if not parent_ref:
                raise ValueError("Missing parentLayer relation for MultilayerAssociation")

            parent_layer_obj = _resolve_ref_instance(parent_ref, missing_ref_policy)
            layer_obj = None
            if layer_ref is not None:
                layer_obj = _resolve_ref_instance(layer_ref, missing_ref_policy)

            assoc_obj = association_manager.filter(uuid=assoc_uuid).first()
            if assoc_obj is None:
                assoc_obj = MultilayerAssociation(uuid=assoc_uuid)

            _apply_fields(assoc_obj, row.get(NODE_FIELDS_KEY, {}))
            assoc_obj.parentLayer = parent_layer_obj
            assoc_obj.layer = layer_obj
            assoc_obj.save()

        # Second pass: companionship relation rows (non-UUID identity).
        for row in rows:
            if row.get(NODE_MODEL_KEY) != COMPANIONSHIP_MODEL:
                continue

            relations = row.get(NODE_RELATIONS_KEY, {})
            owner_ref = relations.get("layer")
            if not owner_ref:
                raise ValueError("Missing layer relation for Companionship")

            owner_layer = _resolve_ref_instance(owner_ref, missing_ref_policy)
            companion_layers = _resolve_ref_list(
                relations.get("companions") or [],
                missing_ref_policy,
            )

            Companionship = apps.get_model(COMPANIONSHIP_MODEL)
            companionship = Companionship.objects.filter(layer=owner_layer).first()
            if companionship is None:
                companionship = Companionship(layer=owner_layer)
                companionship.save()

            companionship.companions.set(companion_layers)

        # Second pass: specific layer subtype rows keyed by resolved base layer relation.
        for row in rows:
            model_label = row.get(NODE_MODEL_KEY)
            if model_label not in SPECIFIC_LAYER_MODELS:
                continue

            relations = row.get(NODE_RELATIONS_KEY, {})
            layer_ref = relations.get("layer")
            if not layer_ref:
                raise ValueError("Missing layer relation for %s" % model_label)

            layer_obj = _resolve_ref_instance(layer_ref, missing_ref_policy)
            model_class = apps.get_model(model_label)

            specific_obj = model_class.objects.filter(layer=layer_obj).first()
            if specific_obj is None:
                specific_obj = model_class(layer=layer_obj)

            _apply_fields(specific_obj, row.get(NODE_FIELDS_KEY, {}))
            specific_obj.save()

            if "lookup_table" in relations and hasattr(specific_obj, "lookup_table"):
                resolved_lookup_refs = _resolve_ref_list(
                    relations.get("lookup_table") or [],
                    missing_ref_policy,
                )
                specific_obj.lookup_table.set(resolved_lookup_refs)

    if dry_run:
        with transaction.atomic():
            _execute_import()
            transaction.set_rollback(True)
            return {
                "imported": 0,
                "dry_run": True,
            }

    _execute_import()
    return {
        "imported": len(rows),
        "dry_run": False,
    }


def import_layer_rows(
    rows,
    dry_run=False,
    associate_all_sites=True,
    missing_ref_policy="error",
    duplicate_uuid_policy="error",
):
    """Import only layers.layer fixture rows (UUID-first resolution)."""
    layer_rows = [row for row in (rows or []) if row.get(NODE_MODEL_KEY) == LAYER_MODEL]
    return import_fixture_rows(
        layer_rows,
        dry_run=dry_run,
        associate_all_sites=associate_all_sites,
        missing_ref_policy=missing_ref_policy,
        duplicate_uuid_policy=duplicate_uuid_policy,
    )


def import_multilayer_rows(
    rows,
    dry_run=False,
    missing_ref_policy="error",
    duplicate_uuid_policy="error",
):
    """Import multilayer-related rows (dimensions, values, associations)."""
    multilayer_rows = [
        row
        for row in (rows or [])
        if row.get(NODE_MODEL_KEY) in {LAYER_MODEL, MULTILAYER_ASSOCIATION_MODEL}
    ]
    return import_fixture_rows(
        multilayer_rows,
        dry_run=dry_run,
        associate_all_sites=True,
        missing_ref_policy=missing_ref_policy,
        duplicate_uuid_policy=duplicate_uuid_policy,
    )


def import_theme_rows(
    rows,
    dry_run=False,
    associate_all_sites=True,
    missing_ref_policy="error",
    duplicate_uuid_policy="error",
):
    """Import theme-related rows and relations."""
    return import_fixture_rows(
        rows,
        dry_run=dry_run,
        associate_all_sites=associate_all_sites,
        missing_ref_policy=missing_ref_policy,
        duplicate_uuid_policy=duplicate_uuid_policy,
    )
