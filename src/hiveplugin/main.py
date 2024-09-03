import os
import argparse
import json
from dotenv import dotenv_values
import requests
from .hive_extract import run_extraction

def load_env(env_file):
    """Load configuration from the specified .env file and merge with environment variables."""
    env = dotenv_values(env_file)
    return {**env, **os.environ}

def parse_arguments():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(description="Process data using configuration from a .env file")
    parser.add_argument("--config", default="hive_plugin.env", 
                        help="Path to the .env file (default: hive_plugin.env)")
    parser.add_argument("--input", required=True, help="Path to the input file")
    parser.add_argument("--output", default="output.json", help="Path to the output file (default: output.json)")
    parser.add_argument("--schema", default="hiveschema", help="Schema name for Metacat (default: hiveschema)")
    return parser.parse_args()

class PluginConfig:
    def __init__(self, env, input_file, output_file, schema):
        self.keycloak_token_url = env.get('KEYCLOAK_TOKEN_URL')
        self.keycloak_userinfo_url = env.get('KEYCLOAK_USERINFO_URL')
        self.keycloak_client_id = env.get('KEYCLOAK_CLIENT_ID')
        self.keycloak_client_secret = env.get('KEYCLOAK_CLIENT_SECRET')
        self.keycloak_username = env.get('KEYCLOAK_USERNAME')
        self.keycloak_password = env.get('KEYCLOAK_PASSWORD')
        self.metacat_url = env.get('METACAT_URL')     
        self.input_file = input_file
        self.output_file = output_file
        self.schema = schema

def connect_to_keycloak(config):
    """Connect to Keycloak and return an access token."""
    required_vars = ['keycloak_token_url', 'keycloak_client_id', 'keycloak_client_secret', 'keycloak_username', 'keycloak_password']
    missing_vars = [var for var in required_vars if not getattr(config, var)]
    
    if missing_vars:
        print(f"Missing required environment variables for Keycloak: {', '.join(missing_vars)}")
        return None

    data = {
        'grant_type': 'password',
        'client_id': config.keycloak_client_id,
        'client_secret': config.keycloak_client_secret,
        'username': config.keycloak_username,
        'password': config.keycloak_password
    }
    try:
        response = requests.post(config.keycloak_token_url, data=data)
        response.raise_for_status()
        return response.json()['access_token']
    except requests.RequestException as e:
        print(f"Error connecting to Keycloak: {str(e)}")
        return None

def send_data_to_metacat(config, access_token, data):
    """Send data to the Metacat API."""
    if not config.metacat_url:
        print("Missing required environment variable for Metacat: METACAT_URL")
        return None

    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json'
    }

    params = {
        'schema': f'{config.schema}',
    }

    try:
        response = requests.post(f"{config.metacat_url}/api/v1/dataset", 
                                 json=data,
                                 headers=headers,
                                 params=params)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        print(f"Error sending data to Metacat: {str(e)}")
        return None

def main():
    args = parse_arguments()
    env = load_env(args.config)
    config = PluginConfig(env, args.input, args.output, args.schema)

    # Extract data
    try:
        data = run_extraction(config.input_file, config.output_file, config.schema)
        print(f"Data extracted from {args.input}")
    except Exception as e:
        print(f"Error during extraction: {str(e)}")
        return
    
    # Send data
    access_token = connect_to_keycloak(config)
    if access_token:
        print("Successfully connected to Keycloak")

        send_data_to_metacat(config, access_token, data)
    else:
        print("Skipping Metacat submission due to Keycloak authentication failure")

if __name__ == "__main__":
    main()