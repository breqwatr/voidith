""" Tests for arcus client """

from base64 import b64encode
from unittest.mock import patch
from click.testing import CliRunner

import voithos.cli.service.arcus.client
import voithos.lib.config


def test_arcus_client_group():
    """ test the arcus client group cli call """
    runner = CliRunner()
    result = runner.invoke(voithos.cli.service.arcus.client.get_client_group())
    assert result.exit_code == 0


@patch("voithos.lib.aws.ecr.shell")
@patch("voithos.lib.aws.ecr.aws")
def test_arcus_client_pull(mock_aws, mock_shell):
    """ test the arcus client pull cli call """
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
        voithos.cli.service.arcus.client.pull, ["--release", "7.5"], catch_exceptions=False
    )
    assert result.exit_code == 0
    assert mock_aws.get_client.return_value.get_authorization_token.called
    assert mock_shell.called


@patch("voithos.lib.docker.assert_path_exists")
@patch("voithos.lib.service.arcus.shell")
def test_arcus_client_start(mock_shell, mock_assert):
    """ Test starting the arcus client service """
    runner = CliRunner()
    result = runner.invoke(
        voithos.cli.service.arcus.client.start,
        [
            "--release",
            "7.5",
            "--api-ip",
            "5.5.5.5",
            "--openstack-ip",
            "5.5.5.5",
            "--glance-https",
            "--arcus-https",
            "--cert-path",
            "/example/fake/file",
            "--cert-key",
            "/example/fake/file",
        ],
        catch_exceptions=False,
    )
    assert result.exit_code == 0, result.output
    assert mock_shell.called
    assert mock_assert.called
