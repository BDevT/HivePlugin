# HivePlugin
Plugin to automatically ingest metadata for HIVE

## Installation
Go to releases and download the latest package (.tar.gz) and install it using the following command:
```bash
pip install <path_to_package.tar.gz>
```

## Usage
```
hiveplugin --config <path_to_config_file> --input <path_to_input_file> --output <path_to_output_file>
```

## Config file
The config file should be an env file with the following variables:
```env
KEYCLOAK_TOKEN_URL
KEYCLOAK_USERINFO_URL
KEYCLOAK_CLIENT_ID
KEYCLOAK_CLIENT_SECRET
KEYCLOAK_USERNAME
KEYCLOAK_PASSWORD
METACAT_URL
```