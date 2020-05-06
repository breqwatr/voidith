""" Tests for arcus """

from click.testing import CliRunner

import voithos.cli.service.arcus


def test_arcus_group():
    """ test the arcus group cli call """
    runner = CliRunner()
    result = runner.invoke(voithos.cli.service.arcus.arcus.get_arcus_group())
    assert result.exit_code == 0
