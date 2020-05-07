""" Tests for arcus api """

from base64 import b64encode
from unittest.mock import patch
from click.testing import CliRunner

import voithos.cli.service.arcus.api
import voithos.lib.config


def test_arcus_api_group():
    """ test the arcus api group cli call """
    runner = CliRunner()
    result = runner.invoke(voithos.cli.service.arcus.api.get_api_group())
    assert result.exit_code == 0


@patch("voithos.lib.aws.ecr.shell")
@patch("voithos.lib.aws.ecr.aws")
def test_arcus_api_pull(mock_aws, mock_shell):
    """ test the arcus api pull cli call """
    config = voithos.lib.config.DEFAULT_CONFIG
    config["license"] = "11111111111111111111-2222222222222222222222222222222222222222"
    #  mock_config_system.get_file_contents.return_value = json.dumps(config)
    token = {
        "authorizationData": [
            {
                "proxyEndpoint": "http://fake.exampple.com",
                "authorizationToken": b64encode("username:password".encode("utf-8")),
            }
        ]
    }
    mock_aws.get_client.return_value.get_authorization_token.return_value = token

    runner = CliRunner()
    result = runner.invoke(
        voithos.cli.service.arcus.api.pull, ["--release", "7.5"], catch_exceptions=False
    )
    assert result.exit_code == 0
    assert mock_aws.get_client.return_value.get_authorization_token.called
    assert mock_shell.called


@patch("voithos.lib.service.arcus.api.shell")
def test_arcus_api_start(mock_shell):
    """ Test starting the arcus api service """
    runner = CliRunner()
    result = runner.invoke(
        voithos.cli.service.arcus.api.start,
        [
            "--release",
            "7.5",
            "--openstack-fqdn",
            "example.com",
            "--rabbit-pass",
            "fake-password",
            "--rabbit-ip",
            "5.5.5.5",
            "--sql-ip",
            "5.5.5.5",
            "--sql-password",
            "fake-password",
            "--ceph",
            "--https",
        ],
        catch_exceptions=False,
    )
    assert result.exit_code == 0, result.output
    assert mock_shell.called


@patch("voithos.lib.service.arcus.api.connector")
def test_arcus_api_database_init(mock_connector):
    """ Test initializing the database """
    runner = CliRunner()
    result = runner.invoke(
        voithos.cli.service.arcus.api.database_init,
        [
            "--host",
            "1.2.3.4",
            "--admin-user",
            "root",
            "--admin-pass",
            "sample-pass",
            "--arcus-pass",
            "sample-pass",
        ],
        catch_exceptions=False,
    )
    assert result.exit_code == 0, result.output
    assert mock_connector.connect.called
