"""Pytest configuration and fixtures for paraglider-tests."""
import os
import sys
import pytest
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# Set test environment
os.environ['ENVIRONMENT'] = 'test'


@pytest.fixture
def test_db_path(tmp_path):
    """Create a temporary test database."""
    return str(tmp_path / "test_gliders.db")


@pytest.fixture
def client():
    """Create FastAPI test client."""
    from fastapi.testclient import TestClient
    from main import app
    
    return TestClient(app)


@pytest.fixture
def async_client():
    """Create async FastAPI test client."""
    from httpx import AsyncClient
    from main import app
    
    return AsyncClient(app=app, base_url="http://test")
