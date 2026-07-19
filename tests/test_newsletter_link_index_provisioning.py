import importlib.util
import sys
from copy import deepcopy
from pathlib import Path

import pytest

from backend.scripts import provision_newsletter_link_indexes as provisioning


def exact_metadata(definition):
    metadata = {
        "v": 2,
        "name": definition.name,
        "key": list(definition.keys),
    }
    if definition.unique:
        metadata["unique"] = True
    if definition.expire_after_seconds is not None:
        metadata["expireAfterSeconds"] = definition.expire_after_seconds
    return metadata


class FakeRepository:
    def __init__(self, indexes=None):
        self.indexes = indexes or {
            provisioning.CHALLENGE_COLLECTION: [],
            provisioning.RATE_LIMIT_COLLECTION: [],
        }
        self.create_calls = []
        self.discover_calls = []
        self.fail_create_at = None
        self.fail_discovery_at = None
        self.post_create_mutator = None

    def discover(self, collection_name):
        self.discover_calls.append(collection_name)
        if (
            self.fail_discovery_at is not None
            and len(self.discover_calls) == self.fail_discovery_at
        ):
            raise provisioning.DatabaseOperationError(
                "Index discovery failed safely."
            )
        return tuple(deepcopy(self.indexes[collection_name]))

    def create(self, definition):
        self.create_calls.append(definition)
        if (
            self.fail_create_at is not None
            and len(self.create_calls) == self.fail_create_at
        ):
            raise provisioning.DatabaseOperationError(
                "Index creation failed safely."
            )
        metadata = exact_metadata(definition)
        if self.post_create_mutator is not None:
            metadata = self.post_create_mutator(definition, metadata)
        self.indexes[definition.collection_name].append(metadata)


class FakeCollection:
    def __init__(self, indexes=()):
        self.indexes = list(indexes)
        self.create_calls = []
        self.document_calls = []

    def list_indexes(self):
        return tuple(deepcopy(self.indexes))

    def create_index(self, keys, **options):
        self.create_calls.append((keys, options))

    def insert_one(self, *args, **kwargs):
        self.document_calls.append(("insert", args, kwargs))

    def update_one(self, *args, **kwargs):
        self.document_calls.append(("update", args, kwargs))

    def delete_one(self, *args, **kwargs):
        self.document_calls.append(("delete", args, kwargs))


class FakeDatabase:
    def __init__(self):
        self.requested = []
        self.collections = {
            provisioning.CHALLENGE_COLLECTION: FakeCollection(),
            provisioning.RATE_LIMIT_COLLECTION: FakeCollection(),
        }

    def __getitem__(self, name):
        self.requested.append(name)
        return self.collections[name]


def all_exact_indexes():
    indexes = {
        provisioning.CHALLENGE_COLLECTION: [],
        provisioning.RATE_LIMIT_COLLECTION: [],
    }
    for definition in provisioning.INDEX_DEFINITIONS:
        indexes[definition.collection_name].append(exact_metadata(definition))
    return indexes


def replace_definition(definition, mutator):
    indexes = all_exact_indexes()
    collection_indexes = indexes[definition.collection_name]
    position = next(
        index
        for index, metadata in enumerate(collection_indexes)
        if metadata["name"] == definition.name
    )
    replacement = deepcopy(collection_indexes[position])
    mutator(replacement)
    collection_indexes[position] = replacement
    return indexes


def test_import_isolation_performs_no_work(monkeypatch):
    source_path = Path(provisioning.__file__)
    source = source_path.read_text()
    assert "backend.server" not in source
    assert "create_repository_from_environment()" not in source.split(
        'if __name__ == "__main__":'
    )[0]

    import pymongo

    def fail_client(*args, **kwargs):
        raise AssertionError("Mongo client created during import")

    monkeypatch.setattr(pymongo, "MongoClient", fail_client)
    spec = importlib.util.spec_from_file_location(
        "isolated_newsletter_link_index_provisioning",
        source_path,
    )
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    monkeypatch.setitem(sys.modules, spec.name, module)
    spec.loader.exec_module(module)


def test_cli_requires_exactly_one_mode():
    parser = provisioning.build_parser()
    with pytest.raises(SystemExit):
        parser.parse_args([])
    with pytest.raises(SystemExit):
        parser.parse_args(["--dry-run", "--apply"])
    assert parser.parse_args(["--dry-run"]).dry_run is True
    assert parser.parse_args(["--apply"]).apply is True


