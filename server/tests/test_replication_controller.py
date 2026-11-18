from database_fixtures import new_in_memory_database
from controllers import ReplicationController
from errors import PeerUnavailable
from fakes import success_response
from models import Channel, Login, RecordKind, ReplicatedRecord
from repositories import ChannelRepository, LoginRepository, PublicationRepository, ReplicationRepository

OWN_NAME = "server-2"
COORDINATOR_NAME = "server-3"
RECORD_LOGICAL_CLOCK = 5


def login_record(origin_server: str, origin_sequence: int, username: str) -> ReplicatedRecord:
    return ReplicatedRecord(
        origin_server,
        origin_sequence,
        RecordKind.LOGIN,
        RECORD_LOGICAL_CLOCK,
        {"username": username, "logged_in_at_ms": 1_000},
    )


def channel_record(origin_server: str, origin_sequence: int, name: str, logical_clock: int) -> ReplicatedRecord:
    return ReplicatedRecord(
        origin_server,
        origin_sequence,
        RecordKind.CHANNEL,
        logical_clock,
        {
            "name": name,
            "created_by_username": f"creator-on-{origin_server}",
            "created_at_ms": 1_000,
            "created_logical_clock": logical_clock,
            "created_on_server": origin_server,
        },
    )


class RecordingReplicationPeer:
    def __init__(self, records_from_coordinator: list[ReplicatedRecord], coordinator_watermarks: dict) -> None:
        self.records_from_coordinator = records_from_coordinator
        self.coordinator_watermarks = coordinator_watermarks
        self.watermarks_sent: list[dict] = []
        self.pushed_records: list[ReplicatedRecord] = []

    def request_replication_sync(self, peer_name: str, watermarks: dict) -> dict:
        self.watermarks_sent.append(watermarks)
        return success_response(
            {
                "records": [record.as_fields() for record in self.records_from_coordinator],
                "watermarks": self.coordinator_watermarks,
            }
        )

    def push_records(self, peer_name: str, records: list[ReplicatedRecord]) -> dict:
        self.pushed_records.extend(records)
        return success_response({})


class UnavailablePeer:
    def request_replication_sync(self, peer_name: str, watermarks: dict) -> dict:
        raise PeerUnavailable(peer_name)


class ReplicationScenario:
    def __init__(self, peer_connector) -> None:
        self.database_connection = new_in_memory_database()
        self.replication_repository = ReplicationRepository(self.database_connection)
        self.login_repository = LoginRepository(self.database_connection)
        self.channel_repository = ChannelRepository(self.database_connection)
        self.controller = ReplicationController(
            OWN_NAME,
            self.database_connection,
            self.replication_repository,
            self.login_repository,
            self.channel_repository,
            PublicationRepository(self.database_connection),
            peer_connector,
        )

    def logged_usernames(self) -> list[str]:
        rows = self.database_connection.execute("SELECT username FROM login ORDER BY id").fetchall()
        return [username for (username,) in rows]


def test_remote_record_is_applied_once_even_when_it_arrives_twice():
    scenario = ReplicationScenario(RecordingReplicationPeer([], {}))

    scenario.controller.apply_remote_record(login_record("server-1", 1, "bot-1"))
    scenario.controller.apply_remote_record(login_record("server-1", 1, "bot-1"))

    assert scenario.logged_usernames() == ["bot-1"]


def test_channel_created_on_two_servers_keeps_the_creation_with_the_smaller_logical_clock():
    scenario = ReplicationScenario(RecordingReplicationPeer([], {}))

    scenario.controller.apply_remote_record(channel_record("server-1", 1, "news", logical_clock=20))
    scenario.controller.apply_remote_record(channel_record("server-3", 1, "news", logical_clock=10))
    scenario.controller.apply_remote_record(channel_record("server-4", 1, "news", logical_clock=30))

    stored_channel = scenario.channel_repository.channel_named("news")
    assert stored_channel.created_on_server == "server-3"
    assert scenario.channel_repository.all_names() == ["news"]


def test_synchronization_sends_own_watermarks_and_applies_what_the_coordinator_had():
    peer = RecordingReplicationPeer([login_record("server-1", 1, "bot-from-server-1")], {"server-1": 1})
    scenario = ReplicationScenario(peer)
    scenario.controller.apply_remote_record(login_record("server-4", 1, "bot-from-server-4"))

    scenario.controller.synchronize_with_coordinator(COORDINATOR_NAME)

    assert peer.watermarks_sent == [{"server-4": 1}]
    assert scenario.logged_usernames() == ["bot-from-server-4", "bot-from-server-1"]


def test_synchronization_pushes_the_records_the_coordinator_lacks():
    peer = RecordingReplicationPeer([], {"server-4": 1})
    scenario = ReplicationScenario(peer)
    scenario.controller.apply_remote_record(login_record("server-4", 1, "bot-a"))
    scenario.controller.apply_remote_record(login_record("server-4", 2, "bot-b"))
    scenario.controller.apply_remote_record(login_record("server-5", 1, "bot-c"))

    scenario.controller.synchronize_with_coordinator(COORDINATOR_NAME)

    assert peer.pushed_records == [login_record("server-4", 2, "bot-b"), login_record("server-5", 1, "bot-c")]


def test_coordinator_does_not_synchronize_with_itself_nor_without_a_coordinator():
    peer = RecordingReplicationPeer([], {})
    scenario = ReplicationScenario(peer)

    scenario.controller.synchronize_with_coordinator(OWN_NAME)
    scenario.controller.synchronize_with_coordinator(None)

    assert peer.watermarks_sent == []


def test_new_coordinator_triggers_a_single_synchronization():
    peer = RecordingReplicationPeer([], {})
    scenario = ReplicationScenario(peer)

    scenario.controller.synchronize_on_new_coordinator(COORDINATOR_NAME)
    scenario.controller.synchronize_on_new_coordinator(COORDINATOR_NAME)

    assert len(peer.watermarks_sent) == 1


def test_unavailable_coordinator_leaves_the_data_untouched():
    scenario = ReplicationScenario(UnavailablePeer())

    scenario.controller.synchronize_with_coordinator(COORDINATOR_NAME)

    assert scenario.logged_usernames() == []


def test_answer_to_a_synchronization_carries_the_missing_records_and_own_watermarks():
    scenario = ReplicationScenario(RecordingReplicationPeer([], {}))
    scenario.controller.apply_remote_record(login_record("server-1", 1, "bot-a"))
    scenario.controller.apply_remote_record(login_record("server-1", 2, "bot-b"))

    records, watermarks = scenario.controller.answer_synchronization({"server-1": 1})

    assert records == [login_record("server-1", 2, "bot-b")]
    assert watermarks == {"server-1": 2}


def test_local_login_record_reads_back_as_a_login():
    scenario = ReplicationScenario(RecordingReplicationPeer([], {}))

    scenario.controller.apply_remote_record(login_record("server-1", 1, "bot-a"))

    assert scenario.login_repository.logins_of("bot-a") == [Login("bot-a", 1_000)]


def test_channel_from_replication_is_listed_like_a_local_one():
    scenario = ReplicationScenario(RecordingReplicationPeer([], {}))
    scenario.channel_repository.add_if_absent(Channel("general", "bot-1", 1_000, 1, OWN_NAME))

    scenario.controller.apply_remote_record(channel_record("server-1", 1, "news", logical_clock=3))

    assert scenario.channel_repository.all_names() == ["general", "news"]
