import pytest
import os
import json
import argparse
import requests
from unittest.mock import patch, mock_open, MagicMock
from hiveplugin.main import (
    load_env, 
    parse_arguments, 
    PluginConfig, 
    connect_to_keycloak, 
    refresh_access_token, 
    send_data_to_metacat, 
    load_json_to_dict
)

@pytest.fixture
def plugin_config():
    return PluginConfig(
        {
            'KEYCLOAK_TOKEN_URL': 'http://localhost:9137/realms/realm1/protocol/openid-connect/token',
            'KEYCLOAK_CLIENT_ID': 'metacat-test',
            'KEYCLOAK_CLIENT_SECRET': 'QniovuqdPTnkJ01czWQOnYKp5y93LhqZ',
            'KEYCLOAK_USERNAME': 'test',
            'KEYCLOAK_PASSWORD': 'test',
            'METACAT_URL': 'http://localhost:5000',
        },
        input_file='hiveExample.json',
        schema='hiveschema'
    )

# Test load_env function
@patch('main.dotenv_values')
def test_load_env(mock_dotenv_values):
    # Mock the dotenv_values to simulate .env file content
    mock_dotenv_values.return_value = {
        'KEYCLOAK_USERNAME': 'test',
        'KEYCLOAK_PASSWORD': 'test'
    }
    # Mock os.environ to simulate existing environment variables
    with patch.dict(os.environ, {'EXISTING_KEY': 'existing_value'}):
        result = load_env('hive_plugin.env')
        assert result['KEYCLOAK_USERNAME'] == 'test'
        assert result['KEYCLOAK_PASSWORD'] == 'test'

# @patch('main.dotenv_values', side_effect=Exception("Error loading .env"))
# def test_load_env_exception(mock_dotenv_values):
#     with pytest.raises(Exception, match="Error loading .env"):
#         load_env('hive_plugin.env')

# Test parse_arguments function
@patch('main.argparse.ArgumentParser.parse_args')
def test_parse_arguments(mock_parse_args):
    mock_parse_args.return_value = argparse.Namespace(
        config='hive_plugin.env',
        input='hiveExample.json',
        schema='hiveschema'
    )
    result = parse_arguments()
    assert result.config == 'hive_plugin.env'
    assert result.input == 'hiveExample.json'
    assert result.schema == 'hiveschema'

@patch('main.argparse.ArgumentParser.parse_args', side_effect=SystemExit(2))
def test_parse_arguments_exception(mock_parse_args):
    with pytest.raises(SystemExit) as excinfo:
        parse_arguments()
    assert excinfo.value.code == 2  # Verify the exit code is as expected

# Test connect_to_keycloak function
@patch('main.requests.post')
def test_connect_to_keycloak_success(plugin_config, mocker):
    mock_post = mocker.patch('main.requests.post')
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        'access_token': 'test_access', 
        'refresh_token': 'test_refresh'
    }
    mock_post.return_value = mock_response

    access_token, refresh_token = connect_to_keycloak(plugin_config)
    assert access_token == 'test_access'
    assert refresh_token == 'test_refresh'

#@patch('main.requests.post')
@patch('main.requests.post', side_effect=requests.RequestException("Connection error"))
def test_connect_to_keycloak_failure(mock_post):
    mock_post.side_effect = requests.RequestException("Error connecting to Keycloak")

    config = PluginConfig(
        {
            'KEYCLOAK_TOKEN_URL': 'http://localhost:9137/realms/realm1/protocol/openid-connect/token',
            'KEYCLOAK_CLIENT_ID': 'metacat-test',
            'KEYCLOAK_CLIENT_SECRET': 'QniovuqdPTnkJ01czWQOnYKp5y93LhqZ',
            'KEYCLOAK_USERNAME': 'test',
            'KEYCLOAK_PASSWORD': 'test'
        },
        input_file='hiveExample.json',
        schema='hiveschema'
    )
    access_token, refresh_token = connect_to_keycloak(config)
    assert access_token is None
    assert refresh_token is None

# Test refresh_access_token function
@patch('main.requests.post')
def test_refresh_access_token_success(mock_post):
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        'access_token': 'new_access_token', 
        'refresh_token': 'new_refresh_token'
    }
    mock_post.return_value = mock_response

    config = PluginConfig(
        {
             'KEYCLOAK_TOKEN_URL': 'http://example.com/token',
            'KEYCLOAK_CLIENT_ID': 'client_id',
            'KEYCLOAK_CLIENT_SECRET': 'client_secret'
        },
        input_file='hiveExample.json',
        schema='hiveschema'
    )
    access_token, refresh_token = refresh_access_token(config, 'old_refresh_token')
    assert access_token == 'new_access_token'
    assert refresh_token == 'new_refresh_token'

@patch('main.requests.post', side_effect=requests.RequestException("Error refreshing token"))
def test_refresh_access_token_failure(mock_post):
    config = PluginConfig(
        {
            'KEYCLOAK_TOKEN_URL': 'http://example.com/token',
            'KEYCLOAK_CLIENT_ID': 'client_id',
            'KEYCLOAK_CLIENT_SECRET': 'client_secret'
        },
        input_file='input.json',
        schema='schema_name'
    )
    access_token, refresh_token = refresh_access_token(config, 'invalid_refresh_token')
    assert access_token is None
    assert refresh_token is None

# Test send_data_to_metacat function
@patch('main.requests.post')
def test_send_data_to_metacat_success(mock_post):
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {'status': 'success'}
    mock_post.return_value = mock_response

    config = PluginConfig(
        {'METACAT_URL': 'http://localhost:5000'},
        input_file='hiveExample.json',
        schema='hiveschema'
    )
    result = send_data_to_metacat(config, 'test_token', {'key': 'value'})
    assert result['status'] == 'success'

@patch('main.requests.post', side_effect=requests.RequestException("Error during API call"))
#@patch('main.requests.post')
def test_send_data_to_metacat_failure(mock_post):
    config = PluginConfig(
        {'METACAT_URL': 'http://localhost:5000'},
        input_file='hiveExample.json',
        schema='hiveschema'
    )
    result = send_data_to_metacat(config, 'access_token', {'key': 'value'})
    assert result is None


# Test load_json_to_dict function
# Mocking the built-in open function
@patch('builtins.open', new_callable=mock_open, read_data='{"key": "value"}')
def test_load_json_to_dict_success(mock_file):
    result = load_json_to_dict('valid_file.json')
    assert result['key'] == 'value'

@patch('builtins.open', side_effect=FileNotFoundError)
def test_load_json_to_dict_file_not_found(mock_file):
    result = load_json_to_dict('non_existent_file.json')
    assert result is None

@patch('builtins.open', new_callable=mock_open, read_data='Invalid JSON')
def test_load_json_to_dict_invalid_json(mock_file):
    result = load_json_to_dict('invalid_file.json')
    assert result is None
