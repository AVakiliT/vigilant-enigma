import shutil
import subprocess
import time
from pathlib import Path
from sqlite3 import OperationalError

import pytest
import redis
import requests
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, clear_mappers
from tenacity import retry, stop_after_delay

import bootstrap
from allocation import config
from allocation.adapters.orm import metadata, start_mappers
from allocation.service_layer import unit_of_work


@pytest.fixture
def in_memory_db():
    engine = create_engine("sqlite:///:memory:")
    metadata.create_all(engine)
    return engine


@pytest.fixture
def sqlite_session_factory(in_memory_db):
    start_mappers(None)
    yield sessionmaker(bind=in_memory_db)
    clear_mappers()



@pytest.fixture()
def session(sqlite_session_factory):
    return sqlite_session_factory()


@retry(stop=stop_after_delay(10))
def wait_for_postgres_to_come_up(engine):
    return engine.connect()


@retry(stop=stop_after_delay(10))
def wait_for_webapp_to_come_up():
    return requests.get(config.get_api_url())


@pytest.fixture(scope="session")
def postgres_db():
    engine = create_engine(config.get_postgres_uri())
    wait_for_postgres_to_come_up(engine)
    metadata.create_all(engine)
    return engine


@pytest.fixture
def postgres_session(postgres_session_factory):
    return postgres_session_factory()


@pytest.fixture
def postgres_session_factory(postgres_db):
    start_mappers(None)
    yield sessionmaker(bind=postgres_db)
    clear_mappers()


@pytest.fixture
def restart_api():
    (Path(__file__).parent / "../src/allocation/entrypoints/flask_app.py").touch()
    time.sleep(0.5)
    wait_for_webapp_to_come_up()


@retry(stop=stop_after_delay(10))
def wait_for_redis_to_come_up():
    r = redis.Redis(**config.get_redis_host_and_port())
    return r.ping()


@pytest.fixture
def restart_redis_pubsub():
    wait_for_redis_to_come_up()
    if not shutil.which("docker-compose"):
        print("skipping restart, assumes running in container")
        return
    subprocess.run(
        ["docker-compose", "restart", "-t", "0", "redis_pubsub"],
        check=True,
    )
@pytest.fixture
def sqlite_bus(sqlite_session_factory):
     bus = bootstrap.bootstrap(
     start_orm=True,
     uow=unit_of_work.SqlAlchemyUnitOfWork(sqlite_session_factory),
     notifications=lambda *args: None,
     publish=lambda *args: None,
     )
     yield bus
     clear_mappers()
