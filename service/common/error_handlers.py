######################################################################
# Copyright 2016, 2022 John J. Rofrano. All Rights Reserved.
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
######################################################################

"""
Error handlers

Handles all of the HTTP Error Codes returning JSON messages
"""

from flask import current_app as app  # Import Flask application
from service.routes import api
from service.models import DataValidationError, DatabaseConnectionError
from . import status


######################################################################
# Special Error Handlers
######################################################################
@api.errorhandler(DataValidationError)
def request_validation_error(error):
    """Handles Value Errors from bad data"""
    message = str(error)
    app.logger.error(message)
    return {
        "status_code": status.HTTP_400_BAD_REQUEST,
        "error": "Bad Request",
        "message": message,
    }, status.HTTP_400_BAD_REQUEST


@api.errorhandler(DatabaseConnectionError)
def database_connection_error(error):
    """Handles Database Errors from connection attempts"""
    message = str(error)
    app.logger.critical(message)
    return {
        "status_code": status.HTTP_503_SERVICE_UNAVAILABLE,
        "error": "Service Unavailable",
        "message": message,
    }, status.HTTP_503_SERVICE_UNAVAILABLE
