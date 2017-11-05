######################################################################
# Copyright 2016, 2017 John Rofrano. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the 'License');
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an 'AS IS' BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
######################################################################

"""
Pet Model that uses Redis

You must initlaize this class before use by calling inititlize().
This class looks for an environment variable called VCAP_SERVICES
to get it's database credentials from. If it cannot find one, it
tries to connect to Redis on the localhost. If that fails it looks
for a server name 'redis' to connect to.
"""

import os
import json
import logging
import pickle
from cerberus import Validator
from redis import Redis
from redis.exceptions import ConnectionError

######################################################################
# Custom Exceptions
######################################################################
class DataValidationError(ValueError):
    pass

######################################################################
# Pet Model for database
#   This class must be initialized with use_db(redis) before using
#   where redis is a value connection to a Redis database
######################################################################
class Pet(object):
    """ Pet interface to database """

    logger = logging.getLogger(__name__)
    redis = None
    schema = {
        'id': {'type': 'integer'},
        'name': {'type': 'string', 'required': True},
        'category': {'type': 'string', 'required': True},
        'available': {'type': 'boolean', 'required': True}
        }
    __validator = Validator(schema)

    def __init__(self, id=0, name=None, category=None, available=True):
        """ Constructor """
        self.id = int(id)
        self.name = name
        self.category = category
        self.available = available

    def save(self):
        """ Saves a Pet in the database """
        if self.name is None:   # name is the only required field
            raise DataValidationError('name attribute is not set')
        if self.id == 0:
            self.id = Pet.__next_index()
        Pet.redis.set(Pet.key(self.id), pickle.dumps(self.serialize()))
        self.add_to_category()

    def delete(self):
        """ Deletes a Pet from the database """
        Pet.redis.delete(Pet.key(self.id))
        self.remove_from_category()

    def serialize(self):
        """ serializes a Pet into a dictionary """
        return {
            "id": self.id,
            "name": self.name,
            "category": self.category,
            "available": self.available
        }

    def deserialize(self, data):
        """ deserializes a Pet my marshalling the data """
        if isinstance(data, dict) and Pet.__validator.validate(data):
            self.name = data['name']
            self.category = data['category']
            self.available = data['available']
        else:
            raise DataValidationError('Invalid pet data: ' + str(Pet.__validator.errors))
        return self

######################################################################
#  R E L A T I O N S H I P S
######################################################################

    def add_to_category(self):
        """ Adds the Pets Redis key to a Category set """
        Pet.redis.sadd('category:{}'.format(self.category), Pet.key(self.id))

    def remove_from_category(self):
        """ Removes the Pets Redis key from a Category set """
        Pet.redis.srem('category:{}'.format(self.category), Pet.key(self.id))

######################################################################
#  S T A T I C   D A T A B S E   M E T H O D S
######################################################################

    @staticmethod
    def __next_index():
        """ Increments the index and returns it """
        return Pet.redis.incr(Pet.__name__.lower() + '-index')

    @staticmethod
    def key(value):
        """ Creates a Redis key using class name and value """
        return '{}:{}'.format(Pet.__name__.lower(), value)

    @staticmethod
    def remove_all():
        """ Removes all Pets from the database """
        Pet.redis.flushall()

    @staticmethod
    def all():
        """ Query that returns all Pets """
        # results = [Pet.from_dict(redis.hgetall(key)) for key in redis.keys() if key != 'index']
        results = []
        for key in Pet.redis.keys(Pet.key('*')):
            data = pickle.loads(Pet.redis.get(key))
            pet = Pet(data['id']).deserialize(data)
            results.append(pet)
        return results

######################################################################
#  F I N D E R   M E T H O D S
######################################################################

    @staticmethod
    def find(pet_id):
        """ Query that finds Pets by their id """
        key = Pet.key(pet_id)
        if Pet.redis.exists(key):
            data = pickle.loads(Pet.redis.get(key))
            pet = Pet(data['id']).deserialize(data)
            return pet
        return None

    @staticmethod
    def find_by_category(category):
        """ Query that finds Pets by their category """
        Pet.logger.info('Processing category query for %s ...', category)
        results = []
        for key in Pet.redis.smembers('category:' + category):
            data = pickle.loads(Pet.redis.get(key))
            results.append(Pet(data['id']).deserialize(data))
        return results

######################################################################
#  R E D I S   D A T A B A S E   C O N N E C T I O N   M E T H O D S
######################################################################

    @staticmethod
    def connect_to_redis(hostname, port, password):
        """ Connects to Redis and tests the connection """
        Pet.logger.info("Testing Connection to: %s:%s", hostname, port)
        Pet.redis = Redis(host=hostname, port=port, password=password)
        try:
            Pet.redis.ping()
            Pet.logger.info("Connection established")
        except ConnectionError:
            Pet.logger.info("Connection Error from: %s:%s", hostname, port)
            Pet.redis = None
        return Pet.redis

    @staticmethod
    def init_db(redis=None):
        """
        Initialized Redis database connection

        This method will work in the following conditions:
          1) In Bluemix with Redis bound through VCAP_SERVICES
          2) With Redis running on the local server as with Travis CI
          3) With Redis --link in a Docker container called 'redis'
          4) Passing in your own Redis connection object

        Exception:
        ----------
          redis.ConnectionError - if ping() test fails
        """
        if redis:
            Pet.logger.info("Using client connection...")
            Pet.redis = redis
            try:
                Pet.redis.ping()
                Pet.logger.info("Connection established")
            except ConnectionError:
                Pet.logger.error("Client Connection Error!")
                Pet.redis = None
                raise ConnectionError('Could not connect to the Redis Service')
            return
        # Get the credentials from the Bluemix environment
        if 'VCAP_SERVICES' in os.environ:
            Pet.logger.info("Using VCAP_SERVICES...")
            vcap_services = os.environ['VCAP_SERVICES']
            services = json.loads(vcap_services)
            creds = services['rediscloud'][0]['credentials']
            Pet.logger.info("Conecting to Redis on host %s port %s",
                            creds['hostname'], creds['port'])
            Pet.connect_to_redis(creds['hostname'], creds['port'], creds['password'])
        else:
            Pet.logger.info("VCAP_SERVICES not found, checking localhost for Redis")
            Pet.connect_to_redis('127.0.0.1', 6379, None)
            if not Pet.redis:
                Pet.logger.info("No Redis on localhost, looking for redis host")
                Pet.connect_to_redis('redis', 6379, None)
        if not Pet.redis:
            # if you end up here, redis instance is down.
            Pet.logger.fatal('*** FATAL ERROR: Could not connect to the Redis Service')
            raise ConnectionError('Could not connect to the Redis Service')
