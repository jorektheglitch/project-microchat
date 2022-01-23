import json
from argparse import ArgumentParser
from ipaddress import ip_network
from pathlib import Path
from os import environ


# Parsing command line arguments
parser = ArgumentParser(description='MicroChat server')
parser.add_argument('--config', dest='config', type=str, required=False, help='Path to config file')
parser.add_argument('--gen-config', dest='gen_config', action='store_true', help='Generate config file?')
parser.add_argument('--reformat-config', dest='reformat_config', action='store_true', help='Reformat config file?')

args = parser.parse_args()

if args.gen_config:
    config = {
        'version': 1,
        'host': '::',
        'port': '80',
        'proxified': False,
        'proxy_subnetwork': '::/127',
        'application_home_directory': './',
        'serve_static': True,
        'static_root': 'www',
        'media_root': 'users_media',
        'db': {
            'type': 'postgresql',
            'driver': 'asyncpg',
            'user': 'microchat_admin',
            'password': 'microchat',
            'host': '127.0.0.1',
            'port': 6543,
            'name': 'microchat',
            'options': {}
        },
    }
    if args.config:
        with open(args.config, 'w') as f:
            json.dump(config, f, indent=2)
    else:
        config_str = json.dumps(config, indent=2)
        print(config_str)

if args.config:
    CONFIG_PATH = args.config
elif environ.get('MICROCHAT_CONFIG'):
    CONFIG_PATH = environ['MICROCHAT_CONFIG']
else:
    CONFIG_PATH = 'config.json'

# Loading config file
CONFIG = {}
if Path(CONFIG_PATH).is_file():
    try:
        with open(CONFIG_PATH, 'r') as file:
            CONFIG = json.load(file)
    except json.JSONDecodeError:
        print(f'Config file broken ({CONFIG_PATH}). Exiting...')
        exit(1)
    if args.reformat_config:
        with open(CONFIG_PATH, 'w') as file:
            json.dump(CONFIG, f, indent=2)
else:
    print(f'Config file ({CONFIG_PATH}) does not exist. Create it with "--gen-config --config {CONFIG_PATH}" command.')
    exit(1)

# Config sub-objects
DB_CONFIG = CONFIG.get('db', {})

# Basic server settings
HOST = CONFIG.get('host', '::')
PORT = CONFIG.get('port', '80')

# Reverse proxy settings
# Change it if you run microchat behind a reverse-proxy
PROXIFIED = CONFIG.get('proxified', False)
PROXY_SUBNETWORK = CONFIG.get('proxy_subnetwork', "::/127")
PROXY_SUBNET = ip_network(PROXY_SUBNETWORK)

# Home directory settings
#  Home directory specifies where will be static content directtory and user's
#  media directory
APPLICATION_HOME_DIRECTORY = CONFIG.get('application_home_directory', "./")
HOME_DIR = Path(APPLICATION_HOME_DIRECTORY)

# Static content serving settings
SERVE_STATIC = CONFIG.get('serve_static', True)
STATIC_DIRECTORY_NAME = CONFIG.get('static_root', 'www')
STATIC_PATH = HOME_DIR / STATIC_DIRECTORY_NAME

# User's media content storing settings
MEDIA_DIRECTORY_NAME = CONFIG.get('media_root', "users_media")
MEDIA_DIRECTORY = HOME_DIR / MEDIA_DIRECTORY_NAME

# Database settings
dbms = DB_CONFIG.get('type', 'postgresql')
driver = DB_CONFIG.get('driver', 'asyncpg')
user = DB_CONFIG.get('user', 'microchat_admin')
password = DB_CONFIG.get('password', 'microchat')
domain = DB_CONFIG.get('host', '127.0.0.1')
port = str(DB_CONFIG.get('port', '6543'))
database = DB_CONFIG.get('name', 'microchat')
DB = f"{dbms}+{driver}://{user}:{password}@{domain}:{port}/{database}"
DB_OPTIONS = DB_CONFIG.get('options', {})
