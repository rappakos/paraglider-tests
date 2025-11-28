"""Tests for routes and endpoint availability."""
import pytest


def test_index_route(client):
    """Test GET / returns 200."""
    response = client.get("/")
    assert response.status_code == 200
    assert "text/html" in response.headers.get("content-type", "")
def test_evaluations_route(client):
    """Test GET /evaluations returns 200."""
    response = client.get("/all/evaluations")
    assert response.status_code == 200
    assert "text/html" in response.headers.get("content-type", "")


def test_static_files(client):
    """Test static file serving."""
    # Favicon request shouldn't crash
    response = client.get("/favicon.ico")
    assert response.status_code in [200, 404]


def test_404_error_page(client):
    """Test 404 error handling returns error page."""
    response = client.get("/this-route-does-not-exist")
    assert response.status_code == 404
    assert "text/html" in response.headers.get("content-type", "")
