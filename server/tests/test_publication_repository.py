from database_fixtures import new_in_memory_database
from models import Publication
from repositories import PublicationRepository

HISTORY_LIMIT = 3


def publication_in(
    channel_name: str, message: str, published_at_ms: int, published_by_server: str = "server-1"
) -> Publication:
    return Publication(
        channel_name=channel_name,
        author_username="bot-1",
        message=message,
        requested_at_ms=published_at_ms,
        published_at_ms=published_at_ms,
        published_by_server=published_by_server,
    )


def repository_with_publications(*publications: Publication) -> PublicationRepository:
    publication_repository = PublicationRepository(new_in_memory_database())
    for publication in publications:
        publication_repository.add(publication)
    return publication_repository


def test_history_goes_from_the_oldest_to_the_newest_publication_whatever_the_arrival_order():
    publication_repository = repository_with_publications(
        publication_in("news", "third", 3_000),
        publication_in("news", "first", 1_000),
        publication_in("news", "second", 2_000),
    )

    history = publication_repository.latest_publications_of("news", HISTORY_LIMIT)

    assert [publication.message for publication in history] == ["first", "second", "third"]


def test_history_keeps_only_the_newest_publications_up_to_the_limit():
    publication_repository = repository_with_publications(
        *(publication_in("news", f"message-{order}", order * 1_000) for order in range(1, 6))
    )

    history = publication_repository.latest_publications_of("news", HISTORY_LIMIT)

    assert [publication.message for publication in history] == ["message-3", "message-4", "message-5"]


def test_history_leaves_out_publications_of_other_channels():
    publication_repository = repository_with_publications(
        publication_in("sports", "elsewhere", 2_000),
        publication_in("news", "here", 1_000),
    )

    history = publication_repository.latest_publications_of("news", HISTORY_LIMIT)

    assert history == [publication_in("news", "here", 1_000)]


def test_publications_at_the_same_instant_follow_the_server_name_on_every_replica():
    publication_on_server_1 = publication_in("news", "zz late in the alphabet", 1_000, "server-1")
    publication_on_server_2 = publication_in("news", "aa early in the alphabet", 1_000, "server-2")
    first_replica = repository_with_publications(publication_on_server_1, publication_on_server_2)
    second_replica = repository_with_publications(publication_on_server_2, publication_on_server_1)

    first_history = first_replica.latest_publications_of("news", HISTORY_LIMIT)
    second_history = second_replica.latest_publications_of("news", HISTORY_LIMIT)

    assert first_history == second_history == [publication_on_server_1, publication_on_server_2]
