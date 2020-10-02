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

import redis
import json
from kubesat.validation import validate_json

class RedisHandler:
    def __init__(self, service_type, schema, host="redis", port=6379, password=None):
        """
        Creates a redis handler object
        Args:
            service_type: type of service initializing this object
            schema: json schema to validate against
            host: redis host
            port: port redis is running on
            password: redis password
        """
        self.service_type = service_type
        self.schema = schema
        self.redis_client = redis.StrictRedis(host=host, port=port, password=password, decode_responses=True)

    def get_shared_storage(self):
        """
        Gets the shared storage from the redis server for the service.
        Args:
        """
        shared_storage = self.redis_client.get(self.service_type)
        shared_storage = json.loads(shared_storage)
        validate_json(shared_storage, self.schema)
        return shared_storage

    def set_shared_storage(self, shared_storage):
        """
        Sets the shared storage in the redis server for the service.
        """
        validate_json(shared_storage, self.schema)
        shared_storage = json.dumps(shared_storage)
        self.redis_client.set(self.service_type, shared_storage)
        return True

    def get_sender_id(self):
        """
        Returns the id of the redis client
        """
        return self.redis_client.get(f"{self.service_type}_sender_id")

    def set_sender_id(self, sender_id):
        """
        Sets the id of the redis client
        """
        self.redis_client.set(f"{self.service_type}_sender_id", sender_id)
        return True
