""" Tests for ceph cli """
from click.testing import CliRunner
import voithos.cli.service


def test_service_group():
    """ test service group cli call """
    runner = CliRunner()
    result = runner.invoke(voithos.cli.service.service.get_service_group())
    assert result.exit_code == 0
