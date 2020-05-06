""" Tests for openstack cli """
from unittest.mock import patch
from click.testing import CliRunner

import voithos.cli.openstack


def test_openstack_group():
    """ test the openstack group cli call """
    runner = CliRunner()
    result = runner.invoke(voithos.cli.openstack.get_openstack_group())
    assert result.exit_code == 0


@patch("voithos.lib.openstack.shell")
def test_openstack_get_passwords(mock_shell):
    """ test generating passwords """
    runner = CliRunner()
    result = runner.invoke(voithos.cli.openstack.get_passwords, ["--release", "train"])
    assert result.exit_code == 0
    assert mock_shell.call_count == 1


@patch("voithos.lib.openstack.shell")
def test_openstack_get_inventory_template(mock_shell):
    """ test generating inventory """
    runner = CliRunner()
    result = runner.invoke(voithos.cli.openstack.get_inventory_template, ["--release", "train"])
    assert result.exit_code == 0
    assert mock_shell.call_count == 1


@patch("voithos.lib.docker.assert_path_exists")
@patch("voithos.lib.openstack.shell")
def test_openstack_get_certificates(mock_shell, mock_assert):
    """ test generating certs """
    runner = CliRunner()
    result = runner.invoke(
        voithos.cli.openstack.get_certificates,
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


@patch("voithos.lib.docker.assert_path_exists")
@patch("voithos.lib.openstack.shell")
def test_openstack_kolla_ansible(mock_shell, mock_assert):
    """ test generating passwords """
    runner = CliRunner()
    result = runner.invoke(
        voithos.cli.openstack.kolla_ansible,
        [
            "--release",
            "train",
            "--ssh-private-key-file",
            "id_rsa",
            "--inventory-file",
            "inventory",
            "--passwords-file",
            "passwords.yml",
            "--globals-file",
            "globals.yml",
            "--certificates-dir",
            "certificates/",
            "--config-dir",
            "config/",
            "deploy",
        ],
    )
    assert result.exit_code == 0, result.output
    assert mock_shell.called
    assert mock_assert.called
