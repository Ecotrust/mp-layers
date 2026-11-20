import uuid
from datetime import date, datetime

from django.contrib.auth import get_user_model
from django.contrib.sites.models import Site
from django.core.cache import cache
from django.test import RequestFactory, TestCase, override_settings
from django.urls import reverse

from layers.admin import LayerAdmin
from layers.models import AttributeInfo, Layer
from layers.views import get_layer_details


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


@override_settings(
    SITE_ID=1,
    CACHES={
        "default": {
            "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
            "LOCATION": "attribute-info-admin-tests",
        }
    },
)
# This test was primarily written by Copilot
class AttributeInfoAdminCacheTest(TestCase):
    '''
    Test case for verifying that the cache is properly cleared when a LayerInline is removed from an AttributeInfo instance.
    '''
    def test_removing_layer_inline_deletes_layer_details_cache(self):
        user = get_user_model().objects.create_superuser(
            username="attribute-admin",
            email="attribute-admin@example.com",
            password="test-password",
        )
        self.client.force_login(user)
        site = Site.objects.get(pk=1)
        layer = Layer.objects.create(name="Attribute layer", layer_type="WMS")
        layer.site.add(site)
        attribute = AttributeInfo.objects.create(
            display_name="Depth",
            field_name="depth",
            field_label="Depth (m)",
        )
        layer.attribute_fields.add(attribute)
        relationship = Layer.attribute_fields.through.objects.get(
            layer=layer, attributeinfo=attribute
        )
        cache_key = "layers_layer_serialized_details_{}_{}".format(layer.pk, site.pk)
        self.addCleanup(cache.delete, cache_key)

        request = RequestFactory().get("/")
        response = get_layer_details(request, layer.pk)
        self.assertEqual(response.status_code, 200)
        cached_details = cache.get(cache_key)
        self.assertIsNotNone(cached_details)
        self.assertEqual(
            [item["field"] for item in cached_details["attributes"]["attributes"]],
            [attribute.field_name],
        )

        change_url = reverse("admin:layers_attributeinfo_change", args=[attribute.pk])
        response = self.client.get(change_url)
        self.assertEqual(response.status_code, 200)
        formset = response.context["inline_admin_formsets"][0].formset
        prefix = formset.prefix
        response = self.client.post(
            change_url,
            {
                "display_name": attribute.display_name,
                "field_name": attribute.field_name,
                "field_label": attribute.field_label,
                "order": attribute.order,
                "precision": "",
                "{}-TOTAL_FORMS".format(prefix): "1",
                "{}-INITIAL_FORMS".format(prefix): "1",
                "{}-MIN_NUM_FORMS".format(prefix): "0",
                "{}-MAX_NUM_FORMS".format(prefix): "1000",
                "{}-0-id".format(prefix): relationship.pk,
                "{}-0-attributeinfo".format(prefix): attribute.pk,
                "{}-0-layer".format(prefix): layer.pk,
                "{}-0-DELETE".format(prefix): "on",
                "_save": "Save",
            },
        )

        self.assertEqual(response.status_code, 302)
        self.assertFalse(layer.attribute_fields.filter(pk=attribute.pk).exists())
        self.assertTrue(Layer.objects.filter(pk=layer.pk).exists())
        self.assertTrue(AttributeInfo.objects.filter(pk=attribute.pk).exists())
        self.assertIsNone(cache.get(cache_key))

        response = get_layer_details(request, layer.pk)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(cache.get(cache_key)["attributes"]["attributes"], [])
