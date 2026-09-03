import json
from unittest.mock import patch
from uuid import uuid4

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse

from layers.fixture_contract import build_node
from layers.models import Layer


class LayerFixtureImportAdminTest(TestCase):
    """PR07.01 contract tests for the Layer fixture import admin workflow."""

    upload_url_name = "admin:layers_layer_import_fixture"

    def setUp(self):
        self.upload_url = reverse(self.upload_url_name)
        self.superuser = get_user_model().objects.create_superuser(
            username="fixture-admin",
            email="fixture-admin@example.com",
            password="password",
        )
        self.valid_rows = [
            build_node(
                model="layers.layer",
                source_pk=1001,
                uuid_value=uuid4(),
                fields={
                    "name": "Uploaded Fixture Layer",
                    "layer_type": "WMS",
                    "slug_name": None,
                    "url": None,
                },
                relations={},
            )
        ]

    def _fixture_file(self, rows=None, name="layers.json"):
        return SimpleUploadedFile(
            name,
            json.dumps(rows if rows is not None else self.valid_rows).encode("utf-8"),
            content_type="application/json",
        )

    def test_upload_view_requires_layer_change_permission(self):
        response = self.client.get(self.upload_url)
        self.assertEqual(response.status_code, 302)

        user = get_user_model().objects.create_user(
            username="no-layer-permission",
            password="password",
            is_staff=True,
        )
        self.client.force_login(user)
        response = self.client.get(self.upload_url)
        self.assertEqual(response.status_code, 403)

    @patch("layers.admin.import_fixture_rows")
    def test_valid_upload_runs_dry_run_and_shows_confirmation(self, import_fixture_rows):
        self.client.force_login(self.superuser)
        import_fixture_rows.return_value = {"imported": 1, "dry_run": True}

        response = self.client.post(
            self.upload_url,
            {"fixture_file": self._fixture_file()},
        )

        self.assertEqual(response.status_code, 200)
        import_fixture_rows.assert_called_once_with(
            self.valid_rows,
            dry_run=True,
            associate_all_sites=True,
            missing_ref_policy="error",
            duplicate_uuid_policy="error",
        )
        self.assertContains(response, "Uploaded Fixture Layer")
        self.assertContains(response, "Confirm")
        self.assertEqual(Layer.all_objects.count(), 0)

    @patch("layers.admin.import_fixture_rows")
    def test_preview_reports_uuid_matched_updates_and_changed_field_values(
        self,
        import_fixture_rows,
    ):
        self.client.force_login(self.superuser)
        existing_layer = Layer.all_objects.create(
            name="Current Layer Name",
            layer_type="WMS",
            url="https://current.example.test/wms",
        )
        fixture_rows = [
            build_node(
                model="layers.layer",
                source_pk=1001,
                uuid_value=existing_layer.uuid,
                fields={
                    "name": "Imported Layer Name",
                    "layer_type": "WMS",
                    "slug_name": None,
                    "url": "https://imported.example.test/wms",
                },
                relations={},
            )
        ]
        import_fixture_rows.return_value = {"imported": 1, "dry_run": True}

        response = self.client.post(
            self.upload_url,
            {"fixture_file": self._fixture_file(fixture_rows)},
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Update existing record")
        self.assertContains(response, "name")
        self.assertContains(response, "Current Layer Name")
        self.assertContains(response, "Imported Layer Name")
        self.assertContains(response, "url")
        self.assertContains(response, "https://current.example.test/wms")
        self.assertContains(response, "https://imported.example.test/wms")

    @patch("layers.admin.import_fixture_rows")
    def test_invalid_json_displays_error_without_import(self, import_fixture_rows):
        self.client.force_login(self.superuser)
        invalid_file = SimpleUploadedFile(
            "broken.json",
            b"{not valid json",
            content_type="application/json",
        )

        response = self.client.post(self.upload_url, {"fixture_file": invalid_file})

        self.assertEqual(response.status_code, 200)
        import_fixture_rows.assert_not_called()
        self.assertContains(response, "valid JSON")
        self.assertEqual(Layer.all_objects.count(), 0)

    @patch("layers.admin.import_fixture_rows")
    def test_confirmation_executes_staged_fixture_not_posted_payload(self, import_fixture_rows):
        self.client.force_login(self.superuser)
        import_fixture_rows.return_value = {"imported": 1, "dry_run": True}

        preview_response = self.client.post(
            self.upload_url,
            {"fixture_file": self._fixture_file()},
        )
        self.assertEqual(preview_response.status_code, 200)

        import_fixture_rows.reset_mock()
        import_fixture_rows.return_value = {"imported": 1, "dry_run": False}
        tampered_rows = [
            build_node(
                model="layers.layer",
                source_pk=9999,
                uuid_value=uuid4(),
                fields={
                    "name": "Tampered Layer",
                    "layer_type": "WMS",
                    "slug_name": None,
                    "url": None,
                },
                relations={},
            )
        ]

        response = self.client.post(
            self.upload_url,
            {"confirm": "1", "fixture_file": self._fixture_file(tampered_rows)},
        )

        self.assertEqual(response.status_code, 302)
        import_fixture_rows.assert_called_once_with(
            self.valid_rows,
            dry_run=False,
            associate_all_sites=True,
            missing_ref_policy="error",
            duplicate_uuid_policy="error",
        )

    @patch("layers.admin.import_fixture_rows")
    def test_cancel_discards_staged_fixture_without_import(self, import_fixture_rows):
        self.client.force_login(self.superuser)
        import_fixture_rows.return_value = {"imported": 1, "dry_run": True}

        self.client.post(self.upload_url, {"fixture_file": self._fixture_file()})
        import_fixture_rows.reset_mock()

        response = self.client.post(self.upload_url, {"cancel": "1"})

        self.assertRedirects(response, reverse("admin:layers_layer_changelist"))
        import_fixture_rows.assert_not_called()
        self.assertEqual(Layer.all_objects.count(), 0)