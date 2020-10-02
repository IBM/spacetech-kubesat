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

import numpy as np
from gym import spaces
from rl.agents.dqn import DQNAgent
from rl.memory import SequentialMemory
from tensorflow.keras.models import load_model
from rl.policy import EpsGreedyQPolicy
from tensorflow.keras.optimizers import Adam
from kubesat.base_simulation import BaseSimulation
from kubesat.services import ServiceTypes
from kubesat.validation import MessageSchemas, check_internal, SharedStorageSchemas
import random

simulation = BaseSimulation(ServiceTypes.RL, SharedStorageSchemas.RL_SERVICE_STORAGE)
agents = []

@simulation.startup_callback
async def initialize_rl(nats_handler, shared_storage, logger):
    """
    Callback used to initialize the agent and model for the reinforcement learning and put it in the list.
    First checks shared storage to see if the satellite is in predict mode or training mode, if it is in
    predict mode it uses the phonebooks to create an input vector to the reinforcement learning model. This
    input vector consists of all possible nodes that the satellite could send or receive data from. The callbacks
    then loads the trained model and weights, and creates a new agent and appends it to the agent list so that
    other callbacks can access the agent.

    Args:
        nats_handler (NatsHandler): NatsHandler used to interact with NATS
        shared_storage (dict): Dictionary to persist memory across callbacks
        logger (JSONLogger): Logger that can be used to log info, error, etc,
    """
    if shared_storage["mode"] == "predict":
        memory = SequentialMemory(limit=1000, window_length=1)
        policy = EpsGreedyQPolicy()
        nb_actions = (len(shared_storage["phonebook"]) + len(shared_storage["iot_phonebook"]) + len(shared_storage["ground_phonebook"]))*2
        model = load_model(shared_storage["model_location"])
        rl_agent = DQNAgent(model=model, nb_actions=nb_actions, memory=memory, nb_steps_warmup=5,
                    target_model_update=1e-2, policy=policy)
        rl_agent.compile(Adam(lr=1e-3), metrics=['mae'])
        rl_agent.load_weights(shared_storage["weights_location"])
        agents.append(rl_agent)

@simulation.subscribe_nats_callback("simulation.timestep", MessageSchemas.TIMESTEP_MESSAGE)
async def rl_step(message, nats_handler, shared_storage, logger):
    """
    Callback used to take a 'rl step'. It observes when the phonebooks have changed (ie: when other nodes pass in or out of range), and then feeds a
    vectorized version of the phonebooks to the rl model in order to determine the output action. This method then calls an action to be done by the satellite,
    a node to point at and whether to send or receive data. It broadcasts this action to be picked up by the data and orbit service.  Only used when in predict mode.

    Args:
        message (Message): incoming message with current pointing target of the sender
        nats_handler (NatsHandler): NatsHandler used to interact with NATS
        shared_storage (dict): Dictionary to persist memory across callbacks
        logger (JSONLogger): Logger that can be used to log info, error, etc,
    """
    if shared_storage["mode"] == "predict" and (shared_storage["new_phonebook"] or shared_storage["new_iot_phonebook"] or shared_storage["new_ground_phonebook"]):
        shared_storage["new_phonebook"] = False
        shared_storage["new_iot_phonebook"] = False
        shared_storage["new_ground_phonebook"] = False
        rl_agent = agents[0]
        ob = []
        ids =[]
        for sat in shared_storage["phonebook"].keys():
            ob.append(shared_storage["phonebook"][sat])
            ids.append(sat)
        for iot in shared_storage["iot_phonebook"].keys():
            ob.append(shared_storage["iot_phonebook"][iot])
            ids.append(iot)
        for ground in shared_storage["ground_phonebook"].keys():
            ob.append(shared_storage["ground_phonebook"][ground])
            ids.append(ground)
        ob.append(shared_storage["buffered_packets"] > 100)
        obs = np.asarray(ob).astype(np.int8)
        action = rl_agent.forward(obs)
        mode = action % 2
        id = int(action / 2)
        id = ids[id]
        if mode == 0:
            data = {
            "action": "sending",
            "id": id
            }
            message = nats_handler.create_message(data, MessageSchemas.RL_ACTION_MESSAGE)
        elif mode == 1:
            data = {
            "action": "receiving",
            "id": id
            }
            message = nats_handler.create_message(data, MessageSchemas.RL_ACTION_MESSAGE)
        return await nats_handler.send_message("internal.rl.action", message)
    elif shared_storage["mode"] == "auto" and (shared_storage["new_phonebook"] or shared_storage["new_iot_phonebook"] or shared_storage["new_ground_phonebook"]):
        shared_storage["new_phonebook"] = False
        shared_storage["new_iot_phonebook"] = False
        shared_storage["new_ground_phonebook"] = False
        targets = []
        iot_key = 0
        for iot in shared_storage["iot_phonebook"].keys():
            if shared_storage["iot_phonebook"][iot] == True:
                targets.append(iot)
        for sat in shared_storage["phonebook"].keys():
            if shared_storage["phonebook"][sat] == True and sat != nats_handler.sender_id:
                targets.append(sat)
        for ground in shared_storage["ground_phonebook"].keys():
            if shared_storage["ground_phonebook"][ground] == True:
                targets.append(ground)
        if len(targets) != 0:
            target = random.choice(targets)
            if "iot" in target:
                action = "receiving"
            elif "groundstation" in target:
                action = "sending"
            else:
                action = random.choice(["sending", "receiving"])
                
            data = {
                "action": action,
                "id": target
            }
            message = nats_handler.create_message(data, MessageSchemas.RL_ACTION_MESSAGE)
            return await nats_handler.send_message("internal.rl.action", message)
    else:
        return False

