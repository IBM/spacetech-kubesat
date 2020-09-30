import asyncio
from kubesat.nats_logger import NatsLoggerFactory
from unittest import IsolatedAsyncioTestCase
from kubesat.message import Message

class FakeNatsHandler:
    """
    TODO
    """
    def __init__(self):
        """
        TODO
        """
        self.out = {}
        self.sender_id = "1"

    def create_message(self, data, schema):
        """
        TODO
        """
        return Message.decode_json({
            "sender_ID": self.sender_id,
            "time_sent": "sometime",
            "data": data
        }, schema)
    
    async def send_message(self, channel, message):
        """
        TODO
        """
        if channel not in self.out.keys():
            self.out[channel] = []
        self.out[channel].append(message)
        return True

class Test(IsolatedAsyncioTestCase):
    """
    TODO
    """
    async def test_logger(self):
        """
        TODO
        """
        fake_nats = FakeNatsHandler()
        logger = NatsLoggerFactory.get_logger(fake_nats, "test")
        await logger.info("this is a test")
        self.assertEqual(len(fake_nats.out["logging.test.1"]), 1)
