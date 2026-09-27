import uuid
from datetime import date, datetime

from django.test import TestCase

from layers.admin import LayerAdmin
from layers.models import Layer


class LayerAdminValuesMatchTest(TestCase):
    """Unit tests for LayerAdmin.values_match used by the fixture import preview."""

    def setUp(self):
        self.admin = LayerAdmin(Layer, None)

    def test_new_value_none_returns_false(self):
        self.assertFalse(self.admin.values_match(datetime(2020, 1, 1), None))

    def test_datetime_match_returns_true(self):
        current = datetime(2020, 1, 1, 12, 30, 0)
        self.assertTrue(self.admin.values_match(current, current.isoformat()))

    def test_datetime_mismatch_returns_false(self):
        current = datetime(2020, 1, 1, 12, 30, 0)
        other = datetime(2021, 6, 15, 8, 0, 0)
        self.assertFalse(self.admin.values_match(current, other.isoformat()))

    def test_date_match_returns_true(self):
        current = date(2020, 1, 1)
        self.assertTrue(self.admin.values_match(current, current.isoformat()))

    def test_uuid_match_returns_true(self):
        current = uuid.uuid4()
        self.assertTrue(self.admin.values_match(current, str(current)))

    def test_uuid_mismatch_returns_false(self):
        current = uuid.uuid4()
        other = uuid.uuid4()
        self.assertFalse(self.admin.values_match(current, str(other)))

    def test_stringified_uuid_matches_uuid_string_representation(self):
        current = uuid.uuid4()
        self.assertTrue(self.admin.values_match(current, str(uuid.UUID(str(current)))))

    def test_int_match_returns_true(self):
        self.assertTrue(self.admin.values_match(5, 5))

    def test_int_mismatch_returns_false(self):
        self.assertFalse(self.admin.values_match(5, 6))

    def test_float_match_returns_true(self):
        self.assertTrue(self.admin.values_match(1.5, 1.5))

    def test_float_mismatch_returns_false(self):
        self.assertFalse(self.admin.values_match(1.5, 2.5))

    def test_str_match_returns_true(self):
        self.assertTrue(self.admin.values_match("hello", "hello"))

    def test_str_mismatch_returns_false(self):
        self.assertFalse(self.admin.values_match("hello", "world"))
