import pytest
from httpx import AsyncClient
from app.main import app

# Since full integration tests require DB, we just test the logic or mock it in a real setup.
# Here we can add a basic structural test.
def test_personal_os_schema():
    from app.schemas.personal_os import TaskCreate
    task = TaskCreate(title="Test Task", priority="HIGH")
    assert task.title == "Test Task"
    assert task.priority == "HIGH"
