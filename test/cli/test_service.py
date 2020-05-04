""" Tests for ceph cli """
from click.testing import CliRunner
import voidith.cli.services


def test_service_group():
    """ test service group cli call """
    runner = CliRunner()
    result = runner.invoke(voidith.cli.services.get_services_group())
    assert result.exit_code == 0
