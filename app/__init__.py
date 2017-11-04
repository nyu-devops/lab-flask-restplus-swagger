"""
Microservice module

This module contains the microservice code for
    service
    models
"""
from flask import Flask

# Create the Flask aoo
app = Flask(__name__)
app.config.from_object('config')

# Service needs app so must be placed after app is created
import service
import models
