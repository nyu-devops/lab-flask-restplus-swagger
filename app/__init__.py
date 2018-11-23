"""
Microservice module

This module contains the microservice code for
    service
    models
"""
import sys
import logging
from flask import Flask

# Create the Flask aoo
app = Flask(__name__)
app.config.from_object('config')

# Service needs app so must be placed after app is created
import service
import models

#
# Set up logging
#
print('Setting up logging...')
# Set up default logging for submodules to use STDOUT
# datefmt='%m/%d/%Y %I:%M:%S %p'
fmt = '[%(asctime)s] %(levelname)s in %(module)s: %(message)s'
logging.basicConfig(stream=sys.stdout, level=app.config['LOGGING_LEVEL'], format=fmt)
# Make a new log handler that uses STDOUT
handler = logging.StreamHandler(sys.stdout)
handler.setFormatter(logging.Formatter(fmt))
handler.setLevel(app.config['LOGGING_LEVEL'])
# Remove the Flask default handlers and use our own
handler_list = list(app.logger.handlers)
for log_handler in handler_list:
    app.logger.removeHandler(log_handler)
app.logger.addHandler(handler)
app.logger.setLevel(app.config['LOGGING_LEVEL'])
app.logger.info('Logging handler established')
