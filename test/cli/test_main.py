""" Tests for main cli """

from click.testing import CliRunner

import voithos.cli.main
from voithos.constants import VOITHOS_VERSION


def test_entrypoint():
    """ test for the entrypoint - should show version if asked"""
    runner = CliRunner()
    result = runner.invoke(voithos.cli.main.get_entrypoint())
    assert result.exit_code == 0


def test_version():
    """ test for the entrypoint """
    runner = CliRunner()
    result = runner.invoke(voithos.cli.main.version)
    assert result.exit_code == 0
    assert result.output == f"{VOITHOS_VERSION}\n"
