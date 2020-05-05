""" Tests for ceph cli """
from click.testing import CliRunner
import voithos.cli.services


def test_service_group():
    """ test service group cli call """
    runner = CliRunner()
    result = runner.invoke(voithos.cli.services.get_services_group())
    assert result.exit_code == 0
