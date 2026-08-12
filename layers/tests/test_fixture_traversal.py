from django.test import SimpleTestCase

from layers.fixture_contract import (
    NODE_MODEL_KEY,
    NODE_SOURCE_PK_KEY,
    NODE_UUID_KEY,
    build_node,
    build_ref,
)
from layers.fixture_traversal import (
    TraversalLimitExceeded,
    mark_visited,
    node_identity_key,
    ref_identity_key,
    should_descend,
    stable_dedupe_nodes,
    stable_dedupe_refs,
    use_node_budget,
)


class FixtureTraversalTest(SimpleTestCase):
    def test_ref_identity_key_prefers_uuid_over_source_pk(self):
        """Does the traversal recognize two references are the same by UUID, 
        even if the source_pk is different?
        It should."""
        ref_one = build_ref(model="layers.layer", source_pk=1, uuid_value="abc")
        ref_two = build_ref(model="layers.layer", source_pk=999, uuid_value="abc")

        self.assertEqual(ref_identity_key(ref_one), ref_identity_key(ref_two))

    def test_ref_identity_key_falls_back_to_source_pk_when_uuid_missing(self):
        """If no UUID, records with different 'id' should be considered different."""
        ref_one = build_ref(model="layers.layer", source_pk=1, uuid_value=None)
        ref_two = build_ref(model="layers.layer", source_pk=2, uuid_value=None)

        self.assertNotEqual(ref_identity_key(ref_one), ref_identity_key(ref_two))

    def test_node_identity_key_prefers_uuid_over_source_pk(self):
        """Test that two nodes with the same UUID are considered the same, 
        even if their 'id' is different."""
        node_one = build_node("layers.layer", 11, "same-uuid", fields={}, relations={})
        node_two = build_node("layers.layer", 12, "same-uuid", fields={}, relations={})

        self.assertEqual(node_identity_key(node_one), node_identity_key(node_two))

    def test_stable_dedupe_refs_removes_duplicates_and_keeps_order(self):
        """Test that stable_dedupe_refs removes duplicates based on identity key and 
        preserves the order of first-seen references."""
        ref_a = build_ref(model="layers.lookupinfo", source_pk=10, uuid_value="u-a")
        ref_a_dupe = build_ref(model="layers.lookupinfo", source_pk=999, uuid_value="u-a")
        ref_b = build_ref(model="layers.lookupinfo", source_pk=11, uuid_value="u-b")

        deduped = stable_dedupe_refs([ref_a, ref_b, ref_a_dupe])

        self.assertEqual(deduped, [ref_a, ref_b])

    def test_stable_dedupe_nodes_removes_duplicates_and_keeps_order(self):
        """Test that stable_dedupe_nodes removes duplicates based on identity key and 
        preserves the order of first-seen nodes."""
        node_a = build_node("layers.layer", 10, "uuid-a", fields={"name": "A"}, relations={})
        node_a_dupe = build_node("layers.layer", 999, "uuid-a", fields={"name": "A2"}, relations={})
        node_b = build_node("layers.layer", 11, "uuid-b", fields={"name": "B"}, relations={})

        deduped = stable_dedupe_nodes([node_a, node_b, node_a_dupe])

        self.assertEqual(deduped, [node_a, node_b])

    def test_should_descend_honors_max_depth(self):
        """Test small helper that is simple as "is a <= b?" for traversal depth."""
        self.assertTrue(should_descend(depth=0, max_depth=None))
        self.assertTrue(should_descend(depth=1, max_depth=1))
        self.assertFalse(should_descend(depth=2, max_depth=1))

    def test_use_node_budget_raises_when_limit_exceeded(self):
        """Test that correct error is raised when traversal goes
        too deep"""
        count = 0
        count = use_node_budget(current_count=count, max_nodes=2)
        count = use_node_budget(current_count=count, max_nodes=2)

        with self.assertRaises(TraversalLimitExceeded):
            use_node_budget(current_count=count, max_nodes=2)

    def test_mark_visited_returns_false_for_repeat_identity(self):
        """Test that mark_visited returns True for first-seen identity key, 
        and False for repeats."""
        ref_obj = build_ref(model="layers.layer", source_pk=1, uuid_value="same")
        visited = set()

        self.assertTrue(mark_visited(visited, ref_identity_key(ref_obj)))
        self.assertFalse(mark_visited(visited, ref_identity_key(ref_obj)))

    def test_stable_dedupe_nodes_keeps_fixture_key_shape(self):
        """Ensure that `stable_dedupe_nodes` doesn't change the node content"""
        node = build_node("layers.layer", 1, "uuid-1", fields={"x": 1}, relations={})
        deduped = stable_dedupe_nodes([node])

        self.assertEqual(deduped[0][NODE_MODEL_KEY], "layers.layer")
        self.assertEqual(deduped[0][NODE_SOURCE_PK_KEY], 1)
        self.assertEqual(deduped[0][NODE_UUID_KEY], "uuid-1")
