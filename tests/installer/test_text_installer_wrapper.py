from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
WRAPPER = (ROOT / "installer" / "text-installer.sh").read_text(encoding="utf-8")


def test_text_installer_delegates_to_shared_backend_without_second_install_path():
    assert 'exec "$backend" "$@"' in WRAPPER
    assert 'does not substitute a shell-based installer' in WRAPPER


def test_missing_backend_fails_closed():
    assert 'INSTALLATION BLOCKED' in WRAPPER
    assert 'exit 78' in WRAPPER

import json

ROOT_POLICY = ROOT / "installer" / "config" / "installed-system-policy.json"
TARGET_POLICY = ROOT / "installer" / "config" / "live-target-parity.json"


def test_installed_locale_timezone_filesystem_policy_is_present_and_fail_closed():
    policy = json.loads(ROOT_POLICY.read_text(encoding="utf-8"))
    assert policy["locale"]["installer_prompt"] is True
    assert policy["time"]["required_service"] == "time-sync"
    assert policy["filesystem"]["foreign_filesystems"]["ntfs"]["identify"] is True
    assert policy["filesystem"]["foreign_filesystems"]["ntfs"]["never_force_dirty_or_hibernated_volume"] is True
    assert policy["installation_safety"]["missing_capability_policy"] == "fail_closed"


def test_installed_target_parity_requires_real_production_evidence():
    targets = json.loads(TARGET_POLICY.read_text(encoding="utf-8"))
    assert targets["acceptance"]["firmware_matrix"] == ["bios", "uefi"]
    assert targets["acceptance"]["same_iso_sha256_required_for_all_traces"] is True
    assert targets["acceptance"]["simulated_smp_is_invalid"] is True
    assert "installed_system_cold_reboot" in targets["targets"]["installer"]["success_evidence"]