def test_cli_has_no_force_or_bypass_option():
    option_strings = {
        option
        for action in provisioning.build_parser()._actions
        for option in action.option_strings
    }
    assert option_strings == {"-h", "--help", "--dry-run", "--apply"}


def test_apply_rejects_noninteractive_input_before_discovery():
    repository = FakeRepository()
    with pytest.raises(provisioning.ConfirmationError):
        provisioning.execute_apply(
            repository,
            input_func=lambda _prompt: provisioning.CONFIRMATION_TEXT,
            stdin_isatty=lambda: False,
        )
    assert repository.discover_calls == []
    assert repository.create_calls == []


@pytest.mark.parametrize(
    "confirmation",
    ("", "apply newsletter link indexes", "APPLY NEWSLETTER LINK INDEX"),
)
def test_apply_rejects_any_nonexact_confirmation(confirmation):
    repository = FakeRepository()
    with pytest.raises(provisioning.ConfirmationError):
        provisioning.execute_apply(
            repository,
            input_func=lambda _prompt: confirmation,
            stdin_isatty=lambda: True,
        )
    assert repository.discover_calls == []
    assert repository.create_calls == []


def test_dry_run_reports_all_missing_and_performs_zero_writes():
    repository = FakeRepository()
    result = provisioning.execute_dry_run(repository)
    assert result.public_dict() == {
        "mode": "dry-run",
        "target_indexes": 4,
        "exact_existing": 0,
        "missing": 4,
        "conflicting": 0,
        "created": 0,
        "verified_exact": 0,
        "status": "inspected",
    }
    assert repository.create_calls == []


def test_dry_run_accepts_all_exact_existing_indexes():
    repository = FakeRepository(all_exact_indexes())
    result = provisioning.execute_dry_run(repository)
    assert result.exact_existing == 4
    assert result.missing == 0
    assert result.conflicting == 0
    assert result.created == 0


def test_dry_run_reports_conflicts_without_writing():
    definition = provisioning.INDEX_DEFINITIONS[0]
    repository = FakeRepository(
        replace_definition(
            definition,
            lambda metadata: metadata.update(unique=False),
        )
    )
    result = provisioning.execute_dry_run(repository)
    assert result.conflicting == 1
    assert result.status == "conflicts_found"
    assert repository.create_calls == []


@pytest.mark.parametrize(
    ("label", "mutator"),
    (
        ("wrong keys", lambda metadata: metadata.update(key=[("other", 1)])),
        ("wrong direction", lambda metadata: metadata.update(key=[("token_hash", -1)])),
        ("wrong uniqueness", lambda metadata: metadata.update(unique=False)),
        ("sparse", lambda metadata: metadata.update(sparse=True)),
        (
            "partial",
            lambda metadata: metadata.update(
                partialFilterExpression={"token_hash": {"$exists": True}}
            ),
        ),
        ("hidden", lambda metadata: metadata.update(hidden=True)),
        ("collation", lambda metadata: metadata.update(collation={"locale": "en"})),
        ("unknown option", lambda metadata: metadata.update(wildcardProjection={})),
    ),
)
def test_semantic_conflicts_block_apply_before_creation(label, mutator):
    definition = provisioning.INDEX_DEFINITIONS[0]
    repository = FakeRepository(replace_definition(definition, mutator))
    with pytest.raises(provisioning.IndexConflictError):
        provisioning.execute_apply(
            repository,
            input_func=lambda _prompt: provisioning.CONFIRMATION_TEXT,
            stdin_isatty=lambda: True,
        )
    assert repository.create_calls == []


def test_wrong_name_with_exact_keys_is_a_conflict():
    definition = provisioning.INDEX_DEFINITIONS[0]
    indexes = all_exact_indexes()
    metadata = next(
        item
        for item in indexes[definition.collection_name]
        if item["name"] == definition.name
    )
    metadata["name"] = "wrong_name"
    assessment = provisioning.assess_indexes(FakeRepository(indexes))
    assert assessment.conflicting == 1
    assert assessment.missing == 0


