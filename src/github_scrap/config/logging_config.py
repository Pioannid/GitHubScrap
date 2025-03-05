"""
Module: logging_config
Creation Date: 2025-03-05
Author: Panagiotis Ioannidis
Summary:
    Provides a centralized logging configuration for the project.
"""

import logging
from logging import Logger

def configure_logging(logger_name: str) -> Logger:
    logger = logging.getLogger(logger_name)
    if not logger.hasHandlers():
        logger.setLevel(logging.INFO)
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    return logger
