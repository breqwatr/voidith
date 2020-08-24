""" Tests for the arcus API service integration commands """
from unittest.mock import patch
from click.testing import CliRunner

import voithos.cli.service.arcus.integrations


def test_arcus_api_integration_group():
    """ test the arcus api integration group cli call """
    runner = CliRunner()
    result = runner.invoke(voithos.cli.service.arcus.integrations.get_integrations_group())
    assert result.exit_code == 0


@patch("voithos.cli.service.arcus.integrations.is_port_open")
@patch("voithos.lib.service.arcus.integrations.requests")
def test_arcus_api_integration_list_types(mock_requests, mock_is_port_open):
    """ test the arcus api integrations list-types cli call """
    runner = CliRunner()
    mock_is_port_open.return_value = True
    mock_requests.get.return_value.status_code = 200
    result = runner.invoke(
        voithos.cli.service.arcus.integrations.integrations_list_types,
        [
            "--api-addr",
            "http://10.10.111.222:1234"
        ],
        catch_exceptions=False
    )
    assert result.exit_code == 0
    assert mock_requests.get.called
    assert mock_is_port_open.called


@patch("voithos.cli.service.arcus.integrations.is_port_open")
@patch("voithos.lib.service.arcus.integrations.requests")
def test_arcus_api_integration_show_type(mock_requests, mock_is_port_open):
    """ test the arcus api integrations show-types cli call """
    runner = CliRunner()
    mock_is_port_open.return_value = True
    mock_requests.get.return_value.status_code = 200
    type_name = "ceph"
    result = runner.invoke(
        voithos.cli.service.arcus.integrations.integrations_show_type,
        [

            "--api-addr",
            "http://10.10.111.222:1234",
            type_name,
        ],
        catch_exceptions=False
    )
    assert result.exit_code == 0
    assert mock_requests.get.called
    assert mock_is_port_open.called


@patch("voithos.lib.service.arcus.integrations.api")
@patch("voithos.cli.service.arcus.integrations.is_port_open")
@patch("voithos.lib.service.arcus.integrations.requests")
def test_arcus_api_integration_list(mock_requests, mock_is_port_open, mock_api):
    """ test the arcus api integrations list cli call """
    runner = CliRunner()
    mock_requests.get.return_value.json.return_value = {'integrations': []}
    result = runner.invoke(
        voithos.cli.service.arcus.integrations.integrations_list,
        [
            "--api-addr",
            "http://10.10.111.222:1234",
            "--username",
            "example",
            "--password",
            "example"
        ],
        catch_exceptions=False
    )
    assert mock_requests.get.called
    assert mock_is_port_open.called
    assert mock_api.get_http_auth_headers.called
    assert result.exit_code == 0


def test_arcus_api_integration_delete():
    """ test the arcus api integrations delete cli call """
    runner = CliRunner()
    integration_id = "000"
    result = runner.invoke(
        voithos.cli.service.arcus.integrations.integrations_delete,
        integration_id,
        catch_exceptions=False
    )
    assert result.exit_code == 0


@patch("voithos.cli.service.arcus.integrations.is_port_open")
@patch("voithos.lib.service.arcus.integrations.requests")
def test_arcus_api_integration_create(mock_requests, mock_is_port_open):
    """ test the arcus api integrations create cli call """
    runner = CliRunner()
    mock_is_port_open.return_value = True
    mock_requests.get.return_value.status_code = 200
    mock_requests.get.return_value.json.return_value = {
        'integration_types': [
            {'type': 'Ceph', 'fields': {}}
        ]
    }
    result = runner.invoke(
        voithos.cli.service.arcus.integrations.integrations_create,
        [
            "--api-addr",
            "http://10.10.111.222:1234",
            "--username",
            "example",
            "--password",
            "example",
            "--type",
            "Ceph"
        ],
    )
    assert result.exit_code == 0
    assert mock_requests.get.called
    assert mock_is_port_open.called


def test_arcus_api_integration_update():
    """ test the arcus api integrations update cli call """
    runner = CliRunner()
    result = runner.invoke(
        voithos.cli.service.arcus.integrations.integrations_update,
        catch_exceptions=False
    )
    assert result.exit_code == 0
