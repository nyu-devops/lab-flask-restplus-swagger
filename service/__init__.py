# Copyright 2016, 2019 John J. Rofrano. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# spell: ignore Rofrano restx gunicorn
"""
Microservice module

This module contains the microservice code for
    service
    models
"""
import os
import sys
import logging
from flask import Flask
from flask_restx import Api
from service.common import log_handlers

# NOTE: Do not change the order of this code
# The Flask app must be created
# BEFORE you import modules that depend on it !!!

# Create the Flask app
app = Flask(__name__)

app.url_map.strict_slashes = False

app.config["SECRET_KEY"] = "secret-for-dev"
app.config["LOGGING_LEVEL"] = logging.INFO
app.config["API_KEY"] = os.getenv("API_KEY")
app.config["ERROR_404_HELP"] = False

# Document the type of authorization required
authorizations = {
    "apikey": {
        "type": "apiKey", 
        "in": "header", 
        "name": "X-Api-Key"
    }
}

######################################################################
# Configure Swagger before initializing it
######################################################################
api = Api(
    app,
    version="1.0.0",
    title="Pet Demo REST API Service",
    description="This is a sample server Pet store server.",
    default="pets",
    default_label="Pet shop operations",
    doc="/apidocs",  # default also could use doc='/apidocs/'
    authorizations=authorizations,
    prefix="/api",
)


# Import the routes After the Flask app is created
# pylint: disable=wrong-import-position, wrong-import-order, cyclic-import
from service import routes, models  # noqa: F401, E402
from service.common import error_handlers

# Set up logging for production
log_handlers.init_logging(app, "gunicorn.error")

app.logger.info(70 * "*")
app.logger.info("  P E T   S E R V I C E   R U N N I N G  ".center(70, "*"))
app.logger.info(70 * "*")

app.logger.info("Service initialized!")

# If an API Key was not provided, autogenerate one
if not app.config["API_KEY"]:
    app.config["API_KEY"] = routes.generate_apikey()
    app.logger.info("Missing API Key! Autogenerated: %s", app.config["API_KEY"])

try:
    routes.init_db()
except Exception as error:  # pylint: disable=broad-except
    app.logger.critical("%s: Cannot continue", error)
    # gunicorn requires exit code 4 to stop spawning workers when they die
    sys.exit(4)
