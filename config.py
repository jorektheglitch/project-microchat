from ipaddress import ip_network
from pathlib import Path


# basic server settings
HOST = "::"
PORT = 80

# Reverse proxy settings
#  Change it if you run microchat bihind a reverse-proxy
PROXIFIED = False
PROXY_SUBNETWORK = "::/127"
PROXY_SUBNET = ip_network(PROXY_SUBNETWORK)

# Home directory settings
#  Home directory specifies where will be static content directtory and user's
#  media directory
APPLICATION_HOME_DIRECTORY = "./"
HOME_DIR = Path(APPLICATION_HOME_DIRECTORY)

# Static content serving settings
SERVE_STATIC = True
STATIC_DIRECTORY_NAME = "www"
STATIC_PATH = HOME_DIR / STATIC_DIRECTORY_NAME

# User's media content storing settings
MEDIA_DIRECTORY_NAME = "users_media"
MEDIA_DIRECTORY = HOME_DIR / MEDIA_DIRECTORY_NAME

# Database settings
dbms = "postgresql"
driver = "asyncpg"
user = "microchat_admin"
password = "microchat"
domain = "127.0.0.1"
port = 6543
database = "microchat"
DB = "{}+{}://{}:{}@{}:{}/{}".format(
        dbms,
        driver,
        user,
        password,
        domain,
        port,
        database
    )
DB_OPTIONS = {}
