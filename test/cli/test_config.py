""" Tests for config cli """

import json
from unittest.mock import patch

from click.testing import CliRunner

import voithos.cli.config
import voithos.lib.config


def test_config_group():
    """ test the config group cli call """
    runner = CliRunner()
    result = runner.invoke(voithos.cli.config.get_config_group())
    assert result.exit_code == 0


@patch("voithos.lib.config.system")
def test_config_license(mock_system):
    """ test the config license cli call """
    runner = CliRunner()
    default_config = voithos.lib.config.DEFAULT_CONFIG
    mock_system.get_file_contents.return_value = json.dumps(default_config)
    result = runner.invoke(voithos.cli.config.license, ["--set", "qqq"])
    assert result.exit_code == 0, result.output
    assert mock_system.get_absolute_path.called
    assert mock_system.get_file_contents.called
    assert mock_system.set_file_contents.called
