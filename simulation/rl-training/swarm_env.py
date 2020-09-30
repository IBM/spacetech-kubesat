import gym
from gym import error, spaces, utils
from gym.utils import seeding
import asyncio
import concurrent.futures
import json
import numpy as np
import pandas as pd
import time
import os
from kubesat.nats_handler import NatsHandler
from kubesat.validation import MessageSchemas
import tensorflow as tf

class SwarmEnv(gym.Env):
    """
    Swarm environment that turns the abstraction of the swarm into vectors the model can understand. 
    """
    def __init__(self, nats=None):
        """
        TODO
        """
        self.num_steps = 0
        self.nats = nats
        self.loop = self.nats.loop

        phonebook, iot_phonebook, ground_phonebook, buffered_packets = self.get_data()
        self.cur_state = np.asarray(self.parse_state(phonebook, iot_phonebook, ground_phonebook, buffered_packets))

        self.phonebook_length = len(phonebook)
        self.iot_phonebook_length = len(iot_phonebook)
        self.ground_phonebook_length = len(ground_phonebook)
        self.last_phonebook = None
        self.last_iot_phonebook = None
        self.last_ground_phonebook = None
        self.ids = {}
        self.steps = 0

        counter = 0
        for id in phonebook:
            self.ids[counter] = id
            counter+=1
        for id in iot_phonebook:
            self.ids[counter] = id
            counter+=1
        for id in ground_phonebook:
            self.ids[counter] = id
            counter += 1
        
        self.observation_space = spaces.MultiBinary(self.phonebook_length + self.iot_phonebook_length + self.ground_phonebook_length +1)
        self.action_space = spaces.Discrete((self.phonebook_length + self.iot_phonebook_length + self.ground_phonebook_length)*2)
        

    def parse_state(self, phonebook, iot_phonebook, ground_phonebook, buffered_packets):
        """
        This function turns the phonebooks and the numbered of buffered packets into a vector that can be put into the reinforcement
        learning model. It creates a vector where if the value is 1, the node is in range, and 0 if not, then the last value is the num of buffered packets. 
        Args:
            Phonebook
        Returns:
            state: observation vector for the model
        """
        phonebook_state = np.concatenate((np.asanyarray(list(phonebook.values())).astype(np.int8), np.asanyarray(list(iot_phonebook.values())).astype(np.int8), np.asanyarray(list(ground_phonebook.values())).astype(np.int8)))
        buffer_state = np.asanyarray([buffered_packets > 0]).astype(np.int8)
        state = np.concatenate((phonebook_state, buffer_state))
        return state

    def get_data(self):
        """
        Gets the data (the phonebooks and buffered packets) needed to create the observation vector from the RL service.
        
        """
        message = self.nats.create_message(None, MessageSchemas.RL_MESSAGE)

        # find out how to insert sender id
        response = self.loop.run_until_complete(self.nats.request_message("internal.rl.update." + self.nats.sender_id, message, MessageSchemas.RL_UPDATE_MESSAGE, 3)).data

        return response["phonebook"], response["iot_phonebook"], response["ground_phonebook"], response["buffered_packets"]

    def _get_reward(self):
        """
        Gets the reward from the RL service.
        
      
        """
        message = self.nats.create_message(None, MessageSchemas.RL_MESSAGE)
        reward = self.loop.run_until_complete(self.nats.request_message("internal.rl.reward." + self.nats.sender_id, message, MessageSchemas.RL_REWARD_MESSAGE, 3))
        return reward.data

    def _take_action(self, action):
        """
        Makes the satellite take an action (point at an object and either send or receive). Sends the action to the RL service so it can be acted upon. 
        
        """
        mode = action % 2
        id = int(action / 2)
        id = self.ids[id]
        if mode == 0:
            data = {
            "action": "sending",
            "id": id
            }
            message = self.nats.create_message(data, MessageSchemas.RL_ACTION_MESSAGE)
        elif mode == 1:
            data = {
            "action": "receiving",
            "id": id
            }
            message = self.nats.create_message(data, MessageSchemas.RL_ACTION_MESSAGE)
        self.loop.run_until_complete(self.nats.send_message("internal.rl.action", message))


    def _next_observation(self):
        """
        Moves the observation space forward one step, by getting the newest state (ie: newest phonebooks and number of buffered packets) 
       
        """
        self.steps += 1
        phonebook, iot_phonebook, ground_phonebook, buffered_packets = self.get_data()
        while phonebook == self.last_phonebook and iot_phonebook == self.last_iot_phonebook and ground_phonebook == self.last_ground_phonebook:
            phonebook, iot_phonebook, ground_phonebook, buffered_packets = self.get_data()
            time.sleep(0.05)
        print(f"Buffer: {buffered_packets}")
        self.last_phonebook = phonebook
        self.last_iot_phonebook = iot_phonebook
        self.last_ground_phonebook = ground_phonebook
        self.cur_state = np.asarray(self.parse_state(phonebook, iot_phonebook, ground_phonebook, buffered_packets))
        return self.cur_state

    def step(self, action):
        """
        This takes a RL step. It takes an action and sees what reward is generated by that action. It then gets the new observations (ie: phonebook and buffered packets)
        in order to take the next action and step. This is how the model learns. 
        
        Args:
            action: the action to be taken 
       
        """
        self._take_action(action)
        reward = self._get_reward()
        print(f"Reward: {reward}")
        cur_state = self._next_observation()
        done = False
        if self.steps > 1000:
            self.steps = 0
            done = True
            print("### DONE ###")
        return cur_state, reward, done, {}

    def reset(self):
        """
        Resets the RL model to step 0
      
        """
        if self.num_steps != 0:
            self.num_steps = 0
            print("RESET")
        return self._next_observation()

    def render(self, mode):
        """
        Prints out what step it is on and the observation space
        
 
        """
        print(f"state:{self.cur_state}")
        if self.steps % 100 == 0:
            print(f"Steps: {self.steps}")
