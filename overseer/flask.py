import os
from flask import Flask, redirect
from flask_caching import Cache
from werkzeug.middleware.proxy_fix import ProxyFix
from flask_sqlalchemy import SQLAlchemy
from loguru import logger

cache = None
OVERSEER = Flask(__name__)
OVERSEER.wsgi_app = ProxyFix(OVERSEER.wsgi_app, x_for=1)

SQLITE_MODE = os.getenv("USE_SQLITE", "0") == "1"

if SQLITE_MODE:
    logger.warning("Using SQLite for database")
    OVERSEER.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///overseer.db"
else:
    OVERSEER.config["SQLALCHEMY_DATABASE_URI"] = os.getenv('POSTGRES_URI')
    OVERSEER.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
        "pool_size": 50,
        "max_overflow": -1,
    }
OVERSEER.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(OVERSEER)
db.init_app(OVERSEER)

if not SQLITE_MODE:
    with OVERSEER.app_context():
        logger.debug("pool size = {}".format(db.engine.pool.size()))
logger.init_ok("Horde Database", status="Started")

# Allow local workstation run
if cache is None:
    cache_config = {
        "CACHE_TYPE": "SimpleCache",
        "CACHE_DEFAULT_TIMEOUT": 300
    }
    cache = Cache(config=cache_config)
    cache.init_app(OVERSEER)
    logger.init_warn("Flask Cache", status="SimpleCache")

