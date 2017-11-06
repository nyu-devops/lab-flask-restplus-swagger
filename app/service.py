######################################################################
# Copyright 2016, 2017 John J. Rofrano. All Rights Reserved.
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
Pet Store Service with Swagger

Paths:
------
GET / - Displays a UI for Selenium testing
GET /pets - Returns a list all of the Pets
GET /pets/{id} - Returns the Pet with a given id number
POST /pets - creates a new Pet record in the database
PUT /pets/{id} - updates a Pet record in the database
DELETE /pets/{id} - deletes a Pet record in the database
"""

import sys
import logging
from flask import jsonify, request, json, url_for, make_response, abort
from flask_api import status    # HTTP Status Codes
from flask_restplus import Api, Resource, fields
from werkzeug.exceptions import NotFound
from app.models import Pet, DataValidationError, DatabaseConnectionError
from . import app

######################################################################
# Configure Swagger before initilaizing it
######################################################################
api = Api(app,
          version='1.0.0',
          title='Pet Demo REST API Service',
          description='This is a sample server Pet store server.',
         )

# This namespace is the start of the path i.e., /pets
ns = api.namespace('pets', description='Pet operations')

# Define the model so that the docs reflect what can be sent
pet_model = api.model('Pet', {
    'id': fields.Integer(readOnly=True,
                         description='The unique id assigned internally by service'),
    'name': fields.String(required=True,
                          description='The name of the Pet'),
    'category': fields.String(required=True,
                              description='The category of Pet (e.g., dog, cat, fish, etc.)'),
    'available': fields.Boolean(required=True,
                                description='Is the Pet avaialble for purchase?')
})

######################################################################
# Special Error Handlers
######################################################################
@api.errorhandler(DataValidationError)
def request_validation_error(error):
    """ Handles Value Errors from bad data """
    message = error.message or str(error)
    app.logger.info(message)
    return {'status':400, 'error': 'Bad Request', 'message': message}, 400

@api.errorhandler(DatabaseConnectionError)
def database_connection_error(error):
    """ Handles Database Errors from connection attempts """
    message = error.message or str(error)
    app.logger.critical(message)
    return {'status':500, 'error': 'Server Error', 'message': message}, 500

######################################################################
# GET HEALTH CHECK
######################################################################
@app.route('/healthcheck')
def healthcheck():
    """ Let them know our heart is still beating """
    return make_response(jsonify(status=200, message='Healthy'), status.HTTP_200_OK)


######################################################################
#  PATH: /pets/{id}
######################################################################
@ns.route('/<int:pet_id>')
@ns.param('pet_id', 'The Pet identifier')
class PetResource(Resource):
    """
    PetResource class

    Allows the manipulation of a single Pet
    GET /pet{id} - Returns a Pet with the id
    PUT /pet{id} - Update a Pet with the id
    DELETE /pet{id} -  Deletes a Pet with the id
    """

    #------------------------------------------------------------------
    # RETRIEVE A PET
    #------------------------------------------------------------------
    @ns.doc('get_pets')
    @ns.response(404, 'Pet not found')
    @ns.marshal_with(pet_model)
    def get(self, pet_id):
        """
        Retrieve a single Pet

        This endpoint will return a Pet based on it's id
        """
        app.logger.info("Request to Retrieve a pet with id [%s]", pet_id)
        pet = Pet.find(pet_id)
        if not pet:
            raise NotFound("Pet with id '{}' was not found.".format(pet_id))
        return pet.serialize(), status.HTTP_200_OK

    #------------------------------------------------------------------
    # UPDATE AN EXISTING PET
    #------------------------------------------------------------------
    @ns.doc('update_pets')
    @ns.response(404, 'Pet not found')
    @ns.response(400, 'The posted Pet data was not valid')
    @ns.expect(pet_model)
    @ns.marshal_with(pet_model)
    def put(self, pet_id):
        """
        Update a Pet

        This endpoint will update a Pet based the body that is posted
        """
        app.logger.info('Request to Update a pet with id [%s]', pet_id)
        check_content_type('application/json')
        pet = Pet.find(pet_id)
        if not pet:
            #api.abort(404, "Pet with id '{}' was not found.".format(pet_id))
            raise NotFound('Pet with id [{}] was not found.'.format(pet_id))
        #data = request.get_json()
        data = api.payload
        app.logger.info(data)
        pet.deserialize(data)
        pet.id = pet_id
        pet.save()
        return pet.serialize(), status.HTTP_200_OK

    #------------------------------------------------------------------
    # DELETE A PET
    #------------------------------------------------------------------
    @ns.doc('delete_pets')
    @ns.response(204, 'Pet deleted')
    def delete(self, pet_id):
        """
        Delete a Pet

        This endpoint will delete a Pet based the id specified in the path
        """
        app.logger.info('Request to Delete a pet with id [%s]', pet_id)
        pet = Pet.find(pet_id)
        if pet:
            pet.delete()
        return '', status.HTTP_204_NO_CONTENT


######################################################################
#  PATH: /pets
######################################################################
@ns.route('/', strict_slashes=False)
class PetCollection(Resource):
    """ Handles all interactions with collections of Pets """
    #------------------------------------------------------------------
    # LIST ALL PETS
    #------------------------------------------------------------------
    @ns.doc('list_pets')
    @ns.param('category', 'List Pets by category')
    @ns.marshal_list_with(pet_model)
    def get(self):
        """ Returns all of the Pets """
        app.logger.info('Request to list Pets...')
        pets = []
        category = request.args.get('category')
        if category:
            pets = Pet.find_by_category(category)
        else:
            pets = Pet.all()

        app.logger.info('[%s] Pets returned', len(pets))
        results = [pet.serialize() for pet in pets]
        return results, status.HTTP_200_OK

    #------------------------------------------------------------------
    # ADD A NEW PET
    #------------------------------------------------------------------
    @ns.doc('create_pets')
    @ns.expect(pet_model)
    @ns.response(400, 'The posted data was not valid')
    @ns.response(201, 'Pet created successfully')
    @ns.marshal_with(pet_model, code=201)
    def post(self):
        """
        Creates a Pet
        This endpoint will create a Pet based the data in the body that is posted
        """
        app.logger.info('Request to Create a Pet')
        check_content_type('application/json')
        pet = Pet()
        app.logger.info('Payload = %s', api.payload)
        pet.deserialize(api.payload)
        pet.save()
        app.logger.info('Pet with new id [%s] saved!', pet.id)
        location_url = api.url_for(PetResource, pet_id=pet.id, _external=True)
        return pet.serialize(), status.HTTP_201_CREATED, {'Location': location_url}


######################################################################
#  PATH: /pets/{id}/purchase
######################################################################
@ns.route('/<int:pet_id>/purchase')
@ns.param('pet_id', 'The Pet identifier')
class PurchaseResource(Resource):
    """ Purchase actions on a Pet """
    @ns.doc('purchase_pets')
    @ns.response(404, 'Pet not found')
    @ns.response(409, 'The Pet is not available for purchase')
    def put(self, pet_id):
        """
        Purchase a Pet

        This endpoint will purchase a Pet and make it unavailable
        """
        app.logger.info('Request to Purchase a Pet')
        pet = Pet.find(pet_id)
        if not pet:
            abort(status.HTTP_404_NOT_FOUND, 'Pet with id [{}] was not found.'.format(pet_id))
        if not pet.available:
            abort(status.HTTP_409_CONFLICT, 'Pet with id [{}] is not available.'.format(pet_id))
        pet.available = False
        pet.save()
        app.logger.info('Pet with id [%s] has been purchased!', pet.id)
        return pet.serialize(), status.HTTP_200_OK


######################################################################
# DELETE ALL PET DATA (for testing only)
######################################################################
@app.route('/pets/reset', methods=['DELETE'])
def pets_reset():
    """ Removes all pets from the database """
    Pet.remove_all()
    return make_response('', status.HTTP_204_NO_CONTENT)

######################################################################
#  U T I L I T Y   F U N C T I O N S
######################################################################

@app.before_first_request
def init_db(redis=None):
    """ Initlaize the model """
    Pet.init_db(redis)

# load sample data
def data_load(payload):
    """ Loads a Pet into the database """
    pet = Pet(0, payload['name'], payload['category'])
    pet.save()

def data_reset():
    """ Removes all Pets from the database """
    Pet.remove_all()

def check_content_type(content_type):
    """ Checks that the media type is correct """
    if request.headers['Content-Type'] == content_type:
        return
    app.logger.error('Invalid Content-Type: %s', request.headers['Content-Type'])
    abort(status.HTTP_415_UNSUPPORTED_MEDIA_TYPE, 'Content-Type must be {}'.format(content_type))

#@app.before_first_request
def initialize_logging(log_level=logging.INFO):
    """ Initialized the default logging to STDOUT """
    if not app.debug:
        print 'Setting up logging...'
        # Set up default logging for submodules to use STDOUT
        # datefmt='%m/%d/%Y %I:%M:%S %p'
        fmt = '[%(asctime)s] %(levelname)s in %(module)s: %(message)s'
        logging.basicConfig(stream=sys.stdout, level=log_level, format=fmt)
        # Make a new log handler that uses STDOUT
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(logging.Formatter(fmt))
        handler.setLevel(log_level)
        # Remove the Flask default handlers and use our own
        handler_list = list(app.logger.handlers)
        for log_handler in handler_list:
            app.logger.removeHandler(log_handler)
        app.logger.addHandler(handler)
        app.logger.setLevel(log_level)
        app.logger.info('Logging handler established')
