"""External-process model-provider profiles must surface in the normal picker."""

from __future__ import annotations

import stat

from providers import register_provider
from providers.base import ProviderProfile


class _PickerAgentProfile(ProviderProfile):
    def create_client(self, **kwargs):
        return kwargs

    def fetch_models(self, **kwargs):
        return None


def _picker_rows():
    from hermes_cli.model_switch_providers import list_picker_providers

    return list_picker_providers(current_provider="", current_model="")


def test_picker_lists_an_available_external_process_provider(tmp_path):
    executable = tmp_path / "picker-agent"
    executable.write_text("#!/bin/sh\nexit 0\n")
    executable.chmod(executable.stat().st_mode | stat.S_IEXEC)
    register_provider(_PickerAgentProfile(
        name="picker-agent",
        display_name="Picker Agent",
        auth_type="external_process",
        base_url="process://picker-agent",
        process_command=str(executable),
        fallback_models=("picker-agent",),
    ))

    rows = _picker_rows()
    assert next(row for row in rows if row["slug"] == "picker-agent") == {
        "slug": "picker-agent",
        "name": "Picker Agent",
        "is_current": False,
        "is_user_defined": False,
        "models": ["picker-agent"],
        "total_models": 1,
        "source": "external-process",
    }


def test_picker_hides_external_process_provider_without_a_runnable_command():
    register_provider(_PickerAgentProfile(
        name="missing-picker-agent",
        display_name="Missing Picker Agent",
        auth_type="external_process",
        base_url="process://missing-picker-agent",
        process_command="hermes-test-command-that-does-not-exist",
        fallback_models=("missing-picker-agent",),
    ))

    assert not any(row["slug"] == "missing-picker-agent" for row in _picker_rows())


def test_picker_uses_external_process_command_environment_override(tmp_path, monkeypatch):
    executable = tmp_path / "picker-agent-override"
    executable.write_text("#!/bin/sh\nexit 0\n")
    executable.chmod(executable.stat().st_mode | stat.S_IEXEC)
    monkeypatch.setenv("HERMES_TEST_PICKER_AGENT", str(executable))
    register_provider(_PickerAgentProfile(
        name="override-picker-agent",
        display_name="Override Picker Agent",
        auth_type="external_process",
        base_url="process://override-picker-agent",
        process_command="hermes-test-command-that-does-not-exist",
        process_command_env_vars=("HERMES_TEST_PICKER_AGENT",),
        fallback_models=("override-picker-agent",),
    ))

    assert next(row for row in _picker_rows() if row["slug"] == "override-picker-agent")[
        "source"
    ] == "external-process"
