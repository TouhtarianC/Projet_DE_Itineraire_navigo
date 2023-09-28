# configure application logging

import logging.config
import os

# if hostname env var is defined use it in logs
pod_name = os.environ.get('HOSTNAME', 'LOCAL')

LOGGING_CONFIG = dict(
    version=1,
    disable_existing_loggers=True,
    formatters={
        'f': {
            'format': f'[%(asctime)s] [{pod_name}][%(process)d] [%(name)s] [%(levelname)s]    %(message)s'
        }
    },
    handlers={
        'h': {
            'class': 'logging.StreamHandler',
            'formatter': 'f',
            'level': logging.DEBUG,
            'stream': 'ext://sys.stdout',  # Default is stderr
        }
    },
    root={
        'handlers': ['h'],
        'level': logging.INFO,
    },
)

logging.config.dictConfig(LOGGING_CONFIG)
