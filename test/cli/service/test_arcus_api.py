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
    result = runner.invoke(voithos.cli.service.arcus.api.pull)
    assert result.exit_code == 0
    assert mock_aws.get_client.return_value.get_authorization_token.called
    assert mock_shell.called
