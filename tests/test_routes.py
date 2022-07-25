######################################################################
# Copyright 2016, 2021 John J. Rofrano. All Rights Reserved.
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

# spell: ignore Rofrano werkzeug
"""
Pet API Service Test Suite

Test cases can be run with the following:
nosetests -v --with-spec --spec-color
nosetests --stop tests/test_service.py:TestPetServer
"""

import logging
from unittest import TestCase
from unittest.mock import patch
from urllib.parse import quote_plus
from werkzeug.datastructures import MultiDict, ImmutableMultiDict
from service import app, routes
from service.utils import status
from service.routes import DatabaseConnectionError
from tests.factories import PetFactory

# Disable all but critical errors during normal test run
# uncomment for debugging failing tests
logging.disable(logging.CRITICAL)

BASE_URL = "/api/pets"
CONTENT_TYPE_JSON = "application/json"

######################################################################
#  T E S T   C A S E S
######################################################################
class TestPetRoutes(TestCase):
    """Pet Service tests"""

    @classmethod
    def setUpClass(cls):
        """Run once before all tests"""
        app.config["TESTING"] = True
        api_key = routes.generate_apikey()
        app.config['API_KEY'] = api_key
        app.logger.setLevel(logging.CRITICAL)

    def setUp(self):
        self.app = app.test_client()
        self.headers = {
            'X-Api-Key': app.config['API_KEY']
        }
        routes.init_db("test")
        routes.data_reset()

    def tearDown(self):
        """Clear the database"""
        resp = self.app.delete(BASE_URL, headers=self.headers)
        self.assertEqual(resp.status_code, status.HTTP_204_NO_CONTENT)     

    ############################################################
    # Utility function to bulk create pets
    ############################################################
    def _create_pets(self, count: int = 1) -> list:
        """Factory method to create pets in bulk"""
        pets = []
        for _ in range(count):
            test_pet = PetFactory()
            resp = self.app.post(
                BASE_URL, 
                json=test_pet.serialize(), 
                content_type=CONTENT_TYPE_JSON,
                headers=self.headers
            )
            self.assertEqual(
                resp.status_code, status.HTTP_201_CREATED, "Could not create test pet"
            )
            new_pet = resp.get_json()
            test_pet.id = new_pet["_id"]
            pets.append(test_pet)
        return pets


    ############################################################
    #  T E S T   C A S E S
    ############################################################
    def test_index(self):
        """Test the index page"""
        resp = self.app.get("/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertIn(b"Pet Shop", resp.data)

    def test_get_pet_list(self):
        """Get a list of Pets"""
        self._create_pets(5)
        resp = self.app.get(BASE_URL)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertTrue(len(resp.data) > 0)

    def test_get_pet(self):
        """get a single Pet"""
        test_pet = self._create_pets()[0]
        resp = self.app.get(
            f"{BASE_URL}/{test_pet.id}", content_type=CONTENT_TYPE_JSON
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        data = resp.get_json()
        logging.debug("Response data = %s", data)
        self.assertEqual(data["name"], test_pet.name)

    def test_get_pet_not_found(self):
        """Get a Pet that doesn't exist"""
        resp = self.app.get(f"{BASE_URL}/foo")
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)
        data = resp.get_json()
        logging.debug("Response data = %s", data)
        self.assertIn("was not found", data["message"])

    def test_create_pet(self):
        """Create a new Pet"""
        test_pet = PetFactory()
        logging.debug("Test Pet: %s", test_pet.serialize())
        resp = self.app.post(
            BASE_URL, 
            json=test_pet.serialize(), 
            content_type=CONTENT_TYPE_JSON,
            headers=self.headers
        )
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)

        # Make sure location header is set
        location = resp.headers.get("Location", None)
        self.assertIsNotNone(location)

        # Check the data is correct
        new_pet = resp.get_json()
        self.assertEqual(new_pet["name"], test_pet.name)
        self.assertEqual(new_pet["category"], test_pet.category)
        self.assertEqual(new_pet["available"], test_pet.available)
        self.assertEqual(new_pet["gender"], test_pet.gender.name)
        self.assertEqual(new_pet["birthday"], test_pet.birthday.isoformat())

        # Check that the location header was correct
        resp = self.app.get(location, content_type=CONTENT_TYPE_JSON)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        new_pet = resp.get_json()
        self.assertEqual(new_pet["name"], test_pet.name, "Names do not match")
        self.assertEqual(new_pet["category"], test_pet.category)
        self.assertEqual(new_pet["available"], test_pet.available)
        self.assertEqual(new_pet["gender"], test_pet.gender.name)
        self.assertEqual(new_pet["birthday"], test_pet.birthday.isoformat())

    def test_update_pet(self):
        """Update a Pet"""
        # create a pet to update
        test_pet = PetFactory()
        resp = self.app.post(
            BASE_URL, 
            json=test_pet.serialize(), 
            content_type=CONTENT_TYPE_JSON,
            headers=self.headers
        )
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)

        # update the pet
        new_pet = resp.get_json()
        logging.debug(new_pet)
        new_pet["category"] = "unknown"
        resp = self.app.put(
            f"{BASE_URL}/{new_pet['_id']}",
            json=new_pet,
            content_type=CONTENT_TYPE_JSON,
            headers=self.headers
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        updated_pet = resp.get_json()
        self.assertEqual(updated_pet["category"], "unknown")

    def test_update_pet_with_no_name(self):
        """Update a Pet without assigning a name"""
        pet = self._create_pets()[0]
        pet_data = pet.serialize()
        del pet_data["name"]
        resp = self.app.put(
            f"{BASE_URL}/{pet.id}",
            json=pet_data,
            content_type=CONTENT_TYPE_JSON,
            headers=self.headers
        )
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_update_pet_not_found(self):
        """Update a Pet that doesn't exist"""
        resp = self.app.put(
            f"{BASE_URL}/foo", 
            json={}, 
            content_type=CONTENT_TYPE_JSON,
            headers=self.headers
        )
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)

    def test_update_pet_not_authorized(self):
        """ Update a Pet Not Authorized """
        pet = self._create_pets()[0]
        pet_data = pet.serialize()
        del pet_data["name"]
        resp = self.app.put( f"{BASE_URL}/{pet.id}", json=pet_data)
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_delete_pet(self):
        """Delete a Pet"""
        pets = self._create_pets(5)
        pet_count = self.get_pet_count()
        test_pet = pets[0]
        resp = self.app.delete(f"{BASE_URL}/{test_pet.id}", headers=self.headers)
        self.assertEqual(resp.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(len(resp.data), 0)
        # make sure they are deleted
        resp = self.app.get(f"{BASE_URL}/{test_pet.id}")
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)
        new_count = self.get_pet_count()
        self.assertEqual(new_count, pet_count - 1)

    def test_delete_pet(self):
        """Delete All Pets under test only"""
        self._create_pets(1)
        app.config["TESTING"] = False
        resp = self.app.delete(BASE_URL, headers=self.headers)
        self.assertEqual(resp.status_code, status.HTTP_204_NO_CONTENT)
        app.config["TESTING"] = True

    def test_create_pet_with_no_name(self):
        """Create a Pet without a name"""
        pet = self._create_pets()[0]
        new_pet = pet.serialize()
        del new_pet["name"]
        logging.debug("Pet no name: %s", new_pet)
        resp = self.app.post(
            BASE_URL, 
            json=new_pet, 
            content_type=CONTENT_TYPE_JSON,
            headers=self.headers
        )
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_pet_no_content_type(self):
        """Create a Pet with no Content-Type"""
        resp = self.app.post(
            BASE_URL, 
            data="bad data",
            headers=self.headers
        )
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_pet_wrong_content_type(self):
        """Create a Pet with wrong Content-Type"""
        resp = self.app.post(
            BASE_URL, 
            data={}, 
            content_type="plain/text",
            headers=self.headers
        )
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_call_create_with_an_id(self):
        """Call create passing an id"""
        resp = self.app.post(
            f"{BASE_URL}/foo", 
            json={},
            headers=self.headers
        )
        self.assertEqual(resp.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_query_by_name(self):
        """Query Pets by name"""
        pets = self._create_pets(5)
        test_name = pets[0].name
        name_count = len([pet for pet in pets if pet.name == test_name])
        resp = self.app.get(
            BASE_URL, query_string=f"name={quote_plus(test_name)}"
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        data = resp.get_json()
        self.assertEqual(len(data), name_count)
        # check the data just to be sure
        for pet in data:
            self.assertEqual(pet["name"], test_name)

    def test_query_by_category(self):
        """Query Pets by category"""
        pets = self._create_pets(5)
        test_category = pets[0].category
        category_count = len([pet for pet in pets if pet.category == test_category])
        resp = self.app.get(
            BASE_URL, query_string=f"category={quote_plus(test_category)}"
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        data = resp.get_json()
        self.assertEqual(len(data), category_count)
        # check the data just to be sure
        for pet in data:
            self.assertEqual(pet["category"], test_category)


    # test_query_by_availability() does not work because of the way CouchDB
    # handles deletions. Need to upgrade to newer ibmcloudant library

    # def test_query_by_availability(self):
    #     """Query Pets by availability"""
    #     pets = self._create_pets(10)
    #     available_pets = [pet for pet in pets if pet.available is True]
    #     unavailable_pets = [pet for pet in pets if pet.available is False]
    #     available_count = len(available_pets)
    #     unavailable_count = len(unavailable_pets)
    #     logging.debug("Available Pets [%d] %s", available_count, available_pets)
    #     logging.debug("Unavailable Pets [%d] %s", unavailable_count, unavailable_pets)

    #     # test for available
    #     resp = self.app.get(
    #         BASE_URL, query_string="available=true"
    #     )
    #     self.assertEqual(resp.status_code, status.HTTP_200_OK)
    #     data = resp.get_json()
    #     self.assertEqual(len(data), available_count)
    #     # check the data just to be sure
    #     for pet in data:
    #         self.assertEqual(pet["available"], True)

    #     # test for unavailable
    #     resp = self.app.get(
    #         BASE_URL, query_string="available=false"
    #     )
    #     self.assertEqual(resp.status_code, status.HTTP_200_OK)
    #     data = resp.get_json()
    #     self.assertEqual(len(data), unavailable_count)
    #     # check the data just to be sure
    #     for pet in data:
    #         self.assertEqual(pet["available"], False)

    def test_purchase_a_pet(self):
        """Purchase a Pet"""
        pets = self._create_pets(10)
        available_pets = [pet for pet in pets if pet.available is True]
        pet = available_pets[0]
        resp = self.app.put(f"{BASE_URL}/{pet.id}/purchase", content_type=CONTENT_TYPE_JSON)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        resp = self.app.get(f"{BASE_URL}/{pet.id}")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        data = resp.get_json()
        logging.debug("Response data: %s", data)
        self.assertEqual(data["available"], False)

    def test_purchase_not_available(self):
        """Purchase a Pet that is not available"""
        pets = self._create_pets(10)
        unavailable_pets = [pet for pet in pets if pet.available is False]
        pet = unavailable_pets[0]
        resp = self.app.put(f"{BASE_URL}/{pet.id}/purchase", content_type=CONTENT_TYPE_JSON)
        self.assertEqual(resp.status_code, status.HTTP_409_CONFLICT)

    def test_purchase_does_not_exist(self):
        """Purchase a Pet that doesn't exist"""
        resp = self.app.put(f"{BASE_URL}/0/purchase", content_type=CONTENT_TYPE_JSON)
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)


    ######################################################################
    #  P A T C H   A N D   M O C K   T E S T   C A S E S
    ######################################################################

    @patch("cloudant.client.Cloudant.__init__")
    def test_connection_error(self, bad_mock):
        """Test Connection error handler"""
        bad_mock.side_effect = DatabaseConnectionError()
        app.config["FLASK_ENV"] = "production"
        self.assertRaises(DatabaseConnectionError, routes.init_db, "test")
        app.config["FLASK_ENV"] = "development"

    ######################################################################
    # Utility functions
    ######################################################################

    def get_pet_count(self):
        """save the current number of pets"""
        resp = self.app.get(BASE_URL)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        data = resp.get_json()
        # logging.debug("data = %s", data)
        return len(data)
