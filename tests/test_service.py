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

"""
Pet API Service Test Suite

Test cases can be run with the following:
nosetests -v --with-spec --spec-color
nosetests --stop tests/test_service.py:TestPetServer
"""

import unittest
import logging
import json
from service import app, service

# Status Codes
HTTP_200_OK = 200
HTTP_201_CREATED = 201
HTTP_204_NO_CONTENT = 204
HTTP_400_BAD_REQUEST = 400
HTTP_401_NOT_AUTHORIZED = 401
HTTP_404_NOT_FOUND = 404
HTTP_405_METHOD_NOT_ALLOWED = 405
HTTP_409_CONFLICT = 409
HTTP_415_UNSUPPORTED_MEDIA_TYPE = 415

######################################################################
#  T E S T   C A S E S
######################################################################
class TestPetServer(unittest.TestCase):
    """ Pet Service tests """

    @classmethod
    def setUpClass(cls):
        api_key = service.generate_apikey()
        app.config['API_KEY'] = api_key

    def setUp(self):
        self.app = app.test_client()
        self.headers = {
            'X-Api-Key': app.config['API_KEY']
        }
        service.init_db("test")
        service.data_reset()
        service.data_load({"name": "fido", "category": "dog", "available": True})
        service.data_load({"name": "kitty", "category": "cat", "available": True})
        service.data_load({"name": "happy", "category": "hippo", "available": False})

    def test_index(self):
        """ Test the index page """
        resp = self.app.get('/')
        self.assertEqual(resp.status_code, HTTP_200_OK)
        # self.assertIn('Pet Demo REST API Service', resp.data)

    def test_get_pet_list(self):
        """ Get a list of Pets """
        resp = self.app.get('/pets')
        self.assertEqual(resp.status_code, HTTP_200_OK)
        self.assertTrue(len(resp.data) > 0)

    def test_get_pet(self):
        """ Get a single Pet """
        pet = self.get_pet('kitty')[0] # returns a list
        resp = self.app.get('/pets/{}'.format(pet['_id']))
        self.assertEqual(resp.status_code, HTTP_200_OK)
        data = resp.get_json()
        logging.debug('data = %s', data)
        self.assertEqual(data['name'], 'kitty')

    def test_get_pet_not_found(self):
        """ Get a Pet that doesn't exist """
        resp = self.app.get('/pets/0')
        self.assertEqual(resp.status_code, HTTP_404_NOT_FOUND)
        data = resp.get_json()
        logging.debug('data = %s', data)
        self.assertIn('was not found', data['message'])

    def test_create_pet(self):
        """ Create a new Pet """
        # save the current number of pets for later comparrison
        pet_count = self.get_pet_count()
        # add a new pet
        new_pet = {'name': 'sammy', 'category': 'snake', 'available': True}
        resp = self.app.post('/pets', json=new_pet,
                             content_type='application/json',
                             headers=self.headers)
        # if resp.status_code == 429: # rate limit exceeded
        #     sleep(1)                # wait for 1 second and try again
        #     resp = self.app.post('/pets', data=data, content_type='application/json')
        self.assertEqual(resp.status_code, HTTP_201_CREATED)
        # Make sure location header is set
        location = resp.headers.get('Location', None)
        self.assertNotEqual(location, None)
        # Check the data is correct
        new_json = resp.get_json()
        self.assertEqual(new_json['name'], 'sammy')
        # check that count has gone up and includes sammy
        resp = self.app.get('/pets')
        data = resp.get_json()
        logging.debug('data = %s', data)
        self.assertEqual(resp.status_code, HTTP_200_OK)
        self.assertEqual(len(data), pet_count + 1)
        self.assertIn(new_json, data)

    def test_create_pet_with_id(self):
        """ Create a new Pet with an id """
        new_pet = {'_id': 'foo', 'name': 'sammy', 'category': 'snake', 'available': True}
        resp = self.app.post('/pets', json=new_pet,
                             content_type='application/json',
                             headers=self.headers)
        self.assertEqual(resp.status_code, HTTP_201_CREATED)
        data = resp.get_json()
        logging.debug('data = %s', data)
        self.assertEqual(data['name'], 'sammy')
        self.assertNotEqual(data['_id'], 'foo')

    def test_update_pet(self):
        """ Update a Pet """
        pet = self.get_pet('kitty')[0] # returns a list
        self.assertEqual(pet['category'], 'cat')
        pet['category'] = 'tabby'
        # make the call
        resp = self.app.put('/pets/{}'.format(pet['_id']), json=pet,
                            content_type='application/json',
                            headers=self.headers)
        self.assertEqual(resp.status_code, HTTP_200_OK)
        # go back and get it again
        resp = self.app.get('/pets/{}'.format(pet['_id']),
                            content_type='application/json')
        self.assertEqual(resp.status_code, HTTP_200_OK)
        data = resp.get_json()
        logging.debug('data = %s', data)
        self.assertEqual(data['category'], 'tabby')

    def test_update_pet_with_no_name(self):
        """ Update a Pet without assigning a name """
        pet = self.get_pet('fido')[0] # returns a list
        del pet['name']
        resp = self.app.put('/pets/{}'.format(pet['_id']), json=pet,
                            content_type='application/json',
                            headers=self.headers)
        self.assertEqual(resp.status_code, HTTP_400_BAD_REQUEST)

    def test_update_pet_not_found(self):
        """ Update a Pet that doesn't exist """
        new_kitty = {"name": "timothy", "category": "mouse"}
        resp = self.app.put('/pets/0', json=new_kitty,
                            content_type='application/json',
                            headers=self.headers)
        self.assertEqual(resp.status_code, HTTP_404_NOT_FOUND)

    def test_update_pet_not_authorized(self):
        """ Update a Pet Not Authorized """
        pet = self.get_pet('kitty')[0] # returns a list
        self.assertEqual(pet['category'], 'cat')
        pet['category'] = 'tabby'
        # make the call
        resp = self.app.put('/pets/{}'.format(pet['_id']), json=pet,
                            content_type='application/json')
        self.assertEqual(resp.status_code, HTTP_401_NOT_AUTHORIZED)

    def test_delete_pet(self):
        """ Delete a Pet """
        pet = self.get_pet('fido')[0] # returns a list
        logging.debug('Pet = %s', pet)
        # save the current number of pets for later comparrison
        pet_count = self.get_pet_count()
        # delete a pet
        resp = self.app.delete('/pets/{}'.format(pet['_id']),
                               content_type='application/json',
                               headers=self.headers)
        self.assertEqual(resp.status_code, HTTP_204_NO_CONTENT)
        self.assertEqual(len(resp.data), 0)
        new_count = self.get_pet_count()
        self.assertEqual(new_count, pet_count - 1)

    def test_create_pet_with_no_name(self):
        """ Create a Pet without a name """
        new_pet = {'category': 'dog', 'available': True}
        resp = self.app.post('/pets', json=new_pet,
                             content_type='application/json',
                             headers=self.headers)
        self.assertEqual(resp.status_code, HTTP_400_BAD_REQUEST)

    def test_call_create_with_an_id(self):
        """ Invalid call to create passing an id """
        new_pet = {'name': 'sammy', 'category': 'snake'}
        data = json.dumps(new_pet)
        resp = self.app.post('/pets/1', data=data, headers=self.headers)
        self.assertEqual(resp.status_code, HTTP_405_METHOD_NOT_ALLOWED)

    def test_query_by_name(self):
        """ Query Pets by name """
        resp = self.app.get('/pets', query_string='name=fido')
        self.assertEqual(resp.status_code, HTTP_200_OK)
        self.assertTrue(len(resp.data) > 0)
        self.assertIn(b'fido', resp.data)
        self.assertNotIn(b'kitty', resp.data)
        data = resp.get_json()
        logging.debug('data = %s', data)
        query_item = data[0]
        self.assertEqual(query_item['name'], 'fido')

    def test_query_by_category(self):
        """ Query Pets by category """
        resp = self.app.get('/pets', query_string='category=dog')
        self.assertEqual(resp.status_code, HTTP_200_OK)
        self.assertTrue(len(resp.data) > 0)
        self.assertIn(b'fido', resp.data)
        self.assertNotIn(b'kitty', resp.data)
        data = resp.get_json()
        logging.debug('data = %s', data)
        query_item = data[0]
        self.assertEqual(query_item['category'], 'dog')

    def test_query_by_available(self):
        """ Query Pets by availability """
        resp = self.app.get('/pets', query_string='available=true')
        self.assertEqual(resp.status_code, HTTP_200_OK)
        self.assertTrue(len(resp.data) > 0)
        data = resp.get_json()
        logging.debug('data = %s', data)
        self.assertTrue(len(data) == 2)
        query_item = data[0]
        self.assertEqual(query_item['available'], True)

    def test_query_by_not_available(self):
        """ Query Pets by not available """
        resp = self.app.get('/pets', query_string='available=false')
        self.assertEqual(resp.status_code, HTTP_200_OK)
        self.assertTrue(len(resp.data) > 0)
        data = resp.get_json()
        logging.debug('data = %s', data)
        self.assertTrue(len(data) == 1)
        query_item = data[0]
        self.assertEqual(query_item['available'], False)

    def test_purchase_a_pet(self):
        """ Purchase a Pet """
        pet = self.get_pet('fido')[0] # returns a list
        resp = self.app.put('/pets/{}/purchase'.format(pet['_id']),
                            content_type='application/json')
        self.assertEqual(resp.status_code, HTTP_200_OK)
        resp = self.app.get('/pets/{}'.format(pet['_id']),
                            content_type='application/json')
        self.assertEqual(resp.status_code, HTTP_200_OK)
        data = resp.get_json()
        logging.debug('data = %s', data)
        self.assertEqual(data['available'], False)

    def test_purchase_not_available(self):
        """ Purchase a Pet that is not available """
        pet = self.get_pet('happy')[0]
        resp = self.app.put('/pets/{}/purchase'.format(pet['_id']),
                            content_type='application/json')
        self.assertEqual(resp.status_code, HTTP_409_CONFLICT)
        data = resp.get_json()
        logging.debug('data = %s', data)
        self.assertIn('not available', data['message'])


######################################################################
# Utility functions
######################################################################

    def get_pet(self, name):
        """ retrieves a pet for use in other actions """
        resp = self.app.get('/pets',
                            query_string='name={}'.format(name))
        self.assertEqual(resp.status_code, HTTP_200_OK)
        self.assertGreater(len(resp.data), 0)
        data = resp.get_json()
        logging.debug('get_pet(data) = %s', data)
        return data

    def get_pet_count(self):
        """ save the current number of pets """
        resp = self.app.get('/pets')
        self.assertEqual(resp.status_code, HTTP_200_OK)
        data = resp.get_json()
        logging.debug('get_pet_count(data) = %s', data)
        return len(data)


######################################################################
#   M A I N
######################################################################
if __name__ == '__main__':
    unittest.main()
