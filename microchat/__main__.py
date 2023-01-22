from dataclasses import asdict
from pathlib import Path
from typing import Callable

from aiohttp import web

from .app import app
from .core.jwt_manager import JWTManager
from .config import Config
from .storages import UoW


def create_uow_factory(config: Config) -> Callable[[], UoW]:
    pass


def run(config: Config) -> None:
    uow_factory = create_uow_factory(config)
    jwt_manager = JWTManager(config.jwt_secret)
    web.run_app(app(uow_factory, jwt_manager), **asdict(config.app))


if __name__ == "__main__":
    from argparse import ArgumentParser

    import tomlkit

    parser = ArgumentParser(description='MicroChat server')
    parser.add_argument(
        '--config', dest='config',
        type=Path, required=False,
        help='Path to config file'
    )

    args = parser.parse_args()
    config_path: Path | None = args.config
    if config_path:
        with config_path.open() as config_file:
            config_toml = tomlkit.load(config_file)
        config = Config.from_mapping(config_toml)
        run(config)
    else:
        parser.print_help()
