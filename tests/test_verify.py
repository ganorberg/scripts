from unittest.mock import MagicMock, patch

import httpx
import pytest

from coldmail.verify import verify_batch, verify_email


class TestVerifyEmail:
    @patch("coldmail.verify.httpx.get")
    def test_returns_result_status(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.json.return_value = {"result": "ok", "credits": 100}
        mock_resp.raise_for_status = MagicMock()
        mock_get.return_value = mock_resp

        result = verify_email("test@example.com")
        assert result == "ok"

    @patch("coldmail.verify.httpx.get")
    def test_returns_unknown_on_missing_result(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.json.return_value = {"credits": 100}
        mock_resp.raise_for_status = MagicMock()
        mock_get.return_value = mock_resp

        result = verify_email("test@example.com")
        assert result == "unknown"

    @patch("coldmail.verify.httpx.get")
    def test_raises_on_http_error(self, mock_get):
        mock_get.side_effect = httpx.HTTPStatusError(
            "500", request=MagicMock(), response=MagicMock()
        )
        with pytest.raises(httpx.HTTPStatusError):
            verify_email("test@example.com")


class TestVerifyBatch:
    @patch("coldmail.verify.verify_email")
    @patch("coldmail.verify.time.sleep")
    def test_processes_all_leads(self, mock_sleep, mock_verify):
        mock_verify.return_value = "ok"
        leads = [{"email": f"u{i}@example.com"} for i in range(3)]
        results = verify_batch(leads, delay=0)
        assert len(results) == 3
        assert all(status == "ok" for _, status in results)

    @patch("coldmail.verify.verify_email")
    @patch("coldmail.verify.time.sleep")
    def test_handles_api_errors(self, mock_sleep, mock_verify):
        mock_verify.side_effect = [
            "ok",
            httpx.HTTPError("timeout"),
            "ok",
        ]
        leads = [{"email": f"u{i}@example.com"} for i in range(3)]
        results = verify_batch(leads, delay=0)
        assert results[0] == ("u0@example.com", "ok")
        assert results[1] == ("u1@example.com", "error")
        assert results[2] == ("u2@example.com", "ok")

    @patch("coldmail.verify.verify_email")
    @patch("coldmail.verify.time.sleep")
    def test_sleeps_between_calls(self, mock_sleep, mock_verify):
        mock_verify.return_value = "ok"
        leads = [{"email": f"u{i}@example.com"} for i in range(3)]
        verify_batch(leads, delay=0.5)
        assert mock_sleep.call_count == 2  # sleeps between, not after last
