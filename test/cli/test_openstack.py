""" Tests for openstack cli """
from unittest.mock import patch
from click.testing import CliRunner

import voithos.cli.openstack


def test_openstack_group():
    """ test the openstack group cli call """
    runner = CliRunner()
    result = runner.invoke(voithos.cli.openstack.get_openstack_group(), catch_exceptions=False)
    assert result.exit_code == 0


@patch("voithos.lib.openstack.shell")
def test_openstack_get_passwords(mock_shell):
    """ test generating passwords """
    runner = CliRunner()
    result = runner.invoke(
        voithos.cli.openstack.get_passwords, ["--release", "train"], catch_exceptions=False
    )
    assert result.exit_code == 0
    assert mock_shell.call_count == 1


@patch("voithos.lib.openstack.shell")
def test_openstack_get_inventory_template(mock_shell):
    """ test generating inventory """
    runner = CliRunner()
    result = runner.invoke(
        voithos.cli.openstack.get_inventory_template, ["--release", "train"], catch_exceptions=False
    )
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
            "--passwords",
            "passwords.yml",
            "--globals",
            "globals.yml",
        ],
        catch_exceptions=False,
    )
    assert result.exit_code == 0
    assert mock_shell.called
    assert mock_assert.called


@patch("voithos.lib.docker.assert_path_exists")
@patch("voithos.lib.openstack.shell")
def test_openstack_get_admin_openrc(mock_shell, mock_assert):
    """ test generating admin-openrc file """
    runner = CliRunner()
    result = runner.invoke(
        voithos.cli.openstack.get_admin_openrc,
        [
            "--passwords",
            "passwords.yml",
            "--globals",
            "globals.yml",
            "--release",
            "train",
            '--inventory',
            'inventory'
        ],
        catch_exceptions=False,
    )
    assert result.exit_code == 0, result.output
    assert mock_shell.called
    assert mock_assert.called


@patch("voithos.lib.docker.assert_path_exists")
@patch("voithos.lib.openstack.shell")
def test_openstack_cli(mock_shell, mock_assert):
    """ test openstack cli """
    runner = CliRunner()
    result = runner.invoke(
        voithos.cli.openstack.cli,
        [
            "--release",
            "train",
            "--openrc",
            "admin-openrc.sh",
        ],
        catch_exceptions=False,
    )
    assert result.exit_code == 0, result.output
    assert mock_shell.called
    assert mock_assert.called


@patch("voithos.lib.docker.assert_path_exists")
@patch("voithos.lib.openstack.shell")
def test_openstack_kolla_ansible(mock_shell, mock_assert):
    """ test running kolla-ansible """
    runner = CliRunner()
    result = runner.invoke(
        voithos.cli.openstack.kolla_ansible,
        [
            "--release",
            "train",
            "--ssh-key",
            "id_rsa",
            "--inventory",
            "inventory",
            "--passwords",
            "passwords.yml",
            "--globals",
            "globals.yml",
            "--certificates",
            "certificates/",
            "--config",
            "config/",
            "deploy",
        ],
        catch_exceptions=False,
    )
    assert result.exit_code == 0, result.output
    assert mock_shell.called
    assert mock_assert.called
