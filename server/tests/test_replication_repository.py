from database_fixtures import new_in_memory_database
from models import RecordKind, ReplicatedRecord
from repositories import ReplicationRepository

LOGIN_CONTENT = {"username": "bot-1", "logged_in_at_ms": 1_000}
RECORD_LOGICAL_CLOCK = 7


def login_record(origin_server: str, origin_sequence: int) -> ReplicatedRecord:
    return ReplicatedRecord(origin_server, origin_sequence, RecordKind.LOGIN, RECORD_LOGICAL_CLOCK, LOGIN_CONTENT)


def repository_with_records(*records: ReplicatedRecord) -> ReplicationRepository:
    replication_repository = ReplicationRepository(new_in_memory_database())
    for record in records:
        replication_repository.add_if_new(record)
    return replication_repository


def test_sequence_of_an_origin_starts_at_one_and_follows_its_records():
    replication_repository = repository_with_records(login_record("server-1", 1), login_record("server-1", 2))

    assert replication_repository.next_sequence_of("server-2") == 1
    assert replication_repository.next_sequence_of("server-1") == 3


def test_same_record_is_kept_only_once():
    replication_repository = repository_with_records(login_record("server-1", 1))

    stored_again = replication_repository.add_if_new(login_record("server-1", 1))

    assert stored_again is False
    assert replication_repository.records_after({}) == [login_record("server-1", 1)]


def test_watermark_is_the_last_sequence_without_a_gap_before_it():
    replication_repository = repository_with_records(
        login_record("server-1", 1),
        login_record("server-1", 2),
        login_record("server-1", 4),
        login_record("server-2", 2),
        login_record("server-3", 1),
    )

    assert replication_repository.contiguous_watermarks() == {"server-1": 2, "server-2": 0, "server-3": 1}


def test_records_after_the_watermarks_include_unknown_origins_and_records_beyond_a_gap():
    replication_repository = repository_with_records(
        login_record("server-1", 1),
        login_record("server-1", 2),
        login_record("server-1", 4),
        login_record("server-2", 1),
    )

    records = replication_repository.records_after({"server-1": 1})

    assert records == [login_record("server-1", 2), login_record("server-1", 4), login_record("server-2", 1)]


def test_records_after_the_watermarks_are_limited_per_exchange():
    replication_repository = repository_with_records(*(login_record("server-1", sequence) for sequence in range(1, 6)))

    records = replication_repository.records_after({}, limit=2)

    assert records == [login_record("server-1", 1), login_record("server-1", 2)]
