# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Tests for the read_config/__init__.py module."""

import pytest
from awslabs.aws_msk_mcp_server.tools.read_config import register_module
from mcp.server.fastmcp import FastMCP
from typing import cast
from unittest.mock import MagicMock, patch


class TestReadConfigInit:
    """Tests for the read_config/__init__.py module."""

    def test_register_module(self):
        """Test the register_module function."""
        # Arrange
        mock_mcp = MagicMock()

        # Act
        register_module(mock_mcp)

        # Assert
        # Verify that the tool decorators were called
        assert mock_mcp.tool.call_count == 2

        # Verify that the expected tools were registered
        mock_mcp.tool.assert_any_call(name='get_configuration_info')
        mock_mcp.tool.assert_any_call(name='list_tags_for_resource')

    @patch('boto3.client')
    @patch('awslabs.aws_msk_mcp_server.tools.read_config.describe_configuration')
    @patch('awslabs.aws_msk_mcp_server.tools.read_config.Config')
    @patch('awslabs.aws_msk_mcp_server.tools.read_config.__version__', '1.0.0')
    def test_get_configuration_info_describe(
        self, mock_config, mock_describe_configuration, mock_boto3_client
    ):
        """Test the get_configuration_info function with describe action."""
        # Arrange
        # Create a spy that will capture the decorated functions
        decorated_functions = {}

        class MockMCP:
            @staticmethod
            def tool(name=None, **kwargs):
                def decorator(func):
                    decorated_functions[name] = func
                    return func

                return decorator

        # Register the tools with our spy
        register_module(cast(FastMCP, MockMCP()))

        # Get the captured function
        get_configuration_info_func = decorated_functions['get_configuration_info']
        assert get_configuration_info_func is not None, (
            'get_configuration_info tool was not registered'
        )

        # Mock the boto3 client
        mock_client = MagicMock()
        mock_boto3_client.return_value = mock_client

        # Mock the Config class
        mock_config_instance = MagicMock()
        mock_config.return_value = mock_config_instance

        # Mock the describe_configuration function
        expected_response = {
            'Arn': 'arn:aws:kafka:us-east-1:123456789012:configuration/test-config/abcdef',
            'CreationTime': '2025-06-20T10:00:00.000Z',
            'Description': 'Test configuration',
            'KafkaVersions': ['2.8.1', '3.3.1'],
            'LatestRevision': {
                'CreationTime': '2025-06-20T10:00:00.000Z',
                'Description': 'Initial revision',
                'Revision': 1,
            },
            'Name': 'test-config',
            'State': 'ACTIVE',
        }
        mock_describe_configuration.return_value = expected_response

        # Act
        # We need to modify the function to handle the kwargs parameter correctly
        # Create a wrapper function that converts the kwargs parameter to a dictionary
        def wrapper_func(region, action, arn, kwargs=None):
            if kwargs is None:
                kwargs = {}
            return get_configuration_info_func(
                region=region, action=action, arn=arn, kwargs=kwargs
            )

        result = wrapper_func(
            region='us-east-1',
            action='describe',
            arn='arn:aws:kafka:us-east-1:123456789012:configuration/test-config/abcdef',
        )

        # Assert
        mock_config.assert_called_once_with(
            user_agent_extra='awslabs/mcp/aws-msk-mcp-server/1.0.0'
        )
        mock_boto3_client.assert_called_once_with(
            'kafka', region_name='us-east-1', config=mock_config_instance
        )
        mock_describe_configuration.assert_called_once_with(
            'arn:aws:kafka:us-east-1:123456789012:configuration/test-config/abcdef', mock_client
        )
        assert result == expected_response

    @patch('boto3.client')
    @patch('awslabs.aws_msk_mcp_server.tools.read_config.list_configuration_revisions')
    @patch('awslabs.aws_msk_mcp_server.tools.read_config.Config')
    @patch('awslabs.aws_msk_mcp_server.tools.read_config.__version__', '1.0.0')
    def test_get_configuration_info_revisions(
        self, mock_config, mock_list_configuration_revisions, mock_boto3_client
    ):
        """Test the get_configuration_info function with revisions action."""
        # Arrange
        # Create a spy that will capture the decorated functions
        decorated_functions = {}

        class MockMCP:
            @staticmethod
            def tool(name=None, **kwargs):
                def decorator(func):
                    decorated_functions[name] = func
                    return func

                return decorator

        # Register the tools with our spy
        register_module(cast(FastMCP, MockMCP()))

        # Get the captured function
        get_configuration_info_func = decorated_functions['get_configuration_info']
        assert get_configuration_info_func is not None, (
            'get_configuration_info tool was not registered'
        )

        # Mock the boto3 client
        mock_client = MagicMock()
        mock_boto3_client.return_value = mock_client

        # Mock the Config class
        mock_config_instance = MagicMock()
        mock_config.return_value = mock_config_instance

        # Mock the list_configuration_revisions function
        expected_response = {
            'Revisions': [
                {
                    'CreationTime': '2025-06-20T10:00:00.000Z',
                    'Description': 'Initial revision',
                    'Revision': 1,
                },
                {
                    'CreationTime': '2025-06-20T11:00:00.000Z',
                    'Description': 'Updated configuration',
                    'Revision': 2,
                },
            ]
        }
        mock_list_configuration_revisions.return_value = expected_response

        # Act
        # We need to modify the function to handle the kwargs parameter correctly
        # Create a wrapper function that converts the kwargs parameter to a dictionary
        def wrapper_func(region, action, arn, kwargs=None):
            if kwargs is None:
                kwargs = {}
            return get_configuration_info_func(
                region=region, action=action, arn=arn, kwargs=kwargs
            )

        kwargs_dict = {'max_results': 20, 'next_token': 'token'}

        result = wrapper_func(
            region='us-east-1',
            action='revisions',
            arn='arn:aws:kafka:us-east-1:123456789012:configuration/test-config/abcdef',
            kwargs=kwargs_dict,
        )

        # Assert
        mock_config.assert_called_once_with(
            user_agent_extra='awslabs/mcp/aws-msk-mcp-server/1.0.0'
        )
        mock_boto3_client.assert_called_once_with(
            'kafka', region_name='us-east-1', config=mock_config_instance
        )
        mock_list_configuration_revisions.assert_called_once_with(
            'arn:aws:kafka:us-east-1:123456789012:configuration/test-config/abcdef',
            mock_client,
            max_results=20,
            next_token='token',
        )
        assert result == expected_response

    @patch('boto3.client')
    @patch('awslabs.aws_msk_mcp_server.tools.read_config.describe_configuration_revision')
    @patch('awslabs.aws_msk_mcp_server.tools.read_config.Config')
    @patch('awslabs.aws_msk_mcp_server.tools.read_config.__version__', '1.0.0')
    def test_get_configuration_info_revision_details(
        self, mock_config, mock_describe_configuration_revision, mock_boto3_client
    ):
        """Test the get_configuration_info function with revision_details action."""
        # Arrange
        # Create a spy that will capture the decorated functions
        decorated_functions = {}

        class MockMCP:
            @staticmethod
            def tool(name=None, **kwargs):
                def decorator(func):
                    decorated_functions[name] = func
                    return func

                return decorator

        # Register the tools with our spy
        register_module(cast(FastMCP, MockMCP()))

        # Get the captured function
        get_configuration_info_func = decorated_functions['get_configuration_info']
        assert get_configuration_info_func is not None, (
            'get_configuration_info tool was not registered'
        )

        # Mock the boto3 client
        mock_client = MagicMock()
        mock_boto3_client.return_value = mock_client

        # Mock the Config class
        mock_config_instance = MagicMock()
        mock_config.return_value = mock_config_instance

        # Mock the describe_configuration_revision function
        expected_response = {
            'Arn': 'arn:aws:kafka:us-east-1:123456789012:configuration/test-config/abcdef',
            'CreationTime': '2025-06-20T10:00:00.000Z',
            'Description': 'Initial revision',
            'Revision': 1,
            'ServerProperties': 'auto.create.topics.enable=true\ndelete.topic.enable=true',
        }
        mock_describe_configuration_revision.return_value = expected_response

        # Act
        # We need to modify the function to handle the kwargs parameter correctly
        # Create a wrapper function that converts the kwargs parameter to a dictionary
        def wrapper_func(region, action, arn, kwargs=None):
            if kwargs is None:
                kwargs = {}
            return get_configuration_info_func(
                region=region, action=action, arn=arn, kwargs=kwargs
            )

        kwargs_dict = {'revision': 1}

        result = wrapper_func(
            region='us-east-1',
            action='revision_details',
            arn='arn:aws:kafka:us-east-1:123456789012:configuration/test-config/abcdef',
            kwargs=kwargs_dict,
        )

        # Assert
        mock_config.assert_called_once_with(
            user_agent_extra='awslabs/mcp/aws-msk-mcp-server/1.0.0'
        )
        mock_boto3_client.assert_called_once_with(
            'kafka', region_name='us-east-1', config=mock_config_instance
        )
        mock_describe_configuration_revision.assert_called_once_with(
            'arn:aws:kafka:us-east-1:123456789012:configuration/test-config/abcdef', 1, mock_client
        )
        assert result == expected_response

    @patch('boto3.client')
    @patch('awslabs.aws_msk_mcp_server.tools.read_config.Config')
    @patch('awslabs.aws_msk_mcp_server.tools.read_config.__version__', '1.0.0')
    def test_get_configuration_info_invalid_action(self, mock_config, mock_boto3_client):
        """Test the get_configuration_info function with an invalid action."""
        # Arrange
        # Create a spy that will capture the decorated functions
        decorated_functions = {}

        class MockMCP:
            @staticmethod
            def tool(name=None, **kwargs):
                def decorator(func):
                    decorated_functions[name] = func
                    return func

                return decorator

        # Register the tools with our spy
        register_module(cast(FastMCP, MockMCP()))

        # Get the captured function
        get_configuration_info_func = decorated_functions['get_configuration_info']
        assert get_configuration_info_func is not None, (
            'get_configuration_info tool was not registered'
        )

        # Mock the boto3 client
        mock_client = MagicMock()
        mock_boto3_client.return_value = mock_client

        # Mock the Config class
        mock_config_instance = MagicMock()
        mock_config.return_value = mock_config_instance

        # Act & Assert
        # We need to modify the function to handle the kwargs parameter correctly
        # Create a wrapper function that converts the kwargs parameter to a dictionary
        def wrapper_func(region, action, arn, kwargs=None):
            if kwargs is None:
                kwargs = {}
            return get_configuration_info_func(
                region=region, action=action, arn=arn, kwargs=kwargs
            )

        with pytest.raises(ValueError) as excinfo:
            wrapper_func(
                region='us-east-1',
                action='invalid_action',
                arn='arn:aws:kafka:us-east-1:123456789012:configuration/test-config/abcdef',
            )

        assert 'Unsupported action: invalid_action' in str(excinfo.value)
        mock_config.assert_called_once_with(
            user_agent_extra='awslabs/mcp/aws-msk-mcp-server/1.0.0'
        )
        mock_boto3_client.assert_called_once_with(
            'kafka', region_name='us-east-1', config=mock_config_instance
        )

    @patch('boto3.client')
    @patch('awslabs.aws_msk_mcp_server.tools.read_config.Config')
    @patch('awslabs.aws_msk_mcp_server.tools.read_config.__version__', '1.0.0')
    def test_get_configuration_info_missing_revision(self, mock_config, mock_boto3_client):
        """Test the get_configuration_info function with missing revision."""
        # Arrange
        # Create a spy that will capture the decorated functions
        decorated_functions = {}

        class MockMCP:
            @staticmethod
            def tool(name=None, **kwargs):
                def decorator(func):
                    decorated_functions[name] = func
                    return func

                return decorator

        # Register the tools with our spy
        register_module(cast(FastMCP, MockMCP()))

        # Get the captured function
        get_configuration_info_func = decorated_functions['get_configuration_info']
        assert get_configuration_info_func is not None, (
            'get_configuration_info tool was not registered'
        )

        # Mock the boto3 client
        mock_client = MagicMock()
        mock_boto3_client.return_value = mock_client

        # Mock the Config class
        mock_config_instance = MagicMock()
        mock_config.return_value = mock_config_instance

        # Act & Assert
        # We need to modify the function to handle the kwargs parameter correctly
        # Create a wrapper function that converts the kwargs parameter to a dictionary
        def wrapper_func(region, action, arn, kwargs=None):
            if kwargs is None:
                kwargs = {}
            return get_configuration_info_func(
                region=region, action=action, arn=arn, kwargs=kwargs
            )

        with pytest.raises(ValueError) as excinfo:
            wrapper_func(
                region='us-east-1',
                action='revision_details',
                arn='arn:aws:kafka:us-east-1:123456789012:configuration/test-config/abcdef',
            )

        assert 'Revision number is required for revision_details action' in str(excinfo.value)
        mock_config.assert_called_once_with(
            user_agent_extra='awslabs/mcp/aws-msk-mcp-server/1.0.0'
        )
        mock_boto3_client.assert_called_once_with(
            'kafka', region_name='us-east-1', config=mock_config_instance
        )

    @patch('boto3.client')
    @patch('awslabs.aws_msk_mcp_server.tools.read_config.list_tags_for_resource')
    @patch('awslabs.aws_msk_mcp_server.tools.read_config.Config')
    @patch('awslabs.aws_msk_mcp_server.tools.read_config.__version__', '1.0.0')
    def test_list_tags_for_resource_tool(
        self, mock_config, mock_list_tags_for_resource, mock_boto3_client
    ):
        """Test the list_tags_for_resource_tool function."""
        # Arrange
        # Create a spy that will capture the decorated functions
        decorated_functions = {}

        class MockMCP:
            @staticmethod
            def tool(name=None, **kwargs):
                def decorator(func):
                    decorated_functions[name] = func
                    return func

                return decorator

        # Register the tools with our spy
        register_module(cast(FastMCP, MockMCP()))

        # Get the captured function
        list_tags_for_resource_tool_func = decorated_functions['list_tags_for_resource']
        assert list_tags_for_resource_tool_func is not None, (
            'list_tags_for_resource tool was not registered'
        )

        # Mock the boto3 client
        mock_client = MagicMock()
        mock_boto3_client.return_value = mock_client

        # Mock the Config class
        mock_config_instance = MagicMock()
        mock_config.return_value = mock_config_instance

        # Mock the list_tags_for_resource function
        expected_response = {'Tags': {'Environment': 'Production', 'Owner': 'DataTeam'}}
        mock_list_tags_for_resource.return_value = expected_response

        # Act
        result = list_tags_for_resource_tool_func(
            region='us-east-1',
            arn='arn:aws:kafka:us-east-1:123456789012:configuration/test-config/abcdef',
        )

        # Assert
        mock_config.assert_called_once_with(
            user_agent_extra='awslabs/mcp/aws-msk-mcp-server/1.0.0'
        )
        mock_boto3_client.assert_called_once_with(
            'kafka', region_name='us-east-1', config=mock_config_instance
        )
        mock_list_tags_for_resource.assert_called_once_with(
            'arn:aws:kafka:us-east-1:123456789012:configuration/test-config/abcdef', mock_client
        )
        assert result == expected_response
