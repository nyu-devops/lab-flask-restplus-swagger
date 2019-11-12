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
import uuid
import logging
from functools import wraps
from flask import jsonify, request, url_for, make_response
from flask_api import status    # HTTP Status Codes
from flask_restplus import Api, Resource, fields, reqparse, inputs
from service.models import Pet, DataValidationError, DatabaseConnectionError
from . import app

# Document the type of autorization required
authorizations = {
    'apikey': {
        'type': 'apiKey',
        'in': 'header',
        'name': 'X-Api-Key'
    }
}

######################################################################
# Configure Swagger before initilaizing it
######################################################################
api = Api(app,
          version='1.0.0',
          title='Pet Demo REST API Service',
          description='This is a sample server Pet store server.',
          default='pets',
          default_label='Pet shop operations',
          doc='/', # default also could use doc='/apidocs/'
          authorizations=authorizations
          # prefix='/api'
         )

# Define the model so that the docs reflect what can be sent
pet_model = api.model('Pet', {
    '_id': fields.String(readOnly=True,
                         description='The unique id assigned internally by service'),
    'name': fields.String(required=True,
                          description='The name of the Pet'),
    'category': fields.String(required=True,
                              description='The category of Pet (e.g., dog, cat, fish, etc.)'),
    'available': fields.Boolean(required=True,
                                description='Is the Pet avaialble for purchase?')
})

create_model = api.model('Pet', {
    'name': fields.String(required=True,
                          description='The name of the Pet'),
    'category': fields.String(required=True,
                              description='The category of Pet (e.g., dog, cat, fish, etc.)'),
    'available': fields.Boolean(required=True,
                                description='Is the Pet avaialble for purchase?')
})

# query string arguments
pet_args = reqparse.RequestParser()
pet_args.add_argument('name', type=str, required=False, help='List Pets by name')
pet_args.add_argument('category', type=str, required=False, help='List Pets by category')
pet_args.add_argument('available', type=inputs.boolean, required=False, help='List Pets by availability')

######################################################################
# Special Error Handlers
######################################################################
@api.errorhandler(DataValidationError)
def request_validation_error(error):
    """ Handles Value Errors from bad data """
    message = str(error)
    app.logger.error(message)
    return {
        'status_code': status.HTTP_400_BAD_REQUEST,
        'error': 'Bad Request',
        'message': message
    }, status.HTTP_400_BAD_REQUEST

@api.errorhandler(DatabaseConnectionError)
def database_connection_error(error):
    """ Handles Database Errors from connection attempts """
    message = str(error)
    app.logger.critical(message)
    return {
        'status_code': status.HTTP_503_SERVICE_UNAVAILABLE,
        'error': 'Service Unavailable',
        'message': message
    }, status.HTTP_503_SERVICE_UNAVAILABLE


######################################################################
# Authorization Decorator
######################################################################
def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        if 'X-Api-Key' in request.headers:
            token = request.headers['X-Api-Key']

        if app.config.get('API_KEY') and app.config['API_KEY'] == token:
            return f(*args, **kwargs)
        else:
            return {'message': 'Invalid or missing token'}, 401
    return decorated


