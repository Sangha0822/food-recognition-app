from fastapi.testclient import TestClient
from sqlmodel import SQLModel, create_engine, Session
from sqlmodel.pool import StaticPool
from app.main import app
from app.database import get_session

# In-memory test database — created fresh, wiped after tests
TEST_DATABASE_URL = "sqlite://"

engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

def override_get_session():
    with Session(engine) as session:
        yield session

# Tell FastAPI to use the test DB instead of the real one
app.dependency_overrides[get_session] = override_get_session

client = TestClient(app)


def setup_function():
    SQLModel.metadata.create_all(engine)

def teardown_function():
    SQLModel.metadata.drop_all(engine)


# --- Write your tests below ---

def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200

def test_register():

def test_register_duplicate_email():

def test_login():

def test_login_wrong_password():

def test_get_entries_requires_auth():

def test_delete_other_users_entry_forbidden():