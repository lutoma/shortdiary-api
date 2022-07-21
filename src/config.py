from pathlib import Path
from os import environ
from typing import List
from confz import ConfZ, ConfZFileSource
from pydantic import AnyUrl


def get_config_file():
    env_path = environ.get('SHORTDIARY_CONFIG')
    if env_path:
        return Path(env_path)

    return Path(__file__).resolve().parent.parent / 'config.yml'


class StripeConfig(ConfZ):
    api_key: str
    webhook_secret: str
    price: str


class APIConfig(ConfZ):
    database: str
    cors_origins: List[AnyUrl]
    jwt_secret: str
    stripe: StripeConfig

    CONFIG_SOURCES = ConfZFileSource(file=get_config_file())