######################################################################
# Function to generate a random API key (good for testing)
######################################################################
def generate_apikey():
    """ Helper function used when testing API keys """
    return uuid.uuid4().hex


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
@api.route('/pets/<pet_id>')
@api.param('pet_id', 'The Pet identifier')
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
    @api.doc('get_pets')
    @api.response(404, 'Pet not found')
    @api.marshal_with(pet_model)
    def get(self, pet_id):
        """
        Retrieve a single Pet

        This endpoint will return a Pet based on it's id
        """
        app.logger.info("Request to Retrieve a pet with id [%s]", pet_id)
        pet = Pet.find(pet_id)
        if not pet:
            api.abort(status.HTTP_404_NOT_FOUND, "Pet with id '{}' was not found.".format(pet_id))
        return pet.serialize(), status.HTTP_200_OK

    #------------------------------------------------------------------
    # UPDATE AN EXISTING PET
    #------------------------------------------------------------------
    @api.doc('update_pets', security='apikey')
    @api.response(404, 'Pet not found')
    @api.response(400, 'The posted Pet data was not valid')
    @api.expect(pet_model)
    @api.marshal_with(pet_model)
    @token_required
    def put(self, pet_id):
        """
        Update a Pet

        This endpoint will update a Pet based the body that is posted
        """
        app.logger.info('Request to Update a pet with id [%s]', pet_id)
        pet = Pet.find(pet_id)
        if not pet:
            api.abort(status.HTTP_404_NOT_FOUND, "Pet with id '{}' was not found.".format(pet_id))
        app.logger.debug('Payload = %s', api.payload)
        data = api.payload
        pet.deserialize(data)
        pet.id = pet_id
        pet.save()
        return pet.serialize(), status.HTTP_200_OK

    #------------------------------------------------------------------
    # DELETE A PET
    #------------------------------------------------------------------
    @api.doc('delete_pets', security='apikey')
    @api.response(204, 'Pet deleted')
    @token_required
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
@api.route('/pets', strict_slashes=False)
class PetCollection(Resource):
    """ Handles all interactions with collections of Pets """
    #------------------------------------------------------------------
    # LIST ALL PETS
    #------------------------------------------------------------------
    @api.doc('list_pets')
    @api.expect(pet_args, validate=True)
    @api.marshal_list_with(pet_model)
    def get(self):
        """ Returns all of the Pets """
        app.logger.info('Request to list Pets...')
        pets = []
        args = pet_args.parse_args()
        if args['category']:
            app.logger.info('Filtering by category: %s', args['category'])
            pets = Pet.find_by_category(args['category'])
        elif args['name']:
            app.logger.info('Filtering by name: %s', args['name'])
            pets = Pet.find_by_name(args['name'])
        elif args['available'] is not None:
            app.logger.info('Filtering by availability: %s', args['available'])
            pets = Pet.find_by_availability(args['available'])
        else:
            pets = Pet.all()

        app.logger.info('[%s] Pets returned', len(pets))
        results = [pet.serialize() for pet in pets]
        return results, status.HTTP_200_OK


    #------------------------------------------------------------------
    # ADD A NEW PET
    #------------------------------------------------------------------
    @api.doc('create_pets', security='apikey')
    @api.expect(create_model)
    @api.response(400, 'The posted data was not valid')
    @api.response(201, 'Pet created successfully')
    @api.marshal_with(pet_model, code=201)
    @token_required
    def post(self):
        """
        Creates a Pet
        This endpoint will create a Pet based the data in the body that is posted
        """
        app.logger.info('Request to Create a Pet')
        pet = Pet()
        app.logger.debug('Payload = %s', api.payload)
        pet.deserialize(api.payload)
        pet.create()
        app.logger.info('Pet with new id [%s] saved!', pet.id)
        location_url = api.url_for(PetResource, pet_id=pet.id, _external=True)
        return pet.serialize(), status.HTTP_201_CREATED, {'Location': location_url}


######################################################################
#  PATH: /pets/{id}/purchase
######################################################################
@api.route('/pets/<pet_id>/purchase')
@api.param('pet_id', 'The Pet identifier')
class PurchaseResource(Resource):
    """ Purchase actions on a Pet """
    @api.doc('purchase_pets')
    @api.response(404, 'Pet not found')
    @api.response(409, 'The Pet is not available for purchase')
    def put(self, pet_id):
        """
        Purchase a Pet

        This endpoint will purchase a Pet and make it unavailable
        """
        app.logger.info('Request to Purchase a Pet')
        pet = Pet.find(pet_id)
        if not pet:
            api.abort(status.HTTP_404_NOT_FOUND, 'Pet with id [{}] was not found.'.format(pet_id))
        if not pet.available:
            api.abort(status.HTTP_409_CONFLICT, 'Pet with id [{}] is not available.'.format(pet_id))
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
def init_db(dbname="pets"):
    """ Initlaize the model """
    Pet.init_db(dbname)

# load sample data
def data_load(payload):
    """ Loads a Pet into the database """
    pet = Pet(payload['name'], payload['category'], payload['available'])
    pet.save()

def data_reset():
    """ Removes all Pets from the database """
    Pet.remove_all()
