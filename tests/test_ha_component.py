"""Tests for the HA custom component: coordinator, config flow, and setup/unload."""

from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from custom_components.comelit_man.models import Camera, DeviceConfig, Door, PushEvent

# Import after conftest has set up mocked HA modules
from custom_components.comelit_man.coordinator import (
    ComelitLocalCoordinator,
    UpdateFailed,
)
from custom_components.comelit_man.exceptions import (
    AuthenticationError,
    ConnectionComelitError,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

HOST = "192.168.1.100"
PORT = 64100
TOKEN = "abc123"


def _make_config() -> DeviceConfig:
    return DeviceConfig(
        apt_address="00000001",
        doors=[Door(id=1, index=0, name="Front", apt_address="00000001", output_index=0)],
        cameras=[Camera(id=1, name="Cam1", rtsp_url="rtsp://cam")],
    )


def _make_hass() -> MagicMock:
    hass = MagicMock()
    hass.data = {}
    hass.config_entries = MagicMock()
    hass.config_entries.async_forward_entry_setups = AsyncMock()
    hass.config_entries.async_unload_platforms = AsyncMock(return_value=True)
    return hass


def _make_coordinator(hass=None) -> ComelitLocalCoordinator:
    entry = MagicMock()
    entry.options = {}
    entry.title = "Test Intercom"
    return ComelitLocalCoordinator(hass or _make_hass(), entry, HOST, PORT, TOKEN)


def _mock_client():
    client = MagicMock()
    client.connect = AsyncMock()
    client.disconnect = AsyncMock()
    client.connected = True
    return client


# ===========================================================================
# Coordinator — async_setup()
# ===========================================================================


class TestCoordinatorSetup:
    """Tests for ComelitLocalCoordinator.async_setup()."""

    @pytest.mark.asyncio
    async def test_setup_success(self):
        """All steps succeed → config/client set, async_set_updated_data called."""
        coord = _make_coordinator()
        config = _make_config()
        client = _mock_client()

        mock_rtsp = MagicMock()
        mock_rtsp.start = AsyncMock(return_value="rtsp://127.0.0.1:8557/live")

        with (
            patch(
                "custom_components.comelit_man.coordinator.IconaBridgeClient",
                return_value=client,
            ),
            patch(
                "custom_components.comelit_man.coordinator.authenticate",
                new_callable=AsyncMock,
            ),
            patch(
                "custom_components.comelit_man.coordinator.get_device_config",
                new_callable=AsyncMock,
                return_value=config,
            ),
            patch(
                "custom_components.comelit_man.coordinator.register_push",
                new_callable=AsyncMock,
            ),
            patch(
                "custom_components.comelit_man.coordinator.LocalRtspServer",
                return_value=mock_rtsp,
            ),
            patch.object(coord, "_start_keepalive"),
        ):
            await coord.async_setup()

        assert coord._client is client
        assert coord._config is config
        assert coord.device_config is config

    @pytest.mark.asyncio
    async def test_setup_authenticate_fails(self):
        """authenticate raises → client.disconnect() called, exception propagates."""
        coord = _make_coordinator()
        client = _mock_client()

        with (
            patch(
                "custom_components.comelit_man.coordinator.IconaBridgeClient",
                return_value=client,
            ),
            patch(
                "custom_components.comelit_man.coordinator.authenticate",
                new_callable=AsyncMock,
                side_effect=AuthenticationError("bad token"),
            ),
            pytest.raises(AuthenticationError),
        ):
            await coord.async_setup()

        client.disconnect.assert_awaited_once()
        assert coord._client is None

    @pytest.mark.asyncio
    async def test_setup_get_device_config_fails(self):
        """get_device_config raises → client.disconnect() called."""
        coord = _make_coordinator()
        client = _mock_client()

        with (
            patch(
                "custom_components.comelit_man.coordinator.IconaBridgeClient",
                return_value=client,
            ),
            patch(
                "custom_components.comelit_man.coordinator.authenticate",
                new_callable=AsyncMock,
            ),
            patch(
                "custom_components.comelit_man.coordinator.get_device_config",
                new_callable=AsyncMock,
                side_effect=RuntimeError("parse error"),
            ),
            pytest.raises(RuntimeError),
        ):
            await coord.async_setup()

        client.disconnect.assert_awaited_once()
        assert coord._client is None

    @pytest.mark.asyncio
    async def test_setup_register_push_fails(self):
        """register_push raises → client.disconnect() called."""
        coord = _make_coordinator()
        client = _mock_client()

        with (
            patch(
                "custom_components.comelit_man.coordinator.IconaBridgeClient",
                return_value=client,
            ),
            patch(
                "custom_components.comelit_man.coordinator.authenticate",
                new_callable=AsyncMock,
            ),
            patch(
                "custom_components.comelit_man.coordinator.get_device_config",
                new_callable=AsyncMock,
                return_value=_make_config(),
            ),
            patch(
                "custom_components.comelit_man.coordinator.register_push",
                new_callable=AsyncMock,
                side_effect=RuntimeError("push fail"),
            ),
            pytest.raises(RuntimeError),
        ):
            await coord.async_setup()

        client.disconnect.assert_awaited_once()
        assert coord._client is None


# ===========================================================================
# Coordinator — _async_update_data()
# ===========================================================================


class TestCoordinatorUpdate:
    """Tests for ComelitLocalCoordinator._async_update_data()."""

    @pytest.mark.asyncio
    async def test_connected_with_config_returns_config(self):
        """Connected with config → returns config, no reconnect."""
        coord = _make_coordinator()
        client = _mock_client()
        config = _make_config()
        coord._client = client
        coord._config = config

        result = await coord._async_update_data()

        assert result is config

    @pytest.mark.asyncio
    async def test_disconnected_triggers_reconnect(self):
        """Disconnected → calls _reconnect, returns new config."""
        coord = _make_coordinator()
        client = _mock_client()
        client.connected = False
        coord._client = client

        new_config = _make_config()

        with patch.object(
            coord, "_reconnect", new_callable=AsyncMock
        ) as mock_reconnect:
            # Simulate _reconnect setting new config
            async def do_reconnect():
                coord._config = new_config

            mock_reconnect.side_effect = do_reconnect

            result = await coord._async_update_data()

        assert result is new_config
        mock_reconnect.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_reconnect_fails_raises_update_failed(self):
        """Reconnect fails → raises UpdateFailed."""
        coord = _make_coordinator()
        coord._client = None

        with (
            patch.object(
                coord,
                "_reconnect",
                new_callable=AsyncMock,
                side_effect=ConnectionError("fail"),
            ),
            pytest.raises(UpdateFailed),
        ):
            await coord._async_update_data()

    @pytest.mark.asyncio
    async def test_client_none_triggers_reconnect(self):
        """_client is None → triggers reconnect."""
        coord = _make_coordinator()
        coord._client = None
        new_config = _make_config()

        with patch.object(
            coord, "_reconnect", new_callable=AsyncMock
        ) as mock_reconnect:

            async def do_reconnect():
                coord._config = new_config

            mock_reconnect.side_effect = do_reconnect

            result = await coord._async_update_data()

        mock_reconnect.assert_awaited_once()
        assert result is new_config


# ===========================================================================
# Coordinator — _reconnect()
# ===========================================================================


class TestCoordinatorReconnect:
    """Tests for ComelitLocalCoordinator._reconnect()."""

    @pytest.mark.asyncio
    async def test_reconnect_success(self):
        """Old client disconnected, new client fully set up."""
        coord = _make_coordinator()
        old_client = _mock_client()
        coord._client = old_client

        new_client = _mock_client()
        config = _make_config()

        with (
            patch(
                "custom_components.comelit_man.coordinator.IconaBridgeClient",
                return_value=new_client,
            ),
            patch(
                "custom_components.comelit_man.coordinator.authenticate",
                new_callable=AsyncMock,
            ),
            patch(
                "custom_components.comelit_man.coordinator.get_device_config",
                new_callable=AsyncMock,
                return_value=config,
            ),
            patch(
                "custom_components.comelit_man.coordinator.register_push",
                new_callable=AsyncMock,
            ),
            patch.object(coord, "_start_keepalive"),
        ):
            await coord._reconnect()

        old_client.disconnect.assert_awaited_once()
        assert coord._client is new_client
        assert coord._config is config

    @pytest.mark.asyncio
    async def test_reconnect_connect_fails(self):
        """New connect fails → new client disconnected, old client was disconnected."""
        coord = _make_coordinator()
        old_client = _mock_client()
        coord._client = old_client

        new_client = _mock_client()
        new_client.connect.side_effect = OSError("refused")

        with (
            patch(
                "custom_components.comelit_man.coordinator.IconaBridgeClient",
                return_value=new_client,
            ),
            pytest.raises(OSError),
        ):
            await coord._reconnect()

        old_client.disconnect.assert_awaited_once()
        new_client.disconnect.assert_awaited_once()
        assert coord._client is None


# ===========================================================================
# Coordinator — async_shutdown() + push callbacks
# ===========================================================================


class TestCoordinatorShutdownAndPush:
    """Tests for shutdown and push callback handling."""

    @pytest.mark.asyncio
    async def test_shutdown_disconnects_client(self):
        """Disconnects client."""
        coord = _make_coordinator()
        client = _mock_client()
        coord._client = client

        await coord.async_shutdown()

        client.disconnect.assert_awaited_once()
        assert coord._client is None

    @pytest.mark.asyncio
    async def test_shutdown_no_client_no_error(self):
        """No client → no error."""
        coord = _make_coordinator()
        coord._client = None

        await coord.async_shutdown()  # Should not raise

    def test_push_callbacks_dispatched(self):
        """Push callbacks dispatched to all registered listeners."""
        coord = _make_coordinator()
        events: list[PushEvent] = []
        cb1 = lambda e: events.append(("cb1", e))
        cb2 = lambda e: events.append(("cb2", e))

        coord.add_push_callback(cb1)
        coord.add_push_callback(cb2)

        event = PushEvent(event_type="ring")
        coord._on_push_event(event)

        assert len(events) == 2
        assert events[0] == ("cb1", event)
        assert events[1] == ("cb2", event)

    def test_push_callback_exception_doesnt_crash_others(self):
        """Exception in one callback doesn't crash others."""
        coord = _make_coordinator()
        events: list = []

        def bad_cb(e):
            raise RuntimeError("boom")

        good_cb = lambda e: events.append(e)

        coord.add_push_callback(bad_cb)
        coord.add_push_callback(good_cb)

        event = PushEvent(event_type="ring")
        coord._on_push_event(event)

        assert len(events) == 1
        assert events[0] is event


# ===========================================================================
# Config Flow — async_step_user()
# ===========================================================================


class TestConfigFlow:
    """Tests for ComelitLocalConfigFlow.async_step_user()."""

    def _make_flow(self):
        from custom_components.comelit_man.config_flow import (
            ComelitLocalConfigFlow,
        )

        return ComelitLocalConfigFlow()

    def _base_input(self, **overrides):
        data = {
            "host": HOST,
            "port": PORT,
            "http_port": 8080,
            "token": TOKEN,
            "password": "comelit",
        }
        data.update(overrides)
        return data

    @pytest.mark.asyncio
    async def test_no_input_shows_form(self):
        """No user_input → shows form."""
        flow = self._make_flow()
        result = await flow.async_step_user(user_input=None)
        assert result["type"] == "form"

    @pytest.mark.asyncio
    async def test_success_creates_entry(self):
        """Token provided, all succeeds → create_entry."""
        flow = self._make_flow()
        client = _mock_client()

        with (
            patch(
                "custom_components.comelit_man.config_flow.IconaBridgeClient",
                return_value=client,
            ),
            patch(
                "custom_components.comelit_man.config_flow.authenticate",
                new_callable=AsyncMock,
            ),
        ):
            result = await flow.async_step_user(self._base_input())

        assert result["type"] == "create_entry"
        assert result["title"] == f"Comelit {HOST}"
        assert result["data"]["host"] == HOST
        assert result["data"]["token"] == TOKEN
        client.disconnect.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_auth_error(self):
        """AuthenticationError → errors['base'] = 'invalid_auth'."""
        flow = self._make_flow()
        client = _mock_client()

        with (
            patch(
                "custom_components.comelit_man.config_flow.IconaBridgeClient",
                return_value=client,
            ),
            patch(
                "custom_components.comelit_man.config_flow.authenticate",
                new_callable=AsyncMock,
                side_effect=AuthenticationError("bad"),
            ),
        ):
            result = await flow.async_step_user(self._base_input())

        assert result["type"] == "form"
        assert result["errors"]["base"] == "invalid_auth"
        client.disconnect.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_connection_error(self):
        """ConnectionComelitError → errors['base'] = 'cannot_connect'."""
        flow = self._make_flow()
        client = _mock_client()
        client.connect.side_effect = ConnectionComelitError("refused")

        with patch(
            "custom_components.comelit_man.config_flow.IconaBridgeClient",
            return_value=client,
        ):
            result = await flow.async_step_user(self._base_input())

        assert result["type"] == "form"
        assert result["errors"]["base"] == "cannot_connect"
        client.disconnect.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_timeout_error(self):
        """TimeoutError → errors['base'] = 'cannot_connect'."""
        flow = self._make_flow()
        client = _mock_client()
        client.connect.side_effect = TimeoutError("timeout")

        with patch(
            "custom_components.comelit_man.config_flow.IconaBridgeClient",
            return_value=client,
        ):
            result = await flow.async_step_user(self._base_input())

        assert result["type"] == "form"
        assert result["errors"]["base"] == "cannot_connect"
        client.disconnect.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_no_token_extract_succeeds(self):
        """No token, extract_token succeeds → uses extracted token."""
        flow = self._make_flow()
        client = _mock_client()

        with (
            patch(
                "custom_components.comelit_man.config_flow.IconaBridgeClient",
                return_value=client,
            ),
            patch(
                "custom_components.comelit_man.config_flow.authenticate",
                new_callable=AsyncMock,
            ),
            patch(
                "custom_components.comelit_man.config_flow.extract_token",
                new_callable=AsyncMock,
                return_value="extracted_token_123",
            ),
        ):
            result = await flow.async_step_user(self._base_input(token=""))

        assert result["type"] == "create_entry"
        assert result["data"]["token"] == "extracted_token_123"

    @pytest.mark.asyncio
    async def test_no_token_extract_fails(self):
        """No token, extract_token fails → errors['base'] = 'token_extraction_failed'."""
        flow = self._make_flow()

        with patch(
            "custom_components.comelit_man.token.extract_token",
            new_callable=AsyncMock,
            side_effect=RuntimeError("no backup"),
        ):
            result = await flow.async_step_user(self._base_input(token=""))

        assert result["type"] == "form"
        assert result["errors"]["base"] == "token_extraction_failed"


# ===========================================================================
# Setup / Unload (__init__.py)
# ===========================================================================


class TestSetupUnload:
    """Tests for async_setup_entry and async_unload_entry."""

    @pytest.mark.asyncio
    async def test_setup_entry_success(self):
        """Setup succeeds → coordinator stored in entry.runtime_data, platforms forwarded."""
        from custom_components.comelit_man import async_setup_entry

        hass = _make_hass()
        entry = MagicMock()
        entry.data = {"host": HOST, "port": PORT, "token": TOKEN}
        entry.entry_id = "test_entry_id"
        entry.options = {}
        entry.title = "Test Intercom"

        config = _make_config()
        mock_rtsp = MagicMock()
        mock_rtsp.start = AsyncMock(return_value="rtsp://127.0.0.1:8557/live")

        with (
            patch(
                "custom_components.comelit_man.coordinator.IconaBridgeClient",
                return_value=_mock_client(),
            ),
            patch(
                "custom_components.comelit_man.coordinator.authenticate",
                new_callable=AsyncMock,
            ),
            patch(
                "custom_components.comelit_man.coordinator.get_device_config",
                new_callable=AsyncMock,
                return_value=config,
            ),
            patch(
                "custom_components.comelit_man.coordinator.register_push",
                new_callable=AsyncMock,
            ),
            patch(
                "custom_components.comelit_man.coordinator.LocalRtspServer",
                return_value=mock_rtsp,
            ),
            patch(
                "custom_components.comelit_man.coordinator.ComelitLocalCoordinator._start_keepalive"
            ),
        ):
            result = await async_setup_entry(hass, entry)

        assert result is True
        assert isinstance(entry.runtime_data, ComelitLocalCoordinator)
        hass.config_entries.async_forward_entry_setups.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_setup_entry_fails_raises_config_entry_not_ready(self):
        """Connection timeout → ConfigEntryNotReady raised."""
        from custom_components.comelit_man import async_setup_entry
        from tests.conftest import _ConfigEntryNotReady

        hass = _make_hass()
        entry = MagicMock()
        entry.data = {"host": HOST, "port": PORT, "token": TOKEN}
        entry.options = {}
        entry.title = "Test Intercom"

        client = _mock_client()
        client.connect.side_effect = TimeoutError("timeout")

        with (
            patch(
                "custom_components.comelit_man.coordinator.IconaBridgeClient",
                return_value=client,
            ),
            pytest.raises(_ConfigEntryNotReady),
        ):
            await async_setup_entry(hass, entry)

    @pytest.mark.asyncio
    async def test_unload_entry(self):
        """Unload → coordinator.async_shutdown() called, client disconnected."""
        from custom_components.comelit_man import async_setup_entry, async_unload_entry

        hass = _make_hass()
        entry = MagicMock()
        entry.data = {"host": HOST, "port": PORT, "token": TOKEN}
        entry.entry_id = "test_entry_id"
        entry.options = {}
        entry.title = "Test Intercom"

        config = _make_config()
        mock_client = _mock_client()
        mock_rtsp = MagicMock()
        mock_rtsp.start = AsyncMock(return_value="rtsp://127.0.0.1:8557/live")
        mock_rtsp.stop = AsyncMock()

        with (
            patch(
                "custom_components.comelit_man.coordinator.IconaBridgeClient",
                return_value=mock_client,
            ),
            patch(
                "custom_components.comelit_man.coordinator.authenticate",
                new_callable=AsyncMock,
            ),
            patch(
                "custom_components.comelit_man.coordinator.get_device_config",
                new_callable=AsyncMock,
                return_value=config,
            ),
            patch(
                "custom_components.comelit_man.coordinator.register_push",
                new_callable=AsyncMock,
            ),
            patch(
                "custom_components.comelit_man.coordinator.LocalRtspServer",
                return_value=mock_rtsp,
            ),
            patch(
                "custom_components.comelit_man.coordinator.ComelitLocalCoordinator._start_keepalive"
            ),
        ):
            await async_setup_entry(hass, entry)

        result = await async_unload_entry(hass, entry)

        assert result is True
        mock_client.disconnect.assert_awaited_once()
