""" Tests for Grafana service """
from click.testing import CliRunner
from unittest.mock import patch

import voithos.cli.service.grafana


def test_grafana_group():
    """ test the pxe group cli call """
    runner = CliRunner()
    result = runner.invoke(voithos.cli.service.grafana.get_grafana_group())
    assert result.exit_code == 0


@patch("voithos.lib.service.grafana.requests")
def test_grafana_create_dashboard(mock_requests):
    """ Testing dashboard creation """
    runner = CliRunner()
    result = runner.invoke(
        voithos.cli.service.grafana.dashboard_create,
        [
            "--user",
            "test-user",
            "--password",
            "tEsT_Pswd",
            "--https",
            "--ip",
            "1.2.3.4",
            "--port",
            "3000",
        ],
        catch_exceptions=False,
    )
    assert result.exit_code == 0, result.output
    assert mock_requests.post.called
