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
Pet API Service Test Suite

Test cases can be run with the following:
  nosetests -v --with-spec --spec-color
  coverage report -m
  codecov --token=$CODECOV_TOKEN

  While debugging just these tests it's convenient to use this:
    nosetests --stop tests/test_service.py:TestPetService
"""
import os
from unittest import TestCase
import logging
from urllib.parse import quote_plus
from service import app, routes
from service.utils import status
from service.models import db, init_db, Pet, Gender
from tests.factories import PetFactory

# Disable all but critical errors during normal test run
# uncomment for debugging failing tests
# logging.disable(logging.CRITICAL)

# DATABASE_URI = os.getenv('DATABASE_URI', 'sqlite:///../db/test.db')
DATABASE_URI = os.getenv(
    "DATABASE_URI", "postgresql://postgres:postgres@localhost:5432/testdb"
)
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
        app.config["DEBUG"] = False
        # Set up the test database
        app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_URI
        init_db(app)
        # generate api key for testing
        api_key = routes.generate_apikey()
        app.config['API_KEY'] = api_key
        app.logger.setLevel(logging.CRITICAL)

    @classmethod
    def tearDownClass(cls):
        """Run once after all tests"""
        db.session.close()

    def setUp(self):
        self.client = app.test_client()
        self.headers = {
            'X-Api-Key': app.config['API_KEY']
        }
        db.session.query(Pet).delete()  # clean up the last tests
        db.session.commit()

    def tearDown(self):
        """Clear the database"""
        db.session.remove()

    ############################################################
    # Utility function to bulk create pets
    ############################################################
    def _create_pets(self, count: int = 1) -> list:
        """Factory method to create pets in bulk"""
        pets = []
        for _ in range(count):
            test_pet = PetFactory()
            response = self.client.post(
                BASE_URL,
                json=test_pet.serialize(),
                headers=self.headers
            )
            self.assertEqual(
                response.status_code, status.HTTP_201_CREATED, "Could not create test pet"
            )
            new_pet = response.get_json()
            logging.debug(f"New Pet = {new_pet}")
            test_pet.id = new_pet["id"]
            pets.append(test_pet)
        return pets

    ############################################################
    #  T E S T   C A S E S
    ############################################################
    def test_index(self):
        """In should return the index page"""
        response = self.client.get("/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn(b"Pet Shop", response.data)

    def test_health(self):
        """It should be healthy"""
        response = self.client.get("/health")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.get_json()
        self.assertEqual(data['message'], 'OK')

    # ----------------------------------------------------------
    # TEST LIST
    # ----------------------------------------------------------
    def test_get_pet_list(self):
        """It should Get a list of Pets"""
        self._create_pets(5)
        response = self.client.get(BASE_URL)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.get_json()
        self.assertEqual(len(data), 5)

    # ----------------------------------------------------------
    # TEST READ
    # ----------------------------------------------------------
    def test_get_pet(self):
        """It should Get a single Pet"""
        # get the id of a pet
        test_pet = self._create_pets(1)[0]
        response = self.client.get(f"{BASE_URL}/{test_pet.id}")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.get_json()
        self.assertEqual(data["name"], test_pet.name)

    def test_get_pet_not_found(self):
        """It should not Get a Pet thats not found"""
        response = self.client.get(f"{BASE_URL}/0")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        data = response.get_json()
        logging.debug("Response data = %s", data)
        self.assertIn("was not found", data["message"])

    # ----------------------------------------------------------
    # TEST CREATE
    # ----------------------------------------------------------
    def test_create_pet(self):
        """It should Create a new Pet"""
        test_pet = PetFactory()
        logging.debug("Test Pet: %s", test_pet.serialize())
        response = self.client.post(
            BASE_URL,
            json=test_pet.serialize(),
            headers=self.headers
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Make sure location header is set
        location = response.headers.get("Location", None)
        self.assertIsNotNone(location)

        # Check the data is correct
        new_pet = response.get_json()
        self.assertEqual(new_pet["name"], test_pet.name)
        self.assertEqual(new_pet["category"], test_pet.category)
        self.assertEqual(new_pet["available"], test_pet.available)
        self.assertEqual(new_pet["gender"], test_pet.gender.name)
        self.assertEqual(new_pet["birthday"], test_pet.birthday.isoformat())

        # Check that the location header was correct
        response = self.client.get(location, content_type=CONTENT_TYPE_JSON)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        new_pet = response.get_json()
        self.assertEqual(new_pet["name"], test_pet.name, "Names do not match")
        self.assertEqual(new_pet["category"], test_pet.category)
        self.assertEqual(new_pet["available"], test_pet.available)
        self.assertEqual(new_pet["gender"], test_pet.gender.name)
        self.assertEqual(new_pet["birthday"], test_pet.birthday.isoformat())

    def test_create_pet_with_no_name(self):
        """It should not Create a Pet without a name"""
        pet = self._create_pets()[0]
        new_pet = pet.serialize()
        del new_pet["name"]
        logging.debug("Pet no name: %s", new_pet)
        response = self.client.post(
            BASE_URL,
            json=new_pet,
            headers=self.headers
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_pet_no_content_type(self):
        """It should not Create a Pet with no Content-Type"""
        response = self.client.post(
            BASE_URL,
            data="bad data",
            headers=self.headers
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_pet_wrong_content_type(self):
        """It should not Create a Pet with wrong Content-Type"""
        response = self.client.post(
            BASE_URL,
            data={},
            content_type="plain/text",
            headers=self.headers
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_call_create_with_an_id(self):
        """It should not allow calling endpoint incorrectly"""
        response = self.client.post(
            f"{BASE_URL}/0",
            json={},
            headers=self.headers
        )
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    # ----------------------------------------------------------
    # TEST UPDATE
    # ----------------------------------------------------------
    def test_update_pet(self):
        """It should Update an existing Pet"""
        # create a pet to update
        test_pet = PetFactory()
        response = self.client.post(
            BASE_URL,
            json=test_pet.serialize(),
            headers=self.headers
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # update the pet
        new_pet = response.get_json()
        logging.debug(new_pet)
        new_pet["category"] = "unknown"
        response = self.client.put(
            f"{BASE_URL}/{new_pet['id']}",
            json=new_pet,
            headers=self.headers
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        updated_pet = response.get_json()
        self.assertEqual(updated_pet["category"], "unknown")

    def test_update_pet_with_no_name(self):
        """It should not Update a Pet without assigning a name"""
        pet = self._create_pets()[0]
        pet_data = pet.serialize()
        del pet_data["name"]
        response = self.client.put(
            f"{BASE_URL}/{pet.id}",
            json=pet_data,
            headers=self.headers
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_update_pet_not_found(self):
        """It should not Update a Pet that doesn't exist"""
        response = self.client.put(
            f"{BASE_URL}/0",
            json={},
            headers=self.headers
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_update_pet_not_authorized(self):
        """ It should not Update a Pet Not Authorized """
        pet = self._create_pets()[0]
        pet_data = pet.serialize()
        del pet_data["name"]
        response = self.client.put(f"{BASE_URL}/{pet.id}", json=pet_data)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    # ----------------------------------------------------------
    # TEST DELETE
    # ----------------------------------------------------------
    def test_delete_pet(self):
        """It should Delete a Pet"""
        pets = self._create_pets(5)
        pet_count = self.get_pet_count()
        test_pet = pets[0]
        response = self.client.delete(f"{BASE_URL}/{test_pet.id}", headers=self.headers)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(len(response.data), 0)
        # make sure they are deleted
        response = self.client.get(f"{BASE_URL}/{test_pet.id}")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        new_count = self.get_pet_count()
        self.assertEqual(new_count, pet_count - 1)

    def test_delete_non_existing_pet(self):
        """It should Delete a Pet even if it doesn't exist"""
        response = self.client.delete(f"{BASE_URL}/0", headers=self.headers)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(len(response.data), 0)

    # ----------------------------------------------------------
    # TEST QUERY
    # ----------------------------------------------------------
    def test_query_by_name(self):
        """It should Query Pets by name"""
        pets = self._create_pets(5)
        test_name = pets[0].name
        name_count = len([pet for pet in pets if pet.name == test_name])
        response = self.client.get(
            BASE_URL, query_string=f"name={quote_plus(test_name)}"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.get_json()
        self.assertEqual(len(data), name_count)
        # check the data just to be sure
        for pet in data:
            self.assertEqual(pet["name"], test_name)

    def test_query_by_category(self):
        """It should Query Pets by Category"""
        pets = self._create_pets(5)
        test_category = pets[0].category
        category_count = len([pet for pet in pets if pet.category == test_category])
        response = self.client.get(
            BASE_URL, query_string=f"category={quote_plus(test_category)}"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.get_json()
        self.assertEqual(len(data), category_count)
        # check the data just to be sure
        for pet in data:
            self.assertEqual(pet["category"], test_category)

    def test_query_by_availability(self):
        """It should Query Pets by availability"""
        pets = self._create_pets(10)
        available_pets = [pet for pet in pets if pet.available is True]
        unavailable_pets = [pet for pet in pets if pet.available is False]
        available_count = len(available_pets)
        unavailable_count = len(unavailable_pets)
        logging.debug("Available Pets [%d] %s", available_count, available_pets)
        logging.debug("Unavailable Pets [%d] %s", unavailable_count, unavailable_pets)

        # test for available
        response = self.client.get(
            BASE_URL, query_string="available=true"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.get_json()
        self.assertEqual(len(data), available_count)
        # check the data just to be sure
        for pet in data:
            self.assertEqual(pet["available"], True)

        # test for unavailable
        response = self.client.get(
            BASE_URL, query_string="available=false"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.get_json()
        self.assertEqual(len(data), unavailable_count)
        # check the data just to be sure
        for pet in data:
            self.assertEqual(pet["available"], False)

    def test_query_by_bad_available(self):
        """It should not Query Pets by bad available"""
        response = self.client.get(BASE_URL, query_string="available=bad")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_query_by_gender(self):
        """It should Query Pets by gender"""
        pets = self._create_pets(10)
        female_pets = [pet for pet in pets if pet.gender == Gender.FEMALE]
        female_count = len(female_pets)
        logging.debug("Female Pets [%d] %s", female_count, female_pets)

        # test for gender
        response = self.client.get(BASE_URL, query_string="gender=female")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.get_json()
        self.assertEqual(len(data), female_count)
        # check the data just to be sure
        for pet in data:
            self.assertEqual(pet["gender"], Gender.FEMALE.name)

    def test_query_by_bad_gender(self):
        """It should not Query Pets by bad gender"""
        response = self.client.get(BASE_URL, query_string="gender=bad")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    # ----------------------------------------------------------
    # TEST PURCHASE ACTION
    # ----------------------------------------------------------
    def test_purchase_a_pet(self):
        """It should Purchase a Pet"""
        pets = self._create_pets(10)
        available_pets = [pet for pet in pets if pet.available is True]
        pet = available_pets[0]
        response = self.client.put(f"{BASE_URL}/{pet.id}/purchase", content_type=CONTENT_TYPE_JSON)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response = self.client.get(f"{BASE_URL}/{pet.id}")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.get_json()
        logging.debug("Response data: %s", data)
        self.assertEqual(data["available"], False)

    def test_purchase_not_available(self):
        """It should not Purchase a Pet that is not available"""
        pets = self._create_pets(10)
        unavailable_pets = [pet for pet in pets if pet.available is False]
        pet = unavailable_pets[0]
        response = self.client.put(f"{BASE_URL}/{pet.id}/purchase", content_type=CONTENT_TYPE_JSON)
        self.assertEqual(response.status_code, status.HTTP_409_CONFLICT)

    def test_purchase_does_not_exist(self):
        """It should not Purchase a Pet that doesn't exist"""
        response = self.client.put(f"{BASE_URL}/0/purchase", content_type=CONTENT_TYPE_JSON)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    ######################################################################
    #  P A T C H   A N D   M O C K   T E S T   C A S E S
    ######################################################################

    # @patch("cloudant.client.Cloudant.__init__")
    # def test_connection_error(self, bad_mock):
    #     """Test Connection error handler"""
    #     bad_mock.side_effect = DatabaseConnectionError()
    #     app.config["FLASK_ENV"] = "production"
    #     self.assertRaises(DatabaseConnectionError, routes.init_db, "test")
    #     app.config["FLASK_ENV"] = "development"

    ######################################################################
    # Utility functions
    ######################################################################

    def get_pet_count(self):
        """save the current number of pets"""
        response = self.client.get(BASE_URL)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.get_json()
        # logging.debug("data = %s", data)
        return len(data)
