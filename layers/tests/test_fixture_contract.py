from uuid import uuid4

from django.test import SimpleTestCase

from layers.fixture_contract import (
    build_node,
    build_ref,
    node_sort_key,
    normalize_uuid,
    ref_sort_key,
    validate_node_shape,
    validate_ref_shape,
)


class _Meta(object):
    label_lower = "layers.layer"


class _InstanceWithUUID(object):
    _meta = _Meta()

    def __init__(self):
        self.pk = 42
        self.uuid = uuid4()


class _InstanceWithoutUUID(object):
    _meta = _Meta()

    def __init__(self):
        self.pk = 84


class FixtureContractTest(SimpleTestCase):
    def test_normalize_uuid_returns_none_for_none(self):
        self.assertIsNone(normalize_uuid(None))

    def test_normalize_uuid_stringifies_uuid_instance(self):
        value = uuid4()
        self.assertEqual(normalize_uuid(value), str(value))

    def test_build_ref_from_instance_with_uuid(self):
        instance = _InstanceWithUUID()
        ref_obj = build_ref(instance=instance)

        self.assertEqual(ref_obj["model"], "layers.layer")
        self.assertEqual(ref_obj["source_pk"], 42)
        self.assertEqual(ref_obj["uuid"], str(instance.uuid))

    def test_build_ref_from_instance_without_uuid(self):
        instance = _InstanceWithoutUUID()
        ref_obj = build_ref(instance=instance)

        self.assertEqual(ref_obj["model"], "layers.layer")
        self.assertEqual(ref_obj["source_pk"], 84)
        self.assertIsNone(ref_obj["uuid"])

    def test_build_node_defaults_fields_and_relations_to_empty_objects(self):
        node_obj = build_node("layers.layer", 1, None)

        self.assertEqual(node_obj["fields"], {})
        self.assertEqual(node_obj["relations"], {})

    def test_validate_ref_shape_accepts_valid_ref(self):
        validate_ref_shape({
            "model": "layers.layer",
            "source_pk": 1,
            "uuid": str(uuid4()),
        })

    def test_validate_ref_shape_rejects_missing_model(self):
        with self.assertRaises(ValueError):
            validate_ref_shape({
                "source_pk": 1,
                "uuid": str(uuid4()),
            })

    def test_validate_node_shape_accepts_valid_node(self):
        validate_node_shape({
            "model": "layers.layer",
            "source_pk": 1,
            "uuid": str(uuid4()),
            "fields": {"name": "Layer"},
            "relations": {},
        })

    def test_validate_node_shape_rejects_missing_relations(self):
        with self.assertRaises(ValueError):
            validate_node_shape({
                "model": "layers.layer",
                "source_pk": 1,
                "uuid": str(uuid4()),
                "fields": {},
            })

    def test_ref_sort_key_is_stable(self):
        ref_one = {"model": "layers.lookupinfo", "source_pk": 2, "uuid": "b"}
        ref_two = {"model": "layers.lookupinfo", "source_pk": 1, "uuid": "a"}

        sorted_refs = sorted([ref_one, ref_two], key=ref_sort_key)

        self.assertEqual(sorted_refs, [ref_two, ref_one])

    def test_node_sort_key_is_stable(self):
        node_one = {
            "model": "layers.layer",
            "source_pk": 2,
            "uuid": "b",
            "fields": {},
            "relations": {},
        }
        node_two = {
            "model": "layers.layer",
            "source_pk": 1,
            "uuid": "a",
            "fields": {},
            "relations": {},
        }

        sorted_nodes = sorted([node_one, node_two], key=node_sort_key)

        self.assertEqual(sorted_nodes, [node_two, node_one])
