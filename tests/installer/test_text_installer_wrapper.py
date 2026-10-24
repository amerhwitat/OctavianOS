from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
WRAPPER = (ROOT / "installer" / "text-installer.sh").read_text(encoding="utf-8")


def test_text_installer_delegates_to_shared_backend_without_second_install_path():
    assert 'exec "$backend" "$@"' in WRAPPER
    assert 'does not substitute a shell-based installer' in WRAPPER


def test_missing_backend_fails_closed():
    assert 'INSTALLATION BLOCKED' in WRAPPER
    assert 'exit 78' in WRAPPER
