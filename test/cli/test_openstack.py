""" Tests for openstack cli """
from unittest.mock import patch
from click.testing import CliRunner

import voidith.cli.openstack


def test_openstack_group():
    """ test the openstack group cli call """
    runner = CliRunner()
    result = runner.invoke(voidith.cli.openstack.get_openstack_group())
    assert result.exit_code == 0


@patch("voidith.lib.openstack.shell")
def test_openstack_get_passwords(mock_shell):
    """ test generating passwords """
    runner = CliRunner()
    result = runner.invoke(voidith.cli.openstack.get_passwords, ["--release", "train"])
    assert result.exit_code == 0
    assert mock_shell.call_count == 1


@patch("voidith.lib.openstack.shell")
def test_openstack_get_inventory_template(mock_shell):
    """ test generating passwords """
    runner = CliRunner()
    result = runner.invoke(voidith.cli.openstack.get_inventory_template, ["--release", "train"])
    assert result.exit_code == 0
    assert mock_shell.call_count == 1


@patch("voidith.lib.docker.assert_path_exists")
@patch("voidith.lib.openstack.shell")
def test_openstack_get_certificates(mock_shell, mock_assert):
    """ test generating passwords """
    runner = CliRunner()
    result = runner.invoke(
        voidith.cli.openstack.get_certificates,
        [
            "--release",
            "train",
            "--passwords-file",
            "passwords.yml",
            "--globals-file",
            "globals.yml",
        ],
    )
    assert result.exit_code == 0
    assert mock_shell.call_count == 1
    assert mock_assert.call_count > 0
