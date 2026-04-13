from collections.abc import Generator

from neuralgraph import GraphDatabase, Session

from config import settings

driver = GraphDatabase.driver(settings.neuralgraph_uri)


def get_session() -> Generator[Session]:
    with driver.session() as session:
        yield session