def test_wrong_key_order_is_a_conflict():
    definition = provisioning.INDEX_DEFINITIONS[2]
    indexes = replace_definition(
        definition,
        lambda metadata: metadata.update(key=list(reversed(metadata["key"]))),
    )
    assert provisioning.assess_indexes(FakeRepository(indexes)).conflicting == 1


@pytest.mark.parametrize("value", ("true", "false", 1, 0, None, [], {}))
def test_malformed_unique_values_are_rejected(value):
    definition = provisioning.INDEX_DEFINITIONS[0]
    metadata = exact_metadata(definition)
    metadata["unique"] = value
    with pytest.raises(provisioning.IndexConflictError):
        provisioning.validate_exact_index(metadata, definition)


@pytest.mark.parametrize("value", ("false", 0, None, [], {}))
def test_malformed_nonunique_values_are_rejected(value):
    definition = provisioning.INDEX_DEFINITIONS[1]
    metadata = exact_metadata(definition)
    metadata["unique"] = value
    with pytest.raises(provisioning.IndexConflictError):
        provisioning.validate_exact_index(metadata, definition)


@pytest.mark.parametrize(
    "direction",
    (True, False, "1", "-1", 0, 2, -2, 1.0, None, [], {}),
)
def test_malformed_key_directions_are_rejected(direction):
    definition = provisioning.INDEX_DEFINITIONS[0]
    metadata = exact_metadata(definition)
    metadata["key"] = [("token_hash", direction)]
    with pytest.raises(provisioning.IndexConflictError):
        provisioning.validate_exact_index(metadata, definition)


@pytest.mark.parametrize("value", (True, False, "0", None, 0.0, [], {}))
def test_malformed_ttl_values_are_rejected(value):
    definition = provisioning.INDEX_DEFINITIONS[1]
    metadata = exact_metadata(definition)
    metadata["expireAfterSeconds"] = value
    with pytest.raises(provisioning.IndexConflictError):
        provisioning.validate_exact_index(metadata, definition)


def test_wrong_integer_ttl_is_rejected():
    definition = provisioning.INDEX_DEFINITIONS[1]
    metadata = exact_metadata(definition)
    metadata["expireAfterSeconds"] = 1
    with pytest.raises(provisioning.IndexConflictError):
        provisioning.validate_exact_index(metadata, definition)


@pytest.mark.parametrize("option", ("sparse", "hidden"))
@pytest.mark.parametrize("value", ("false", 0, None, [], {}))
def test_malformed_false_boolean_options_are_rejected(option, value):
    definition = provisioning.INDEX_DEFINITIONS[1]
    metadata = exact_metadata(definition)
    metadata[option] = value
    with pytest.raises(provisioning.IndexConflictError):
        provisioning.validate_exact_index(metadata, definition)


def test_apply_creates_only_missing_indexes_and_verifies_each_one():
    repository = FakeRepository()
    result = provisioning.execute_apply(
        repository,
        input_func=lambda _prompt: provisioning.CONFIRMATION_TEXT,
        stdin_isatty=lambda: True,
    )
    assert repository.create_calls == list(provisioning.INDEX_DEFINITIONS)
    assert result.created == 4
    assert result.verified_exact == 4
    assert result.status == "verified"
    assert len(repository.discover_calls) == 12


def test_apply_never_recreates_exact_existing_indexes():
    repository = FakeRepository(all_exact_indexes())
    result = provisioning.execute_apply(
        repository,
        input_func=lambda _prompt: provisioning.CONFIRMATION_TEXT,
        stdin_isatty=lambda: True,
    )
    assert result.created == 0
    assert result.verified_exact == 4
    assert repository.create_calls == []


def test_apply_is_idempotent_on_rerun():
    repository = FakeRepository()
    first = provisioning.execute_apply(
        repository,
        input_func=lambda _prompt: provisioning.CONFIRMATION_TEXT,
        stdin_isatty=lambda: True,
    )
    second = provisioning.execute_apply(
        repository,
        input_func=lambda _prompt: provisioning.CONFIRMATION_TEXT,
        stdin_isatty=lambda: True,
    )
    assert first.created == 4
    assert second.created == 0
    assert len(repository.create_calls) == 4


