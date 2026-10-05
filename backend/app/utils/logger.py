"""
Structured Application Logging Utility.
Emits structured log messages for terminal/CloudWatch and PostgreSQL persistence.
"""
import logging
import json
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from app.models.log import DeploymentLog

# Configure Python root logger with standard structured format
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] [%(name)s]: %(message)s"
)
logger = logging.getLogger("canary_simulator")


def log_event(
    db: Session,
    deployment_id: int,
    level: str,
    source: str,
    message: str
) -> DeploymentLog:
    """Log an event both to stdout/CloudWatch stream and the PostgreSQL database."""
    normalized_level = level.upper().strip()
    log_record = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "deployment_id": deployment_id,
        "level": normalized_level,
        "source": source,
        "message": message
    }
    
    # Emit to application stream
    if normalized_level == "ERROR" or normalized_level == "CRITICAL":
        logger.error(json.dumps(log_record))
    elif normalized_level == "WARNING":
        logger.warning(json.dumps(log_record))
    else:
        logger.info(json.dumps(log_record))

    # Persist in database
    db_log = DeploymentLog(
        deployment_id=deployment_id,
        level=normalized_level,
        source=source,
        message=message,
        timestamp=datetime.now(timezone.utc)
    )
    db.add(db_log)
    db.commit()
    return db_log
