import os
import logging
from logging.handlers import TimedRotatingFileHandler


class Config:
    # FLASK_ENV controls which log level is used
    FLASK_ENV = os.getenv('FLASK_ENV', 'local')

    # Optional: override log level directly (takes priority over FLASK_ENV)
    LOG_LEVEL = os.getenv('LOG_LEVEL', None)

    # Log format — timestamp, level, logger name, message
    LOG_FORMAT = '%(asctime)s | %(levelname)-8s | %(name)s | %(message)s'
    LOG_DATE_FORMAT = '%Y-%m-%d %H:%M:%S'

    # Map environment names to console log levels
    LOG_LEVEL_MAP = {
        'local': 'DEBUG',
        'development': 'INFO',
        'production': 'WARNING',
    }

    # Directory + filename for the rotating error log (dev/prod only)
    LOG_DIR = os.getenv('LOG_DIR', 'logs')
    ERROR_LOG_FILE = 'error.log'

    # How many days of rotated error logs to keep (default: 1 year)
    LOG_BACKUP_DAYS = int(os.getenv('LOG_BACKUP_DAYS', 365))

    @classmethod
    def get_log_level(cls):
        """Priority: LOG_LEVEL env var > FLASK_ENV mapping > default DEBUG"""
        if cls.LOG_LEVEL:
            return cls.LOG_LEVEL.upper()
        return cls.LOG_LEVEL_MAP.get(cls.FLASK_ENV, 'DEBUG')

    @classmethod
    def is_hosted(cls):
        """True when running in development or production (i.e. not local)."""
        return cls.FLASK_ENV in ('development', 'production')


def setup_logging():
    """
    Configure the root logger so that every `logging.info/error/...` call
    across the app is routed consistently.

    - All environments: console handler at the environment's log level.
    - development / production: additionally write ERROR+ to a daily-rotating
      file (logs/error.log), keeping the last LOG_BACKUP_DAYS files.
    """
    root = logging.getLogger()
    log_level = Config.get_log_level()
    root.setLevel(logging.DEBUG)  # let handlers decide what to emit

    # Clear any pre-existing handlers (e.g. from logging.basicConfig) to
    # avoid duplicate log lines.
    for handler in list(root.handlers):
        root.removeHandler(handler)

    formatter = logging.Formatter(Config.LOG_FORMAT, datefmt=Config.LOG_DATE_FORMAT)

    # --- Console handler (all environments) ---
    console = logging.StreamHandler()
    console.setLevel(log_level)
    console.setFormatter(formatter)
    root.addHandler(console)

    # --- Rotating error file (development / production only) ---
    if Config.is_hosted():
        os.makedirs(Config.LOG_DIR, exist_ok=True)
        error_path = os.path.join(Config.LOG_DIR, Config.ERROR_LOG_FILE)
        file_handler = TimedRotatingFileHandler(
            error_path,
            when='midnight',           # rotate at midnight → new file per day
            backupCount=Config.LOG_BACKUP_DAYS,
            encoding='utf-8',
        )
        file_handler.setLevel(logging.ERROR)  # errors-only for efficiency
        file_handler.setFormatter(formatter)
        root.addHandler(file_handler)

    logging.getLogger(__name__).debug(
        "Logging configured (env=%s, level=%s, error_file=%s)",
        Config.FLASK_ENV, log_level, Config.is_hosted()
    )
