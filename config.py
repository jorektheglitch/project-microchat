from pathlib import Path

ORM = 'sqlalchemy'
DB_OPTIONS = {}
DB = "postgresql+asyncpg://microchat_admin:microchat@127.0.0.1:6543/microchat"

MEDIA_DIRECTORY_NAME = "users_media"

MEDIA_DIRECTORY = Path(__file__).parent / MEDIA_DIRECTORY_NAME
