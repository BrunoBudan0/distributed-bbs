import sqlite3

from connectors import PeerConnector
from constants import CLIENT_MESSAGES_PER_REPLICA_SYNCHRONIZATION, PAYLOAD_FIELD, STATUS_FIELD
from errors import BbsError, PeerUnavailable
from models import Channel, Login, Publication, RecordKind, ReplicatedRecord, ResponseStatus
from repositories import ChannelRepository, LoginRepository, PublicationRepository, ReplicationRepository
from schemas import replicated_records_from, watermarks_from
from utils import print_ignored_replica_answer, print_replica_synchronization, print_unavailable


class ReplicationController:
    def __init__(
        self,
        server_name: str,
        database_connection: sqlite3.Connection,
        replication_repository: ReplicationRepository,
        login_repository: LoginRepository,
        channel_repository: ChannelRepository,
        publication_repository: PublicationRepository,
        peer_connector: PeerConnector,
    ) -> None:
        self.server_name = server_name
        self.database_connection = database_connection
        self.replication_repository = replication_repository
        self.login_repository = login_repository
        self.channel_repository = channel_repository
        self.publication_repository = publication_repository
        self.peer_connector = peer_connector
        self.received_client_messages = 0
        self.last_synchronized_coordinator: str | None = None
        self.appliers_by_kind = {
            RecordKind.LOGIN: self.apply_login,
            RecordKind.CHANNEL: self.apply_channel,
            RecordKind.PUBLICATION: self.apply_publication,
        }

    def count_client_message(self, coordinator_name: str | None) -> None:
        self.received_client_messages += 1
        if self.received_client_messages % CLIENT_MESSAGES_PER_REPLICA_SYNCHRONIZATION == 0:
            self.synchronize_with_coordinator(coordinator_name)

    def synchronize_on_new_coordinator(self, coordinator_name: str | None) -> None:
        if coordinator_name != self.last_synchronized_coordinator:
            self.synchronize_with_coordinator(coordinator_name)

    def synchronize_with_coordinator(self, coordinator_name: str | None) -> None:
        if coordinator_name is None or coordinator_name == self.server_name:
            return

        try:
            self.exchange_missing_records_with(coordinator_name)
        except PeerUnavailable as unavailable_coordinator:
            print_unavailable(unavailable_coordinator)
        except BbsError as answer_outside_the_protocol:
            print_ignored_replica_answer(coordinator_name, answer_outside_the_protocol.code)

    def exchange_missing_records_with(self, coordinator_name: str) -> None:
        sync_response = self.peer_connector.request_replication_sync(
            coordinator_name, self.replication_repository.contiguous_watermarks()
        )
        if sync_response[STATUS_FIELD] != ResponseStatus.SUCCESS:
            return

        received_records = replicated_records_from(sync_response[PAYLOAD_FIELD])
        coordinator_watermarks = watermarks_from(sync_response[PAYLOAD_FIELD])
        applied_record_count = self.applied_count(received_records)

        records_the_coordinator_lacks = self.replication_repository.records_after(coordinator_watermarks)
        if records_the_coordinator_lacks:
            self.peer_connector.push_records(coordinator_name, records_the_coordinator_lacks)

        self.last_synchronized_coordinator = coordinator_name
        print_replica_synchronization(coordinator_name, applied_record_count, len(records_the_coordinator_lacks))

    def answer_synchronization(
        self, requester_watermarks: dict[str, int]
    ) -> tuple[list[ReplicatedRecord], dict[str, int]]:
        return (
            self.replication_repository.records_after(requester_watermarks),
            self.replication_repository.contiguous_watermarks(),
        )

    def accept_pushed_records(self, records: list[ReplicatedRecord]) -> None:
        self.applied_count(records)

    def applied_count(self, records: list[ReplicatedRecord]) -> int:
        return sum(self.apply_remote_record(record) for record in records)

    def apply_remote_record(self, record: ReplicatedRecord) -> bool:
        with self.database_connection:
            if not self.replication_repository.add_if_new(record):
                return False
            self.appliers_by_kind[record.kind](record.domain_object())
            return True

    def apply_login(self, login: Login) -> None:
        self.login_repository.add(login)

    def apply_channel(self, channel: Channel) -> None:
        if self.channel_repository.add_if_absent(channel):
            return

        current_creation = self.channel_repository.channel_named(channel.name)
        if channel.wins_over(current_creation):
            self.channel_repository.replace_creation(channel)

    def apply_publication(self, publication: Publication) -> None:
        self.publication_repository.add(publication)
