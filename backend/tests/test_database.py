"""
Unit and integration tests for SQLAlchemy database models and relational integrity.
"""
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.database import Base, check_db_tables
from app.models import (
    User,
    Deployment,
    DeploymentVersion,
    TrafficConfig,
    Metric,
    DeploymentEvent,
    DeploymentLog
)

# Use an in-memory SQLite database for isolated test execution
TEST_DB_URL = "sqlite:///:memory:"


@pytest.fixture(scope="module")
def db_engine():
    engine = create_engine(TEST_DB_URL, connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def db_session(db_engine):
    connection = db_engine.connect()
    transaction = connection.begin()
    Session = sessionmaker(bind=connection)
    session = Session()

    yield session

    session.close()
    transaction.rollback()
    connection.close()


def test_required_tables_exist(db_engine):
    """Verify that all 7 academic required tables are created in the database schema."""
    import app.models  # noqa
    tables = Base.metadata.tables.keys()
    expected_tables = {
        "users",
        "deployments",
        "deployment_versions",
        "traffic_configs",
        "metrics",
        "deployment_events",
        "logs"
    }
    assert expected_tables.issubset(set(tables)), f"Missing tables: {expected_tables - set(tables)}"


def test_create_user_and_deployment(db_session):
    """Test user creation and associated canary deployment generation."""
    user = User(
        email="test_dev@example.com",
        hashed_password="mock_hashed_secret",
        full_name="Canary Engineer",
        role="ADMIN"
    )
    db_session.add(user)
    db_session.commit()
    assert user.id is not None

    deployment = Deployment(
        name="Canary Rollout Service",
        description="Testing canary gradual shift",
        rollback_threshold=10.0,
        user_id=user.id
    )
    db_session.add(deployment)
    db_session.commit()
    assert deployment.id is not None
    assert deployment.status == "PENDING"
    assert deployment.owner.email == "test_dev@example.com"


def test_versions_and_traffic_config_relationships(db_session):
    """Test relational integrity across deployment versions and traffic configurations."""
    user = User(email="operator@example.com", hashed_password="securepassword")
    db_session.add(user)
    db_session.commit()

    deployment = Deployment(
        name="Microservice Rollout",
        user_id=user.id,
        rollback_threshold=12.5
    )
    db_session.add(deployment)
    db_session.commit()

    # Stable (v1) and Canary (v2) versions
    v1 = DeploymentVersion(
        deployment_id=deployment.id,
        version_tag="v1.0.0",
        version_type="STABLE",
        failure_rate=0.0
    )
    v2 = DeploymentVersion(
        deployment_id=deployment.id,
        version_tag="v2.0.0",
        version_type="CANARY",
        failure_rate=0.30
    )
    traffic = TrafficConfig(
        deployment_id=deployment.id,
        stable_percentage=90.0,
        canary_percentage=10.0
    )
    db_session.add_all([v1, v2, traffic])
    db_session.commit()

    # Query back deployment
    fetched = db_session.query(Deployment).filter(Deployment.id == deployment.id).first()
    assert len(fetched.versions) == 2
    assert fetched.traffic_config.canary_percentage == 10.0
    assert fetched.traffic_config.stable_percentage == 90.0


def test_metrics_and_events_persistence(db_session):
    """Test persistence of performance metrics and audit trail events."""
    user = User(email="metrics_tester@example.com", hashed_password="pw")
    db_session.add(user)
    db_session.commit()

    deployment = Deployment(name="Telemetry Service", user_id=user.id)
    db_session.add(deployment)
    db_session.commit()

    metric = Metric(
        deployment_id=deployment.id,
        version_type="CANARY",
        total_requests=100,
        successful_requests=85,
        failed_requests=15,
        error_rate=15.0,
        avg_response_time_ms=64.2
    )
    event = DeploymentEvent(
        deployment_id=deployment.id,
        event_type="AUTO_ROLLBACK",
        message="Canary error rate (15.0%) breached rollback threshold (10.0%)",
        details='{"trigger": "threshold_exceeded", "threshold": 10.0, "actual": 15.0}'
    )
    log_entry = DeploymentLog(
        deployment_id=deployment.id,
        level="ERROR",
        source="MONITOR",
        message="Circuit breaker activated: initiating rollback to 100% stable."
    )
    db_session.add_all([metric, event, log_entry])
    db_session.commit()

    assert metric.id is not None
    assert event.id is not None
    assert log_entry.id is not None
    assert metric.error_rate == 15.0

    # Query via relationships
    dep = db_session.query(Deployment).filter_by(id=deployment.id).first()
    assert len(dep.metrics) == 1
    assert len(dep.events) == 1
    assert len(dep.logs) == 1
    assert dep.events[0].event_type == "AUTO_ROLLBACK"
