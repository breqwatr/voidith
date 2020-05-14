""" Tests for registry service """
from unittest.mock import patch

from click.testing import CliRunner

import voithos.cli.ceph
import voithos.lib.ceph


def test_registry_group():
    """ test the ceph group cli call """
    runner = CliRunner()
    result = runner.invoke(voithos.cli.service.registry.get_registry_group())
    assert result.exit_code == 0


@patch("voithos.lib.service.registry.shell")
def test_registry_start(mock_shell):
    """ test ceph-ansible cli call """
    runner = CliRunner()
    result = runner.invoke(
        voithos.cli.service.registry.start,
        ["--ip", "1.2.3.4", "--port", "5000"],
        catch_exceptions=False,
    )
    assert mock_shell.call_count == 1
    assert result.exit_code == 0


@patch("voithos.lib.service.registry.requests")
def test_registry_list_images(mock_requests):
    """ test ceph-ansible cli call """
    runner = CliRunner()
    result = runner.invoke(
        voithos.cli.service.registry.list_images,
        ["http://example.registry.com"],
        catch_exceptions=False,
    )
    assert mock_requests.getcalled
    assert result.exit_code == 0
