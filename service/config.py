"""
Global Configuration for Application
"""
import os
import logging

LOGGING_LEVEL = logging.INFO

# Secret for session management
SECRET_KEY = os.getenv("SECRET_KEY", "sup3r-s3cr3t-for-dev")

# See if an API Key has been set for security
API_KEY = os.getenv("API_KEY")

# Turn off helpful error messages that interfere with REST API messages
ERROR_404_HELP = False
