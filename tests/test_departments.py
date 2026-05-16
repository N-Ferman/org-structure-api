from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import settings
from app.db.base import Base
from app.db.session import get_db
from app.main import app


test_engine = create_engine(
    settings.test_database_url,
    pool_pre_ping=True,
)

TestingSessionLocal = sessionmaker(
    bind=test_engine,
    autocommit=False,
    autoflush=False,
)


@pytest.fixture()
def db_session() -> Generator[Session, None, None]:
    Base.metadata.drop_all(bind=test_engine)
    Base.metadata.create_all(bind=test_engine)

    db = TestingSessionLocal()

    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=test_engine)


@pytest.fixture()
def client(db_session: Session) -> Generator[TestClient, None, None]:
    def override_get_db() -> Generator[Session, None, None]:
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


def test_create_department_employee_tree_and_cycle_validation(
    client: TestClient,
) -> None:
    root_response = client.post(
        "/departments/",
        json={"name": " Engineering "},
    )

    assert root_response.status_code == 201

    root = root_response.json()

    assert root["name"] == "Engineering"
    assert root["parent_id"] is None

    duplicate_response = client.post(
        "/departments/",
        json={"name": "Engineering"},
    )

    assert duplicate_response.status_code == 409

    child_response = client.post(
        "/departments/",
        json={
            "name": "Backend",
            "parent_id": root["id"],
        },
    )

    assert child_response.status_code == 201

    child = child_response.json()

    employee_response = client.post(
        f"/departments/{child['id']}/employees/",
        json={
            "full_name": " Ivan Petrov ",
            "position": " Backend Developer ",
            "hired_at": "2025-10-01",
        },
    )

    assert employee_response.status_code == 201

    employee = employee_response.json()

    assert employee["full_name"] == "Ivan Petrov"
    assert employee["position"] == "Backend Developer"

    tree_response = client.get(
        f"/departments/{root['id']}?depth=1&include_employees=true",
    )

    assert tree_response.status_code == 200

    tree = tree_response.json()

    assert tree["department"]["name"] == "Engineering"
    assert len(tree["children"]) == 1
    assert tree["children"][0]["department"]["name"] == "Backend"
    assert tree["children"][0]["employees"][0]["full_name"] == "Ivan Petrov"

    cycle_response = client.patch(
        f"/departments/{root['id']}",
        json={"parent_id": child["id"]},
    )

    assert cycle_response.status_code == 409