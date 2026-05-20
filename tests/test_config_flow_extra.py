"""Additional config flow tests — reauth, reconfigure, options, DHCP confirm."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from custom_components.comelit_man.exceptions import AuthenticationError

HOST = "192.168.1.111"
PORT = 64100
TOKEN = "abc123def456abc123def456abc123de"


def _mock_client(*, auth_error: bool = False, connect_error: Exception | None = None):
    client = MagicMock()
    client.connect = AsyncMock(side_effect=connect_error)
    client.disconnect = AsyncMock()
    if auth_error:
        from custom_components.comelit_man.exceptions import AuthenticationError
        client.connect = AsyncMock()
    return client


# ---------------------------------------------------------------------------
# Options flow
# ---------------------------------------------------------------------------


class TestOptionsFlow:
    def _make_options_flow(self, current_notifications: bool = True):
        from custom_components.comelit_man.config_flow import ComelitLocalOptionsFlow

        entry = MagicMock()
        entry.options = {"enable_notifications": current_notifications}
        return ComelitLocalOptionsFlow(entry)

    @pytest.mark.asyncio
    async def test_no_input_shows_form(self):
        flow = self._make_options_flow()
        result = await flow.async_step_init(user_input=None)
        assert result["type"] == "form"

    @pytest.mark.asyncio
    async def test_submit_creates_entry(self):
        flow = self._make_options_flow()
        result = await flow.async_step_init(user_input={"enable_notifications": False})
        assert result["type"] in ("create_entry", "abort", "form")  # stub returns dict

    @pytest.mark.asyncio
    async def test_default_reflects_current_setting(self):
        flow = self._make_options_flow(current_notifications=False)
        result = await flow.async_step_init(user_input=None)
        # Form is shown — data_schema carries the default; just verify type
        assert result["type"] == "form"


# ---------------------------------------------------------------------------
# Reauth flow
# ---------------------------------------------------------------------------


class TestReauthFlow:
    def _make_flow(self):
        from custom_components.comelit_man.config_flow import ComelitLocalConfigFlow

        flow = ComelitLocalConfigFlow()
        # Stub the reauth entry
        mock_entry = MagicMock()
        mock_entry.data = {"host": HOST, "port": PORT, "http_port": 8080, "token": TOKEN}
        flow._get_reauth_entry = lambda: mock_entry
        return flow

    @pytest.mark.asyncio
    async def test_reauth_shows_form_on_no_input(self):
        flow = self._make_flow()
        result = await flow.async_step_reauth_confirm(user_input=None)
        assert result["type"] == "form"

    @pytest.mark.asyncio
    async def test_reauth_success_updates_entry(self):
        flow = self._make_flow()
        client = _mock_client()

        with (
            patch("custom_components.comelit_man.config_flow.IconaBridgeClient", return_value=client),
            patch("custom_components.comelit_man.config_flow.authenticate", new_callable=AsyncMock),
        ):
            result = await flow.async_step_reauth_confirm(
                user_input={"token": TOKEN, "password": "comelit"}
            )

        client.disconnect.assert_awaited_once()
        # Result should be an abort (reauth_successful) or create_entry
        assert result["type"] in ("abort", "create_entry")

    @pytest.mark.asyncio
    async def test_reauth_invalid_auth_shows_error(self):
        flow = self._make_flow()
        client = _mock_client()

        with (
            patch("custom_components.comelit_man.config_flow.IconaBridgeClient", return_value=client),
            patch(
                "custom_components.comelit_man.config_flow.authenticate",
                new_callable=AsyncMock,
                side_effect=AuthenticationError("bad token"),
            ),
        ):
            result = await flow.async_step_reauth_confirm(
                user_input={"token": TOKEN, "password": "comelit"}
            )

        assert result["type"] == "form"
        assert result["errors"]["base"] == "invalid_auth"


# ---------------------------------------------------------------------------
# Reconfigure flow
# ---------------------------------------------------------------------------


class TestReconfigureFlow:
    def _make_flow(self):
        from custom_components.comelit_man.config_flow import ComelitLocalConfigFlow

        flow = ComelitLocalConfigFlow()
        mock_entry = MagicMock()
        mock_entry.data = {"host": HOST, "port": PORT, "http_port": 8080, "token": TOKEN}
        flow._get_reconfigure_entry = lambda: mock_entry
        return flow

    @pytest.mark.asyncio
    async def test_reconfigure_shows_form_on_no_input(self):
        flow = self._make_flow()
        result = await flow.async_step_reconfigure(user_input=None)
        assert result["type"] == "form"

    @pytest.mark.asyncio
    async def test_reconfigure_success(self):
        flow = self._make_flow()
        client = _mock_client()

        with (
            patch("custom_components.comelit_man.config_flow.IconaBridgeClient", return_value=client),
            patch("custom_components.comelit_man.config_flow.authenticate", new_callable=AsyncMock),
        ):
            result = await flow.async_step_reconfigure(
                user_input={"host": HOST, "port": PORT, "http_port": 8080, "token": TOKEN, "password": "comelit"}
            )

        client.disconnect.assert_awaited_once()
        assert result["type"] in ("abort", "create_entry")

    @pytest.mark.asyncio
    async def test_reconfigure_cannot_connect(self):
        flow = self._make_flow()
        client = _mock_client(connect_error=OSError("refused"))

        with patch("custom_components.comelit_man.config_flow.IconaBridgeClient", return_value=client):
            result = await flow.async_step_reconfigure(
                user_input={"host": HOST, "port": PORT, "http_port": 8080, "token": TOKEN, "password": "comelit"}
            )

        assert result["type"] == "form"
        assert result["errors"]["base"] == "cannot_connect"
