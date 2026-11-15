"""Tests for the hikvision_next integration."""

import pytest
from unittest.mock import patch
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr
from custom_components.hikvision_next.const import DOMAIN
from custom_components.hikvision_next.hikvision_device import HikvisionDevice
from pytest_homeassistant_custom_component.common import MockConfigEntry
from homeassistant.config_entries import ConfigEntryState

from tests.conftest import TEST_CONFIG, TEST_CONFIG_WITH_ALARM_SERVER, TEST_CONFIG_OUTSIDE_NETWORK


@pytest.mark.parametrize("init_integration",
[
    "DS-7608NXI-I2",
    "DS-2CD2386G2-IU",
    "DS-2CD2146G2-ISU",
    "DS-2CD2443G0-IW",
    "DS-2CD2532F-IWS",
    "DS-2TD1228-2-QA",
    "DS-2CD2346G2-ISU",
    "DS-2CD2T46G2-ISU",
    "DS-2CD2T86G2-ISU",
    "DS-2SE4C425MWG-E-26",
    "DS-7616NI-K2",
    "DS-7616NI-Q2",
    "DS-7732NI-M4",
    "iDS-7204HUHI-M1",
    "iDS-7208HQHI-M1"
], indirect=True)

async def test_basic_init(hass: HomeAssistant, init_integration: MockConfigEntry) -> None:
    """Test a successful setup entry."""

    entry = init_integration
    assert entry.state == ConfigEntryState.LOADED

    device: HikvisionDevice = entry.runtime_data
    assert device.host == TEST_CONFIG["host"]
    assert init_integration.title in device.device_info.model


@pytest.mark.parametrize("init_integration", ["DS-7608NXI-I2"], indirect=True)
async def test_camera_devices_linked_to_nvr(hass: HomeAssistant, init_integration: MockConfigEntry) -> None:
    """Test camera devices are linked to the NVR device."""

    entry = init_integration
    device: HikvisionDevice = entry.runtime_data
    registry = dr.async_get(hass)

    nvr_entry = next(
        d for d in registry.devices.values() if (DOMAIN, device.device_info.serial_no) in d.identifiers
    )

    camera_entries = [
        d
        for d in registry.devices.values()
        if d.id != nvr_entry.id and any(domain == DOMAIN for domain, _ in d.identifiers)
    ]
    assert camera_entries
    for camera_entry in camera_entries:
        assert camera_entry.via_device_id == nvr_entry.id


