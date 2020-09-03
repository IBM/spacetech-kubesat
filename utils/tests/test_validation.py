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
