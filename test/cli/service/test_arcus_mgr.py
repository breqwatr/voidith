""" Tests for arcus manager """

from base64 import b64encode
from unittest.mock import patch
from click.testing import CliRunner

import voithos.cli.service.arcus.client
import voithos.lib.config


def test_arcus_mgr_group():
    """ test the arcus client group cli call """
    runner = CliRunner()
    result = runner.invoke(voithos.cli.service.arcus.mgr.get_mgr_group())
    assert result.exit_code == 0


@patch("voithos.lib.aws.ecr.shell")
@patch("voithos.lib.aws.ecr.aws")
def test_arcus_mgr_pull(mock_aws, mock_shell):
    """ test the arcus mgr pull cli call """
    config = voithos.lib.config.DEFAULT_CONFIG
    config["license"] = "11111111111111111111-2222222222222222222222222222222222222222"
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
        voithos.cli.service.arcus.mgr.pull, ["--release", "7.5"], catch_exceptions=False
    )
    assert result.exit_code == 0
    assert mock_aws.get_client.return_value.get_authorization_token.called
    assert mock_shell.called


@patch("voithos.lib.service.arcus.mgr.shell")
@patch("voithos.lib.service.arcus.mgr.volume_opt")
def test_arcus_mgr_start(mock_shell, mock_volume_opt):
    """ Test starting the arcus mgr service """
    runner = CliRunner()
    result = runner.invoke(
        voithos.cli.service.arcus.mgr.start,
        [
            "--release",
            "7.5",
            "--openstack-vip",
            "1.2.2.2",
            "--sql-pass",
            "passwd",
            "--sql-ip",
            "1.2.3.4",
            "--rabbit-ip",
            "1.2.3.4",
            "--rabbit-pass",
            "4.5.6.7",
            "--no-ceph",
            "--kolla-ansible-dir",
            "/etc/arcus-mgr",
            "--cloud-name",
            "test cloud for unit tests"
        ],
        catch_exceptions=False,
    )
    assert result.exit_code == 0, result.output
    assert mock_shell.called
    assert mock_volume_opt.called
