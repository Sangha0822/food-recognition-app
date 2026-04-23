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
    response = client.post("/register", json={"email": "test@test.com", "password": "abc123"})
    assert response.status_code == 200
    assert response.json()["message"] == "User registered successfully"

def test_register_duplicate_email():
    client.post("/register", json={"email": "test@test.com", "password": "abc123"})
    response = client.post("/register", json={"email": "test@test.com", "password": "abc123"})
    assert response.status_code == 400

def test_login():
    client.post("/register", json={"email": "test@test.com", "password": "abc123"})
    response = client.post("/login", data={"username": "test@test.com", "password": "abc123"})
    assert response.status_code == 200
    assert "access_token" in response.json()

def test_login_wrong_password():
    client.post("/register", json={"email": "test@test.com", "password": "abc123"})
    response = client.post("/login", data={"username": "test@test.com", "password": "wrongpassword"})
    assert response.status_code == 401

def test_get_entries_requires_auth():
    response = client.get("/entries")
    assert response.status_code == 401

def test_invalid_file_type():
    client.post("/register", json={"email": "test@test.com", "password": "password"})
    login = client.post("/login", data={"username": "test@test.com", "password": "password"})
    token = login.json()["access_token"]

    response = client.post(
        "/uploads",
        headers={"Authorization": f"Bearer {token}"},
        files={"file": ("test.txt", b"hello", "text/plain")}
    )
    assert response.status_code == 400

def test_delete_other_users_entry_forbidden():
    client.post("/register", json={"email": "user1@test.com", "password": "abc123"})
    client.post("/register", json={"email": "user2@test.com", "password": "abc123"})

    login2 = client.post("/login", data={"username": "user2@test.com", "password": "abc123"})
    token2 = login2.json()["access_token"]

    # Insert a food entry for user1 directly into the test DB
    from app.models import FoodEntry, User
    from sqlmodel import select
    with Session(engine) as session:
        user1 = session.exec(select(User).where(User.email == "user1@test.com")).first()
        entry = FoodEntry(final_label="Pizza", user_id=user1.id)
        session.add(entry)
        session.commit()
        session.refresh(entry)
        entry_id = entry.id

    # User2 tries to delete user1's entry — should get 403
    response = client.delete(f"/entries/{entry_id}", headers={"Authorization": f"Bearer {token2}"})
    assert response.status_code == 403