@simulation.subscribe_nats_callback("internal.iot_phonebook", MessageSchemas.PHONEBOOK_MESSAGE)
@check_internal
async def update_iot_phonebook(message, nats_handler, shared_storage, logger):
    """
    Callback used to update the internal knowledge of which iot sensors are in range. Receives broadcasts from orbit service that contain the new iot phonebooks.
     Updates the iot phonebook if it is different, and sets the shared storage variable new_iot_phonebook to True, to inform the other callbacks there is a new iot phonebook.

    Args:
        message (Message): incoming message with current pointing target of the sender
        nats_handler (NatsHandler): NatsHandler used to interact with NATS
        shared_storage (dict): Dictionary to persist memory across callbacks
        logger (JSONLogger): Logger that can be used to log info, error, etc,
    """

    if message.data != shared_storage["iot_phonebook"]:
        shared_storage["new_iot_phonebook"] = True
        shared_storage["iot_phonebook"] = message.data

@simulation.subscribe_nats_callback("internal.grnst_phonebook", MessageSchemas.PHONEBOOK_MESSAGE)
@check_internal
async def update_grstn_phonebook(message, nats_handler, shared_storage, logger):
    """
    Callback used to update the internal knowledge of which ground stations are in range. Receives broadcasts from orbit service that contain the new ground phonebooks.
    Updates the ground phonebook if it is different, and sets the shared storage variable new_ground_phonebook to True, to inform the other callbacks there is a new ground phonebook.

    Args:
        message (Message): incoming message with current pointing target of the sender
        nats_handler (NatsHandler): NatsHandler used to interact with NATS
        shared_storage (dict): Dictionary to persist memory across callbacks
        logger (JSONLogger): Logger that can be used to log info, error, etc,
    """

    if message.data != shared_storage["ground_phonebook"]:
        shared_storage["new_ground_phonebook"] = True
        shared_storage["ground_phonebook"] = message.data

@simulation.subscribe_nats_callback("internal.phonebook", MessageSchemas.PHONEBOOK_MESSAGE)
@check_internal
async def update_phonebook(message, nats_handler, shared_storage, logger):
    """
    Callback used to update the internal knowledge of which satellites are in range

    Args:
        message (Message): incoming message with current pointing target of the sender
        nats_handler (NatsHandler): NatsHandler used to interact with NATS
        shared_storage (dict): Dictionary to persist memory across callbacks
        logger (JSONLogger): Logger that can be used to log info, error, etc,
    """
    if message.data != shared_storage["phonebook"]:
        shared_storage["new_phonebook"] = True
        shared_storage["phonebook"] = message.data

@simulation.subscribe_nats_callback("internal.buffer_size", MessageSchemas.BUFFER_MESSAGE)
@check_internal
async def update_buffered_packets(message, nats_handler, shared_storage, logger):
    """
    Callback used to update the internal knowledge of how many packets are currently in the sats buffer

    Args:
        message (Message): incoming message with current pointing target of the sender
        nats_handler (NatsHandler): NatsHandler used to interact with NATS
        shared_storage (dict): Dictionary to persist memory across callbacks
        logger (JSONLogger): Logger that can be used to log info, error, etc,
    """
    shared_storage["last_buffered_packets"] = shared_storage["buffered_packets"]
    shared_storage["buffered_packets"] = message.data

