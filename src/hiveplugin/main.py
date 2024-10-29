import os
import argparse
import json
import requests
from dotenv import dotenv_values

def load_env(env_file):
    """
    Load configuration from the specified .env file and merge it with environment variables.

    :param env_file: Path to the .env file
    :return: A dictionary with environment variables
    """
    try:
        env = dotenv_values(env_file)
        return {**env, **os.environ}
    except Exception as e:
        print(f"Error loading .env file: {e}")
        raise

def parse_arguments():
    """
    Parse command-line arguments.

    :return: Parsed arguments object
    """
    parser = argparse.ArgumentParser(description="Process data using configuration from a .env file")
    parser.add_argument("--config", default="hive_plugin.env", help="Path to the .env file (default: hive_plugin.env)")
    parser.add_argument("--input", required=True, help="Path to the input file")
    parser.add_argument("--output", default="output.json", help="Path to the output file (default: output.json)")
    parser.add_argument("--schema", default="hiveschema", help="Schema name for Metacat (default: hiveschema)")
    
    try:
        return parser.parse_args()
    except argparse.ArgumentError as e:
        print(f"Argument parsing error: {e}")
        raise

class PluginConfig:
    def __init__(self, env, input_file, output_file, schema):
        """
        Initialize PluginConfig with required parameters.

        :param env: Environment variables dictionary
        :param input_file: Path to the input file
        :param output_file: Path to the output file
        :param schema: Schema for Metacat
        """
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
    """
    Connect to Keycloak and retrieve an access token.

    :param config: PluginConfig object with Keycloak settings
    :return: Access token or None on failure
    """
    required_vars = ['keycloak_token_url', 'keycloak_client_id', 'keycloak_client_secret', 'keycloak_username', 'keycloak_password']
    missing_vars = [var for var in required_vars if not getattr(config, var)]

    if missing_vars:
        print(f"Missing required Keycloak environment variables: {', '.join(missing_vars)}")
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
        #return response.json().get('access_token')
    except requests.RequestException as e:
        print(f"Error connecting to Keycloak: {e}")
        return None

def send_data_to_metacat(config, access_token, data):
    """
    Send data to the Metacat API.

    :param config: PluginConfig object with Metacat settings
    :param access_token: Keycloak access token
    :param data: Data to be sent to Metacat API
    :return: API response or None on failure
    """
    if not config.metacat_url:
        print("Missing required environment variable for Metacat: METACAT_URL")
        return None

    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json'
    }

    params = {
        'schema': config.schema,
    }

    try:
        response = requests.post(f"{config.metacat_url}/api/v1/dataset", json=data, headers=headers, params=params)
        response.raise_for_status()
        print("Data successfully sent to Metacat.")
        return response.json()
    except requests.RequestException as e:
        print(f"Error sending data to Metacat: {str(e)}")
        return None

def load_json_to_dict(file_path):
    """
    Read a JSON file and return its content as a dictionary.

    :param file_path: Path to the JSON file
    :return: A dictionary containing the JSON data, or None on failure
    """
    try:
        with open(file_path, 'r') as file:
            data = json.load(file)
        return data
    except FileNotFoundError:
        print(f"Error: The file {file_path} was not found.")
    except json.JSONDecodeError:
        print(f"Error: The file {file_path} contains invalid JSON.")
    except Exception as e:
        print(f"An unexpected error occurred while reading {file_path}: {e}")
    return None

def main():
    """
    Main function to orchestrate argument parsing, Keycloak connection, and data submission to Metacat.
    """
    try:
        args = parse_arguments()
        env = load_env(args.config)
        config = PluginConfig(env, args.input, args.output, args.schema)

        data = load_json_to_dict(config.input_file)
        if data is None:
            print("Failed to load input data, aborting.")
            return

        access_token = connect_to_keycloak(config)
        if access_token:
            print("Successfully authenticated with Keycloak.")
            send_data_to_metacat(config, access_token, data)
        else:
            print("Authentication failed. Data submission aborted.")
    except Exception as e:
        print(f"An unexpected error occurred in the main process: {e}")
        raise

if __name__ == "__main__":
    main()
