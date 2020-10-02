# Copyright 2020 IBM Corporation
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import asyncio
import unittest
from unittest import TestCase
from time import sleep
import sys
import os
from kubesat.validation import validate_json
from kubesat.validation import MessageSchemas
from kubesat.message import Message
from jsonschema.exceptions import ValidationError

class Test(TestCase):
    def test_validate_message(self):
        """
        validate_message test
        """
        TEST_MESSAGE = {
            "type": "object",
            "additionalProperties": False,
            "required": ["sender_ID", "time_sent", "data"],
            "properties": {
                "sender_ID": {
                    "type": "string",
                },
                "time_sent": {
                    "type": "string"
                },
                "data": {
                    "type": "object",
                    "additionalProperties": False,
                    "required": ["testData"],
                    "properties": {
                        "testData": {
                            "type": "string"
                        }
                    }
                }
            }
        }

        test_message = {
            "sender_ID": "abc",
            "time_sent": "ajfjejfeni49o4904f",
            "data": {
                "testData": "somedata"
            }
        }
        result = validate_json(test_message, TEST_MESSAGE)
        self.assertTrue(result)

        test_message = {
            "sender_ID": "abc",
            "time_sents": "ajfjejfeni49o4904f",
            "data": {
                "testData": "somedata"
            }
        }
        with self.assertRaises(ValidationError):
            result = validate_json(test_message, TEST_MESSAGE)

        test_message = {
            "sender_ID": 2,
            "time_sent": "ajfjejfeni49o4904f",
            "data": {
                "testData": "somedata"
            }
        }
        with self.assertRaises(ValidationError):
            result = validate_json(test_message, TEST_MESSAGE)