@simulation.subscribe_nats_callback("groundstation.packets_received", MessageSchemas.BUFFER_MESSAGE)
async def update_packets_received(message, nats_handler, shared_storage, logger):
    """
    Callback used to update the internal knowledge of how many packets a ground station has received so far.
    Receives a message from a groundstation, then adds the number of packets received from that individual groundstation to the total number of packets received.
    Keeps track of packets received for all different groundstations.
    Args:
        message (Message): incoming message with current pointing target of the sender
        nats_handler (NatsHandler): NatsHandler used to interact with NATS
        shared_storage (dict): Dictionary to persist memory across callbacks
        logger (JSONLogger): Logger that can be used to log info, error, etc,
    """

    shared_storage["packets_received"][message.origin_id] += message.data

@simulation.request_nats_callback("internal.rl.update.", MessageSchemas.RL_MESSAGE, append_sender_id=True)
async def update_rl(message, nats_handler, shared_storage, logger):
    """
    Request callback used to reply with the current information of available objects and internal buffer size, which
    represents the input of the RL model.

    Args:
        message (Message): incoming message with current pointing target of the sender
        nats_handler (NatsHandler): NatsHandler used to interact with NATS
        shared_storage (dict): Dictionary to persist memory across callbacks
        logger (JSONLogger): Logger that can be used to log info, error, etc,
    """
    if shared_storage["mode"] == "train":
        data = {
            "phonebook": shared_storage["phonebook"],
            "iot_phonebook": shared_storage["iot_phonebook"],
            "ground_phonebook": shared_storage["ground_phonebook"],
            "buffered_packets": shared_storage["buffered_packets"]
        }
        for key in shared_storage["packets_received"].keys():
            shared_storage["packets_received"][key] = 0
        return nats_handler.create_message(data, MessageSchemas.RL_UPDATE_MESSAGE)
    return

@simulation.request_nats_callback("internal.rl.reward.", MessageSchemas.RL_MESSAGE, append_sender_id=True)
async def give_reward(message, nats_handler, shared_storage, logger):
    """
    Request callback used to reply with the total number of packets received by ground stations divided by
    a scaling factor, representing the current reward for the RL model. The request message comes from the DQN when
    in training mode, it uses packets received as well as the number of buffered packets to calculate the reward, then sends the reward as a response back to the DQN.

    Args:
        message (Message): incoming message with current pointing target of the sender
        nats_handler (NatsHandler): NatsHandler used to interact with NATS
        shared_storage (dict): Dictionary to persist memory across callbacks
        logger (JSONLogger): Logger that can be used to log info, error, etc,
    """
    if shared_storage["mode"] == "train":
        packets_received = 0
        for value in shared_storage["packets_received"].values():
            packets_received += value * 10
            if value == 0:
                packets_received -= 3
        delta = shared_storage["buffered_packets"] - shared_storage["last_buffered_packets"]
        if delta > 0:
            packets_received += delta * 0.25
        for key in shared_storage["packets_received"].keys():
            shared_storage["packets_received"][key] = 0
        return nats_handler.create_message(packets_received, MessageSchemas.RL_REWARD_MESSAGE)
    return

@simulation.subscribe_nats_callback("internal.rl.action", MessageSchemas.RL_ACTION_MESSAGE)
@check_internal
async def take_action(message, nats_handler, shared_storage, logger):
    """
    Request callback used to reply with the total number of packets received by ground stations divided by
    a scaling factor, representing the current reward for the RL model. The request message comes from the DQN when
    in training mode, it uses packets received as well as the number of buffered packets to calculate the reward, then sends the reward as a response back to the DQN. 

    Args:
        message (Message): incoming message with current pointing target of the sender
        nats_handler (NatsHandler): NatsHandler used to interact with NATS
        shared_storage (dict): Dictionary to persist memory across callbacks
        logger (JSONLogger): Logger that can be used to log info, error, etc,
    """
    data = message.data["action"]
    to_point_id = message.data["id"]
    if to_point_id != nats_handler.sender_id:
        mode_message = nats_handler.create_message(data, MessageSchemas.TRANSMISSION_MODE_MESSAGE)
        await nats_handler.send_message("internal.rl-action.mode", mode_message)
        point_message = nats_handler.create_message(to_point_id, MessageSchemas.POINTING_MESSAGE)
        sent = await nats_handler.send_message("command.point", point_message)
