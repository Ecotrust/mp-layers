import json
from unittest.mock import Mock, patch
from uuid import uuid4

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse

from layers.fixture_contract import build_node
from layers.admin import export_theme_details
from layers.models import ChildOrder, Layer, Theme


class ThemeFixtureImportAdminTest(TestCase):
    """Contract tests for the Theme fixture import admin workflow."""

    upload_url_name = "admin:layers_theme_import_fixture"

    def setUp(self):
        self.upload_url = reverse(self.upload_url_name)
        self.superuser = get_user_model().objects.create_superuser(
            username="theme-fixture-admin",
            email="theme-fixture-admin@example.com",
            password="password",
        )
        self.theme_uuid = uuid4()
        self.valid_rows = [
            build_node(
                model="layers.theme",
                source_pk=1001,
                uuid_value=self.theme_uuid,
                fields={
                    "name": "Uploaded Fixture Theme",
                    "display_name": "Uploaded Fixture Theme",
                    "theme_type": "checkbox",
                    "order": 10,
                    "is_visible": True,
                    "is_top_theme": False,
                },
                relations={},
            )
        ]

    def _fixture_file(self, rows=None, name="themes.json"):
        return SimpleUploadedFile(
            name,
            json.dumps(rows if rows is not None else self.valid_rows).encode("utf-8"),
            content_type="application/json",
        )

    def test_upload_view_requires_theme_change_permission(self):
        response = self.client.get(self.upload_url)
        self.assertEqual(response.status_code, 302)

        user = get_user_model().objects.create_user(
            username="no-theme-permission",
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
        self.assertContains(response, "Uploaded Fixture Theme")
        self.assertContains(response, "Confirm")
        self.assertEqual(Theme.all_objects.count(), 0)

    @patch("layers.admin.import_fixture_rows")
    def test_exported_theme_fixture_preview_has_no_field_differences(self, import_fixture_rows):
        self.client.force_login(self.superuser)
        theme = Theme.all_objects.create(
            name="Preview Theme",
            display_name="Preview Theme",
        )
        layer = Layer.all_objects.create(name="Preview Layer", layer_type="WMS")
        ChildOrder.objects.create(
            parent_theme=theme,
            content_object=layer,
            order=4,
        )

        export_response = export_theme_details(
            Mock(),
            Mock(),
            Theme.all_objects.filter(pk=theme.pk),
        )
        fixture_file = SimpleUploadedFile(
            "exported-theme.json",
            export_response.content,
            content_type="application/json",
        )
        import_fixture_rows.return_value = {"imported": 0, "dry_run": True}

        response = self.client.post(
            self.upload_url,
            {"fixture_file": fixture_file},
        )

        self.assertEqual(response.status_code, 200)
        import_fixture_rows.assert_called_once()
        self.assertTrue(response.context["preview_rows"])
        self.assertTrue(all(not row["changes"] for row in response.context["preview_rows"]))
        self.assertContains(response, "Create or merge relationship record")

    @patch("layers.admin.import_fixture_rows")
    def test_preview_reports_uuid_matched_theme_updates(self, import_fixture_rows):
        self.client.force_login(self.superuser)
        existing_theme = Theme.all_objects.create(
            name="Current Theme Name",
            display_name="Current Theme Name",
            uuid=self.theme_uuid,
        )
        fixture_rows = [
            build_node(
                model="layers.theme",
                source_pk=1001,
                uuid_value=existing_theme.uuid,
                fields={
                    "name": "Imported Theme Name",
                    "display_name": "Imported Theme Name",
                    "theme_type": "checkbox",
                    "order": 10,
                    "is_visible": True,
                    "is_top_theme": False,
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
        self.assertContains(response, "Current Theme Name")
        self.assertContains(response, "Imported Theme Name")

    @patch("layers.admin.import_fixture_rows")
    def test_source_id_collision_does_not_change_uuid_first_import_policy(self, import_fixture_rows):
        self.client.force_login(self.superuser)
        Theme.all_objects.create(
            name="Existing Theme",
            display_name="Existing Theme",
            uuid=uuid4(),
            id=1001,
        )
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
                model="layers.theme",
                source_pk=9999,
                uuid_value=uuid4(),
                fields={
                    "name": "Tampered Theme",
                    "display_name": "Tampered Theme",
                    "theme_type": "checkbox",
                    "order": 10,
                    "is_visible": True,
                    "is_top_theme": False,
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

        self.assertRedirects(response, reverse("admin:layers_theme_changelist"))
        import_fixture_rows.assert_not_called()
        self.assertEqual(Theme.all_objects.count(), 0)

    @patch("layers.admin.import_fixture_rows")
    def test_confirm_without_preview_does_not_write(self, import_fixture_rows):
        self.client.force_login(self.superuser)

        response = self.client.post(self.upload_url, {"confirm": "1"})

        self.assertEqual(response.status_code, 200)
        import_fixture_rows.assert_not_called()
        self.assertContains(response, "No validated fixture")
        self.assertEqual(Theme.all_objects.count(), 0)

    @patch("layers.admin.import_fixture_rows")
    def test_invalid_json_does_not_write(self, import_fixture_rows):
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
        self.assertEqual(Theme.all_objects.count(), 0)