def test_partial_creation_failure_stops_immediately():
    repository = FakeRepository()
    repository.fail_create_at = 2
    with pytest.raises(provisioning.DatabaseOperationError):
        provisioning.execute_apply(
            repository,
            input_func=lambda _prompt: provisioning.CONFIRMATION_TEXT,
            stdin_isatty=lambda: True,
        )
    assert len(repository.create_calls) == 2


def test_rediscovery_failure_stops_after_creation():
    repository = FakeRepository()
    repository.fail_discovery_at = 3
    with pytest.raises(provisioning.DatabaseOperationError):
        provisioning.execute_apply(
            repository,
            input_func=lambda _prompt: provisioning.CONFIRMATION_TEXT,
            stdin_isatty=lambda: True,
        )
    assert len(repository.create_calls) == 1


def test_post_create_mismatch_stops_before_later_indexes():
    repository = FakeRepository()

    def change_created_index(definition, metadata):
        metadata["sparse"] = True
        return metadata

    repository.post_create_mutator = change_created_index
    with pytest.raises(provisioning.VerificationError):
        provisioning.execute_apply(
            repository,
            input_func=lambda _prompt: provisioning.CONFIRMATION_TEXT,
            stdin_isatty=lambda: True,
        )
    assert len(repository.create_calls) == 1


def test_repository_creates_exact_definitions_without_document_mutation():
    database = FakeDatabase()
    repository = provisioning.NewsletterLinkIndexRepository(database)
    for definition in provisioning.INDEX_DEFINITIONS:
        repository.create(definition)

    assert database.requested == [
        provisioning.CHALLENGE_COLLECTION,
        provisioning.RATE_LIMIT_COLLECTION,
    ]
    challenge_calls = database.collections[
        provisioning.CHALLENGE_COLLECTION
    ].create_calls
    rate_calls = database.collections[
        provisioning.RATE_LIMIT_COLLECTION
    ].create_calls
    assert challenge_calls == [
        (
            [("token_hash", 1)],
            {
                "name": "newsletter_link_challenge_token_hash_unique",
                "unique": True,
                "sparse": False,
            },
        ),
        (
            [("expires_at", 1)],
            {
                "name": "newsletter_link_challenge_ttl",
                "unique": False,
                "sparse": False,
                "expireAfterSeconds": 0,
            },
        ),
    ]
    assert rate_calls == [
        (
            [("dimension", 1), ("hash", 1), ("operation", 1)],
            {
                "name": "newsletter_link_request_limit_unique",
                "unique": True,
                "sparse": False,
            },
        ),
        (
            [("expires_at", 1)],
            {
                "name": "newsletter_link_request_limit_ttl",
                "unique": False,
                "sparse": False,
                "expireAfterSeconds": 0,
            },
        ),
    ]
    assert all(
        collection.document_calls == []
        for collection in database.collections.values()
    )


def test_main_dry_run_output_is_aggregate_only(capsys):
    sensitive_values = (
        "mongodb+srv://private",
        "private_database",
        "reader@example.com",
        "private-token",
        "private-hash",
        "203.0.113.10",
    )
    repository = FakeRepository()
    result = provisioning.main(
        ["--dry-run"],
        repository_factory=lambda: repository,
    )
    output = capsys.readouterr()
    assert result == 0
    assert output.err == ""
    payload = output.out
    assert '"target_indexes": 4' in payload
    assert all(value not in payload for value in sensitive_values)


def test_main_sanitises_database_errors(capsys):
    private_detail = (
        "mongodb+srv://user:password@private/private_database "
        "reader@example.com private-token private-hash 203.0.113.10"
    )

    def fail_repository():
        raise RuntimeError(private_detail)

    result = provisioning.main(
        ["--dry-run"],
        repository_factory=fail_repository,
    )
    output = capsys.readouterr()
    assert result == 1
    assert "unexpected error" in output.err
    assert private_detail not in output.err
    assert "mongodb+srv" not in output.err


def test_runtime_and_startup_do_not_import_or_execute_script():
    root = Path(__file__).resolve().parents[1]
    script_name = "provision_newsletter_link_indexes"
    for relative in (
        "backend/server.py",
        "backend/app/email_service.py",
        "backend/scheduler/tasks.py",
        "backend/scripts/migrate_newsletter_management_ids.py",
    ):
        assert script_name not in (root / relative).read_text()
