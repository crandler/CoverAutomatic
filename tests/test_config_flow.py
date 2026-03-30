"""Tests for CoverAutomatic config flow."""
from __future__ import annotations

from unittest.mock import MagicMock, PropertyMock

import pytest

from custom_components.cover_automatic.config_flow import (
    CoverAutomaticConfigFlow,
    CoverAutomaticOptionsFlow,
)


# ---------------------------------------------------------------------------
# ConfigFlow tests
# ---------------------------------------------------------------------------


class TestConfigFlow:
    """Tests for the initial ConfigFlow."""

    @pytest.mark.asyncio
    async def test_step_user_shows_form(self) -> None:
        """Test user step shows confirmation form when no input."""
        flow = CoverAutomaticConfigFlow()
        flow.hass = MagicMock()

        result = await flow.async_step_user(None)

        assert result["type"] == "form"
        assert result["step_id"] == "user"

    @pytest.mark.asyncio
    async def test_step_user_creates_entry(self) -> None:
        """Test user step creates entry with empty data on confirm."""
        flow = CoverAutomaticConfigFlow()
        flow.hass = MagicMock()
        flow.async_create_entry = MagicMock(return_value={"type": "create_entry"})

        result = await flow.async_step_user({})

        flow.async_create_entry.assert_called_once_with(
            title="CoverAutomatic", data={}
        )
        assert result["type"] == "create_entry"

    def test_async_get_options_flow_returns_correct_class(self) -> None:
        """Test async_get_options_flow returns CoverAutomaticOptionsFlow."""
        mock_entry = MagicMock()
        flow = CoverAutomaticConfigFlow.async_get_options_flow(mock_entry)

        assert isinstance(flow, CoverAutomaticOptionsFlow)


# ---------------------------------------------------------------------------
# OptionsFlow tests
# ---------------------------------------------------------------------------


class TestOptionsFlow:
    """Tests for the OptionsFlow (redirect to panel)."""

    @pytest.fixture
    def options_flow(self) -> CoverAutomaticOptionsFlow:
        """Create OptionsFlow instance with mocked dependencies."""
        flow = CoverAutomaticOptionsFlow()
        flow.hass = MagicMock()

        mock_entry = MagicMock()
        mock_entry.options = {"scan_interval": 60}
        type(flow).config_entry = PropertyMock(return_value=mock_entry)

        return flow

    @pytest.mark.asyncio
    async def test_init_shows_form(self, options_flow) -> None:
        """Test init step shows form when no input."""
        result = await options_flow.async_step_init(None)

        assert result["type"] == "form"
        assert result["step_id"] == "init"

    @pytest.mark.asyncio
    async def test_init_creates_entry_on_submit(self, options_flow) -> None:
        """Test init step creates entry preserving existing options."""
        options_flow.async_create_entry = MagicMock(
            return_value={"type": "create_entry"}
        )

        result = await options_flow.async_step_init({})

        options_flow.async_create_entry.assert_called_once_with(
            title="", data={"scan_interval": 60}
        )
        assert result["type"] == "create_entry"

    @pytest.mark.asyncio
    async def test_init_preserves_empty_options(self) -> None:
        """Test init step works with empty options dict."""
        flow = CoverAutomaticOptionsFlow()
        flow.hass = MagicMock()

        mock_entry = MagicMock()
        mock_entry.options = {}
        type(flow).config_entry = PropertyMock(return_value=mock_entry)
        flow.async_create_entry = MagicMock(return_value={"type": "create_entry"})

        await flow.async_step_init({"confirm": True})

        flow.async_create_entry.assert_called_once_with(title="", data={})
