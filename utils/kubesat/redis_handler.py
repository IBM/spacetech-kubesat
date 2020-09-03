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
