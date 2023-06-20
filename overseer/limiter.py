from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from overseer.flask import OVERSEER
from loguru import logger

limiter = None
# Very basic DOS prevention
logger.init("Limiter Cache", status="Connecting")

# Allow local workstation run
if limiter is None:
    limiter = Limiter(
        OVERSEER,
        key_func=get_remote_address,
        default_limits=["90 per minute"],
        headers_enabled=True
    )
    logger.init_warn("Limiter Cache", status="Memory Only")
