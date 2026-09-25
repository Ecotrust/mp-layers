import uuid

from django.test import SimpleTestCase

from layers.models import AttributeInfo
from layers.serializers import AttributeInfoExportSerializer


class AttributeInfoExportSerializerTest(SimpleTestCase):
    def test_represents_attribute_info_with_expected_fields(self):
        attribute_info = AttributeInfo(
            uuid=uuid.UUID("12345678-1234-5678-1234-567812345678"),
            display_name="Record Name",
            field_name="FIELD",
            field_label="Field Label",
            precision=2,
            order=3,
            preserve_format=True,
        )

        result = AttributeInfoExportSerializer(attribute_info).data

        self.assertEqual(result, {
            "uuid": "12345678-1234-5678-1234-567812345678",
            "display_name": "Record Name",
            "field_name": "FIELD",
            "field_label": "Field Label",
            "precision": 2,
            "order": 3,
            "preserve_format": True,
        })
