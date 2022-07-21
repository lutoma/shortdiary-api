from pathlib import Path
from os import environ
from typing import List
from confz import ConfZ, ConfZFileSource
from pydantic import AnyUrl

CONFIG_DIR = Path(__file__).resolve().parent.parent


class StripeConfig(ConfZ):
    api_key: str
    webhook_secret: str
    price: str


class APIConfig(ConfZ):
    database: str
    cors_origins: List[AnyUrl]
    jwt_secret: str
    stripe: StripeConfig

    CONFIG_SOURCES = ConfZFileSource(file=environ.get(
        'SHORTDIARY_CONFIG', CONFIG_DIR / 'config.yml'))
