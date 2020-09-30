import json
from kubesat.validation import validate_json

class Message:
    """
    Class that is used to hold data within the kubesat module. Has attributes to hold data and information
    about message creation and origin
    """

    def __init__(self, schema, sender_ID: str = None, origin_ID: str = None, message_type: str = None, time_sent: str = None, data: dict = None):
        """
        Initializes a new Message instance

        Args:
            schema (dict): Schema do validate the json encoding of the message against
            sender_ID (str, optional): Sender ID of the service sending the message. Defaults to None.
            origin_ID (str, optional): Sender ID of the service creating the message. Defaults to None.
            message_type (str, optional): Type of the message. Defaults to None.
            time_sent (str, optional): ISO string of the time when the message is sent. Defaults to None.
            data (dict, optional): Dictionary holding the data of the message. Defaults to None.
        """        

        self.sender_id = sender_ID
        self.origin_id = origin_ID
        self.message_type = message_type
        self.time_sent = time_sent
        self.data = data
        self.schema = schema

    @classmethod
    def decode_raw(cls, raw_message: bytes, schema: dict):
        """
        Decodes a byte encoded json string into a message object and validate it against a schema. 

        Args:
            raw_message (bytes): Raw message to be decoded.
            schema (dict): Schema to validate the raw message format against.

        Returns:
            Message: New Message instance populated with the decoded raw input.
        """    

        json_message = json.loads(raw_message.decode())
        return cls.decode_json(json_message, schema)

    @classmethod
    def decode_json(cls, json_message: dict, schema: dict):
        """
        Decodes a dict into a message object and validate it against a schema.

        Args:
            json_message (dict): String message to be decoded.
            schema (dict): Schema to validate the raw message format against.

        Returns:
            Message: New Message instance populated with the decoded string input.
        """

        if "origin_ID" not in json_message.keys():
            json_message["origin_ID"] = json_message["sender_ID"]
        if "message_type" not in json_message.keys():
            json_message["message_type"] = "unknown"
            if "name" in schema.keys():
                json_message["message_type"] = schema["name"]
        if not validate_json(json_message, schema):
            return None
        return cls(schema, sender_ID=json_message["sender_ID"], origin_ID=json_message["origin_ID"], message_type=json_message["message_type"], time_sent=json_message["time_sent"], data=json_message["data"])

    def encode_raw(self) -> bytes:
        """
        Creates a byte encoded json string representation of the message and validates it against its schema.

        Returns:
            bytes: Byte representation of the message
        """        

        return json.dumps(self.encode_json()).encode()

    def encode_json(self) -> dict:
        """
        Creates a dict representation of the message and validates it against its schema.

        Returns:
            dict: Dict representation of the message
        """ 

        json_message = {
            "sender_ID": self.sender_id,
            "origin_ID": self.origin_id,
            "message_type": self.message_type,
            "time_sent": self.time_sent,
            "data": self.data
        }
        if not validate_json(json_message, self.schema):
            return None
        return json_message
