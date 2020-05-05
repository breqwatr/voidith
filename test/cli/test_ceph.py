""" Tests for ceph cli """
from unittest.mock import patch

from click.testing import CliRunner

import voidith.cli.ceph
import voidith.lib.ceph


def test_ceph_group():
    """ test the ceph group cli call """
    runner = CliRunner()
    result = runner.invoke(voidith.cli.ceph.get_ceph_group())
    assert result.exit_code == 0


@patch("voidith.lib.ceph.shell")
def test_ceph_ansible(mock_shell):
    """ test ceph-ansible cli call """
    runner = CliRunner()
    result = runner.invoke(
        voidith.cli.ceph.ceph_ansible,
        ["--release", "test", "--inventory", "test", "--group-vars", "test", "--ssh-key", "test",],
    )
    assert mock_shell.call_count == 1
    assert result.exit_code == 0


@patch("voidith.lib.system.assert_path_exists")
@patch("voidith.lib.ceph.shell")
def test_ceph_zap(mock_shell, mock_assert):
    """ test ceph zap-disk """
    runner = CliRunner()
    result = runner.invoke(voidith.cli.ceph.zap_disk, ["/dev/FAKE", "--force"])
    assert mock_shell.call_count == 2
    assert mock_assert.call_count == 1
    assert result.exit_code == 0
