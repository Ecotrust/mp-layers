from uuid import UUID


FIXTURE_SCHEMA_VERSION = "layer-export-v2"

NODE_MODEL_KEY = "model"
NODE_SOURCE_PK_KEY = "source_pk"
NODE_UUID_KEY = "uuid"
NODE_FIELDS_KEY = "fields"
NODE_RELATIONS_KEY = "relations"


def normalize_uuid(value):
    """Normalize UUID-like inputs to a canonical string-or-None value.

    Use this whenever fixture code accepts mixed UUID sources
    (UUID objects, strings, blank strings, or None).

    Example:
        normalize_uuid(UUID('12345678-1234-5678-1234-567812345678'))
        -> '12345678-1234-5678-1234-567812345678'
    """
    if value is None:
        return None
    if isinstance(value, UUID):
        return str(value)

    normalized = str(value).strip()
    if normalized == "":
        return None
    return normalized


def build_ref(instance=None, model=None, source_pk=None, uuid_value=None):
    """Build a canonical relationship reference object.

    References are lightweight pointers used under relation fields
    (for example, Layer -> AttributeInfo or Vector -> LookupInfo).

    Example using an instance:
        build_ref(instance=attribute_info)

    Example using explicit values:
        build_ref(model='layers.layer', source_pk=10, uuid_value='...')
    """
    if instance is not None:
        model = instance._meta.label_lower
        source_pk = instance.pk
        uuid_value = getattr(instance, "uuid", None)

    ref_obj = {
        NODE_MODEL_KEY: model,
        NODE_SOURCE_PK_KEY: source_pk,
        NODE_UUID_KEY: normalize_uuid(uuid_value),
    }
    validate_ref_shape(ref_obj)
    return ref_obj


def build_node(model, source_pk, uuid_value, fields=None, relations=None):
    """Build a canonical fixture node for one exported object.

    Nodes are the top-level rows in the fixture and include the identity
    metadata plus serialized fields and relationship refs.

    Example:
        build_node('layers.layer', 55, 'uuid-str', {'name': 'Layer A'}, {'attribute_fields': []})
    """
    node_obj = {
        NODE_MODEL_KEY: model,
        NODE_SOURCE_PK_KEY: source_pk,
        NODE_UUID_KEY: normalize_uuid(uuid_value),
        NODE_FIELDS_KEY: fields or {},
        NODE_RELATIONS_KEY: relations or {},
    }
    validate_node_shape(node_obj)
    return node_obj


def validate_ref_shape(ref_obj):
    """Validate that a reference object matches the expected contract.

    Call this when ingesting untrusted fixture data or before writing refs
    to ensure stable structure for downstream import logic.

    Example:
        validate_ref_shape({'model': 'layers.layer', 'source_pk': 1, 'uuid': '...'})
    """
    required_keys = {
        NODE_MODEL_KEY,
        NODE_SOURCE_PK_KEY,
        NODE_UUID_KEY,
    }
    missing_keys = required_keys - set(ref_obj.keys())
    if missing_keys:
        raise ValueError("Invalid ref: missing keys {}".format(sorted(missing_keys)))

    model = ref_obj[NODE_MODEL_KEY]
    source_pk = ref_obj[NODE_SOURCE_PK_KEY]
    uuid_value = ref_obj[NODE_UUID_KEY]

    if not isinstance(model, str) or model.strip() == "":
        raise ValueError("Invalid ref: 'model' must be a non-empty string")

    if source_pk is not None and not isinstance(source_pk, int):
        raise ValueError("Invalid ref: 'source_pk' must be an int or None")

    if uuid_value is not None and not isinstance(uuid_value, str):
        raise ValueError("Invalid ref: 'uuid' must be a string or None")


def validate_node_shape(node_obj):
    """Validate that a fixture node has required keys and value types.

    This protects export and import code from malformed rows by ensuring
    identity, fields, and relations all exist with expected types.

    Example:
        validate_node_shape({'model': 'layers.layer', 'source_pk': 1, 'uuid': '...', 'fields': {}, 'relations': {}})
    """
    required_keys = {
        NODE_MODEL_KEY,
        NODE_SOURCE_PK_KEY,
        NODE_UUID_KEY,
        NODE_FIELDS_KEY,
        NODE_RELATIONS_KEY,
    }
    missing_keys = required_keys - set(node_obj.keys())
    if missing_keys:
        raise ValueError("Invalid node: missing keys {}".format(sorted(missing_keys)))

    validate_ref_shape({
        NODE_MODEL_KEY: node_obj[NODE_MODEL_KEY],
        NODE_SOURCE_PK_KEY: node_obj[NODE_SOURCE_PK_KEY],
        NODE_UUID_KEY: node_obj[NODE_UUID_KEY],
    })

    if not isinstance(node_obj[NODE_FIELDS_KEY], dict):
        raise ValueError("Invalid node: 'fields' must be an object")

    if not isinstance(node_obj[NODE_RELATIONS_KEY], dict):
        raise ValueError("Invalid node: 'relations' must be an object")


def ref_sort_key(ref_obj):
    """Return a deterministic sorting key for reference objects.

    Use this for stable export ordering so identical data emits identical
    fixture output across runs.

    Example:
        sorted(refs, key=ref_sort_key)
    """
    validate_ref_shape(ref_obj)
    return (
        ref_obj[NODE_MODEL_KEY],
        ref_obj[NODE_SOURCE_PK_KEY] if ref_obj[NODE_SOURCE_PK_KEY] is not None else -1,
        ref_obj[NODE_UUID_KEY] if ref_obj[NODE_UUID_KEY] is not None else "",
    )


def node_sort_key(node_obj):
    """Return a deterministic sorting key for fixture node objects.

    Use this when producing normalized fixture output or comparing fixtures
    in tests where ordering should be repeatable.

    Example:
        sorted(nodes, key=node_sort_key)
    """
    validate_node_shape(node_obj)
    return (
        node_obj[NODE_MODEL_KEY],
        node_obj[NODE_SOURCE_PK_KEY] if node_obj[NODE_SOURCE_PK_KEY] is not None else -1,
        node_obj[NODE_UUID_KEY] if node_obj[NODE_UUID_KEY] is not None else "",
    )
