""" Tests for Horizon service """
from unittest.mock import patch

from click.testing import CliRunner
import voithos.cli.service.horizon


def test_horizon_group():
    """ test the horizon group cli call """
    runner = CliRunner()
    result = runner.invoke(voithos.cli.service.horizon.get_horizon_group())
    assert result.exit_code == 0


@patch("voithos.lib.service.horizon.shell")
def test_horizon_start(mock_shell):
    """ test horizon cli call """
    runner = CliRunner()
    result = runner.invoke(
        voithos.cli.service.horizon.start,
        [
            "--ip", "1.2.3.4",
            "--port", "5000",
            "--internal-vip", "1.2.3.4",
            "--control-node-ip", "1.2.3.4",
            "--conf-dir", "/etc/kolla/horizon",
            "--name", "horizon",
            "--release", "train"
        ],
        catch_exceptions=False,
    )
    assert mock_shell.call_count == 1
    assert result.exit_code == 0
