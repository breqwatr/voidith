""" Tests for registry service """
from unittest.mock import patch

from click.testing import CliRunner

import voithos.cli.service.pxe


def test_registry_group():
    """ test the pxe group cli call """
    runner = CliRunner()
    result = runner.invoke(voithos.cli.service.pxe.get_pxe_group())
    assert result.exit_code == 0


@patch("voithos.lib.service.pxe.shell")
@patch("voithos.lib.service.pxe.ecr")
def test_registry_start(mock_ecr, mock_shell):
    """ test ceph-ansible cli call """
    runner = CliRunner()
    result = runner.invoke(
        voithos.cli.service.pxe.start,
        [
            "--interface",
            "en0",
            "--dhcp-start",
            "192.168.0.130",
            "--dhcp-end",
            "192.168.0.190",
            "--release",
            "stable",
        ],
        catch_exceptions=False,
    )
    #assert mock_ecr.pull.call_count == 1
    #assert mock_shell.call_count == 1
    assert result.exit_code == 0, result.output
