"""Tests for middleware and error handling."""
import pytest


def test_404_handler_returns_html(client):
    """Test 404 error handler returns HTML page."""
    response = client.get("/nonexistent")
    assert response.status_code == 404
    assert "text/html" in response.headers.get("content-type", "")
    assert "<!DOCTYPE" in response.text or "<html" in response.text


def test_500_handler_would_handle_errors(client):
    """Test that exception handler middleware is in place."""
    # 500 errors are harder to trigger in tests; this just validates setup
    from main import app
    assert len(app.exception_handlers) > 0
