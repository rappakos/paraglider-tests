"""Tests for view functions and template rendering."""
import pytest


def test_index_returns_template(client):
    """Test index view returns rendered HTML with data."""
    response = client.get("/")
    assert response.status_code == 200
    html = response.text
    # Check for template markers (these should exist in index.html)
    assert "<!DOCTYPE" in html or "<html" in html
def test_response_headers_are_html(client):
    """Test all HTML endpoints return correct content-type."""
    endpoints = ["/", "/all/evaluations"]
    for endpoint in endpoints:
        response = client.get(endpoint)
        if response.status_code == 200:
            content_type = response.headers.get("content-type", "")
            assert "text/html" in content_type
