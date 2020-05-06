""" Unit test for the AWS lib """

import json

from unittest.mock import patch

import voithos.lib.config
import voithos.lib.aws.aws as aws


@patch("voithos.lib.config.system")
def test_get_aws_iam(mock_system):
    """ get_aws_iam returns a dict with id and secret """
    config = voithos.lib.config.DEFAULT_CONFIG
    config['license'] = '11111111111111111111-2222222222222222222222222222222222222222'
    mock_system.get_file_contents.return_value = json.dumps(config)
    iam = aws.get_aws_iam()
    assert 'id' in iam
    assert 'secret' in iam
    assert isinstance(iam, dict)