@pytest.mark.parametrize("init_integration", ["DS-7608NXI-I2"], indirect=True)
async def test_camera_device_info_via_device(
    hass: HomeAssistant, init_integration: MockConfigEntry, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Test camera device info uses via_device_id on new HA and via_device on old HA."""

    entry = init_integration
    device: HikvisionDevice = entry.runtime_data
    camera_id = device.cameras[0].id

    monkeypatch.setattr("custom_components.hikvision_next.hikvision_device.SUPPORTS_VIA_DEVICE_ID", True)
    device.nvr_device_id = "nvr-device-id"
    device_info = device.hass_device_info(camera_id)
    assert device_info["via_device_id"] == "nvr-device-id"
    assert "via_device" not in device_info

    monkeypatch.setattr("custom_components.hikvision_next.hikvision_device.SUPPORTS_VIA_DEVICE_ID", False)
    device_info = device.hass_device_info(camera_id)
    assert device_info["via_device"] == (DOMAIN, device.device_info.serial_no)
    assert "via_device_id" not in device_info


@pytest.mark.parametrize("init_integration", ["DS-7608NXI-I2"], indirect=True)
async def test_async_setup_entry_nvr(hass: HomeAssistant, init_integration: MockConfigEntry) -> None:
    """Test a successful NVR setup entry."""

    entry = init_integration
    assert entry.state == ConfigEntryState.LOADED

    device: HikvisionDevice = entry.runtime_data
    assert device.host == TEST_CONFIG["host"]
    assert len(device.cameras) == 4
    assert len(device.supported_events) == 63

    device_info = device.device_info
    capabilities = device.capabilities
    assert device_info.device_type == "NVR"
    assert device_info.firmware == "V4.62.210"
    assert capabilities.input_ports == 4
    assert TEST_CONFIG["host"].endswith(device_info.ip_address)
    assert device_info.is_nvr is True
    assert len(device_info.mac_address) == 17
    assert device_info.manufacturer == "Hikvision"
    assert device_info.model == "DS-7608NXI-I2/8P/S"
    assert device_info.name == "nvr"
    assert capabilities.output_ports == 1
    assert device.protocols.rtsp_port == "10554"
    assert device_info.serial_no == "DS-7608NXI-I0/0P/S0000000000CCRRJ00000000WCVU"
    assert len(device.storage) == 1
    assert capabilities.support_alarm_server is True
    assert capabilities.analog_cameras_inputs == 0
    assert capabilities.support_channel_zero is True
    assert capabilities.digital_cameras_inputs == 8
    assert capabilities.is_multi_channel is False
    assert capabilities.support_event_mutex_checking is False
    assert capabilities.support_holiday_mode is True

    # test successful unload
    await hass.config_entries.async_unload(entry.entry_id)
    await hass.async_block_till_done()

    assert not hass.data.get(DOMAIN)


@pytest.mark.parametrize("init_integration", ["DS-2CD2386G2-IU"], indirect=True)
async def test_async_setup_entry_ipc(hass: HomeAssistant, init_integration: MockConfigEntry) -> None:
    """Test a successful IP camera setup entry."""

    entry = init_integration
    assert entry.state == ConfigEntryState.LOADED

    device: HikvisionDevice = entry.runtime_data
    assert device.host == TEST_CONFIG["host"]
    assert len(device.cameras) == 1
    assert len(device.supported_events) == 14

    device_info = device.device_info
    capabilities = device.capabilities
    assert device_info.device_type == "IPCamera"
    assert device_info.firmware == "V5.7.15"
    assert capabilities.input_ports == 0
    assert TEST_CONFIG["host"].endswith(device_info.ip_address)
    assert device_info.is_nvr is False
    assert len(device_info.mac_address) == 17
    assert device_info.manufacturer == "Hikvision"
    assert device_info.model == "DS-2CD2386G2-IU"
    assert device_info.name == "yard"
    assert capabilities.output_ports == 0
    assert device.protocols.rtsp_port == "10554"
    assert device_info.serial_no == "DS-2CD2386G2-IU00000000AAWRJ00000000"
    assert len(device.storage) == 2
    assert capabilities.support_alarm_server is True
    assert capabilities.analog_cameras_inputs == 0
    assert capabilities.support_channel_zero is False
    assert capabilities.digital_cameras_inputs == 0
    assert capabilities.is_multi_channel is False
    assert capabilities.support_event_mutex_checking is False
    assert capabilities.support_holiday_mode is False

    # test successful unload
    await hass.config_entries.async_unload(entry.entry_id)
    await hass.async_block_till_done()

    assert not hass.data.get(DOMAIN)


@pytest.mark.parametrize("mock_config_entry", [TEST_CONFIG_WITH_ALARM_SERVER], indirect=True)
@pytest.mark.parametrize("init_integration", [("DS-7608NXI-I2", True), ("DS-2CD2386G2-IU", True)], indirect=True)
async def test_async_setup_entry_nvr_with_alarm_server(hass: HomeAssistant, init_integration: MockConfigEntry) -> None:
    """Test a successful NVR setup entry with setting alarm server."""

    entry = init_integration

    with patch("custom_components.hikvision_next.isapi.ISAPIClient.set_alarm_server") as set_alarm_server_mock:
        await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

        assert entry.state == ConfigEntryState.LOADED
        assert set_alarm_server_mock.call_args[0] == ("http://1.0.0.11:8123", "/api/hikvision")

        # test successful unload
        await hass.config_entries.async_unload(entry.entry_id)
        await hass.async_block_till_done()

        assert set_alarm_server_mock.call_args[0] == ("http://0.0.0.0:80", "/")
        assert not hass.data.get(DOMAIN)


@pytest.mark.parametrize("mock_isapi", [TEST_CONFIG_OUTSIDE_NETWORK['host']], indirect=True)
@pytest.mark.parametrize("mock_config_entry", [TEST_CONFIG_OUTSIDE_NETWORK], indirect=True)
@pytest.mark.parametrize("init_integration", [("DS-2CD2T86G2-ISU")], indirect=True)
async def test_async_setup_entry_nvr_outside_network(hass: HomeAssistant, init_integration: MockConfigEntry) -> None:
    """Test a successful IP camera setup entry outside network."""

    entry = init_integration
    assert entry.state == ConfigEntryState.LOADED

    device: HikvisionDevice = entry.runtime_data
    assert device.host == TEST_CONFIG_OUTSIDE_NETWORK["host"]
    assert len(device.cameras) == 1
    assert len(device.supported_events) == 15

    device_info = device.device_info
    capabilities = device.capabilities
    assert device_info.device_type == "IPCamera"
    assert device_info.firmware == "V5.7.18"
    assert capabilities.input_ports == 1
    assert TEST_CONFIG_OUTSIDE_NETWORK["host"].endswith(device_info.ip_address)
    assert device_info.is_nvr is False
    assert len(device_info.mac_address) == 17
    assert device_info.manufacturer == "Hikvision"
    assert device_info.model == "DS-2CD2T86G2-ISU/SL"
    assert device_info.name == "CAMERA 3"
    assert capabilities.output_ports == 1
    assert device.protocols.rtsp_port == "5151"
    assert device_info.serial_no == "DS-2CD2T86G2-ISU/SL00000000AAWRAE0000000"
    assert len(device.storage) == 1
    assert capabilities.support_alarm_server is True
    assert capabilities.analog_cameras_inputs == 0
    assert capabilities.support_channel_zero is False
    assert capabilities.digital_cameras_inputs == 0
    assert capabilities.support_event_mutex_checking is False
    assert capabilities.support_holiday_mode is False

    # test successful unload
    await hass.config_entries.async_unload(entry.entry_id)
    await hass.async_block_till_done()

    assert not hass.data.get(DOMAIN)
