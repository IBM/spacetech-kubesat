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

import kubesat.orekit as orekit_utils
from kubesat.base_simulation import BaseSimulation
from kubesat.services import ServiceTypes
from kubesat.validation import check_omni_in_range, MessageSchemas, check_internal, SharedStorageSchemas

simulation = BaseSimulation(ServiceTypes.Orbits, SharedStorageSchemas.ORBIT_SERVICE_STORAGE)



@simulation.subscribe_nats_callback("state", MessageSchemas.STATE_MESSAGE)
@check_omni_in_range
async def cubesat_state(message, nats_handler, shared_storage, logger):
    """
    Update the state of a cubesat in the shared dictionary

    Args:
        message (natsmessage): message
            message.data dictionary with structure as described in message_structure.json
            message.data["state"] is a dictionary containing telematry data of a satellite
        nats_handler (natsHandler): distributes callbacks according to the message subject
        shared_storage: dictionary containing information on on the entire swarm, the time, and the particular satellites phonebook
    """
    state = message.data["state"]
    target_sat_id = list(state.keys())[0]
    if orekit_utils.t1_lte_t2_string(shared_storage["swarm"][target_sat_id]["last_update_time"], state[target_sat_id]["last_update_time"]):
        shared_storage["swarm"][target_sat_id] = state[target_sat_id]


@simulation.subscribe_nats_callback("state.attitude", MessageSchemas.ATTITUDE_MESSAGE)
@check_omni_in_range
async def cubesat_X_attitude_provider(message, nats_handler, shared_storage, logger):
    """
    Update the attitude law for a satellite (satellite ID given in the subject of the message) in the shared dictionary

    Args:
        message (natsmessage): message
            message.data dictionary with structure as described in message_structure.json
            message.data["data"]["attitude"] is a dictionary containing what the satellite will point at
        nats_handler (natsHandler): distributes callbacks according to the message subject
        shared_storage: dictionary containing information on on the entire swarm, the time, and the particular satellites phonebook
    """
    attitude = message.data["attitude"]
    satellite_id = message.data["id"]
    new_time = message.data["time"]

    old_attitude_provider_time = shared_storage["swarm"][satellite_id]["last_update_time"]
    if orekit_utils.t1_lte_t2_string(old_attitude_provider_time, new_time):
        shared_storage["swarm"][satellite_id]["orbit"]["attitude"] = attitude


@simulation.subscribe_nats_callback("simulation.timestep", MessageSchemas.TIMESTEP_MESSAGE)
async def simulation_timepulse_propagate(message, nats_handler, shared_storage, logger):
    """
    Propagates the satellites current orbit and attitude

    Args:
        message (natsmessage): message
            message.data dictionary with structure as described in message_structure.json
            message.data["time"] is the time update
        nats_handler (natsHandler): distributes callbacks according to the message subject
        shared_storage: dictionary containing information on on the entire swarm, the time, and the particular satellites phonebook
    """
    # Distance that will prevent satellites from communicating
    max_range = shared_storage["range"]

    # Updating time 
    shared_storage["time"] = message.data["time"]

    cubesat_id = nats_handler.sender_id

    #  Making a propagator for satellite running this service
    self_orbit_propagator = orekit_utils.analytical_propagator(shared_storage["swarm"][cubesat_id]["orbit"])

    # Each satellite's state will be upated and the phonebook will be updated
    for satellite in shared_storage["swarm"]:
        # Info about each satellite state is accessed to propagate orbit and attitude
        orbit_propagator = orekit_utils.analytical_propagator(shared_storage["swarm"][satellite]["orbit"])
        attitude = shared_storage["swarm"][satellite]["orbit"]["attitude"]
        attitude_param = dict()
        frame = shared_storage["swarm"][satellite]["orbit"]["frame"]

        # Info about satellite attitude is accessed
        if attitude in shared_storage["swarm"]:
            attitude_provider_type = orekit_utils.utils.MOVING_BODY_TRACKING
            attitude_param = shared_storage["swarm"][attitude]["orbit"]

        elif attitude in shared_storage["grstns"]:
            attitude_provider_type = orekit_utils.utils.GROUND_TRACKING
            attitude_param = shared_storage["grstns"][attitude]["location"]

        elif attitude in shared_storage["iots"]:
            attitude_provider_type = orekit_utils.utils.GROUND_TRACKING
            attitude_param = shared_storage["iots"][attitude]["location"]

        elif attitude == orekit_utils.utils.NADIR_TRACKING:
            attitude_provider_type = attitude
        else:
            raise Exception("attitude unknown")

        # storing/updating reference frame 
        attitude_param["frame"] = frame
        
        # constructing a attitude provider from info gathered above
        attitude_provider = orekit_utils.attitude_provider_constructor(attitude_provider_type, attitude_param)
       
        # the orbit propagator and attitude provider are consolidated
        orbit_propagator.setAttitudeProvider(attitude_provider)
        
        time = orekit_utils.absolute_time_converter_utc_string(shared_storage["time"])

        # new satellite state containg attitude and orbit info
        new_state = orbit_propagator.propagate(time)

        # the shared storage is updated as necessary
        shared_storage["swarm"][satellite]["orbit"] = orekit_utils.get_keplerian_parameters(new_state)
        shared_storage["swarm"][satellite]["orbit"].update({"frame":frame})
        shared_storage["swarm"][satellite]["orbit"].update({"attitude": attitude})
        shared_storage["swarm"][satellite]["last_update_time"] = shared_storage["time"]

        # Checking if the satellites target is in view and upating shared storage accordingly
        if attitude_provider_type == orekit_utils.utils.GROUND_TRACKING:
            shared_storage["swarm"][satellite]["target_in_view"] = orekit_utils.check_iot_in_range(orbit_propagator,
                                                                    attitude_param["latitude"], attitude_param["longitude"],
                                                                    attitude_param["altitude"], time)
        elif attitude_provider_type == orekit_utils.utils.NADIR_TRACKING:
            shared_storage["swarm"][satellite]["target_in_view"] = True

        elif attitude_provider_type == orekit_utils.utils.MOVING_BODY_TRACKING:
            tracked_propagator = orekit_utils.analytical_propagator(attitude_param)
            shared_storage["swarm"][satellite]["target_in_view"] = orekit_utils.visible_above_horizon(orbit_propagator,
                                                                    tracked_propagator, time)
        else:
            raise Exception("attitude_provider unknown")

        # Updating phonebook based on the location of the satellites
        if satellite != cubesat_id:
            cur_orbit_propagator = orekit_utils.analytical_propagator(shared_storage["swarm"][satellite]["orbit"])

            time = orekit_utils.absolute_time_converter_utc_string(shared_storage["time"])

            distance = orekit_utils.find_sat_distance(self_orbit_propagator, cur_orbit_propagator, time)

            if distance < max_range and orekit_utils.visible_above_horizon(self_orbit_propagator, cur_orbit_propagator, time):
                shared_storage["sat_phonebook"][satellite] = True
            else:
                shared_storage["sat_phonebook"][satellite] = False

    # Message contaning data on the updated state of a satellite is sent for each sent
    for sat_id in shared_storage["swarm"]:
        msg = nats_handler.create_message({"state": {sat_id : shared_storage["swarm"][sat_id]}}, MessageSchemas.STATE_MESSAGE)
        subject = "state"
        await nats_handler.send_message(subject, msg)

    # The satellites updated phonebook is sent
    sat_phonebook_message = nats_handler.create_message(shared_storage["sat_phonebook"], MessageSchemas.PHONEBOOK_MESSAGE)
    await nats_handler.send_message("internal.phonebook", sat_phonebook_message)

    # IOT PHONEBOOK UPDATER
    for iot_id in shared_storage["iots"]:
        latitude = shared_storage["iots"][iot_id]["location"]["latitude"]
        longitude = shared_storage["iots"][iot_id]["location"]["longitude"]
        altitude = shared_storage["iots"][iot_id]["location"]["altitude"]

        if orekit_utils.check_iot_in_range(self_orbit_propagator, latitude, longitude, altitude, orekit_utils.absolute_time_converter_utc_string(shared_storage["time"])):
            shared_storage["iot_phonebook"][iot_id] = True
        else:
            shared_storage["iot_phonebook"][iot_id] = False
    # Sending updated phonebook
    iot_phonebook_message = nats_handler.create_message(shared_storage["iot_phonebook"], MessageSchemas.PHONEBOOK_MESSAGE)
    await nats_handler.send_message("internal.iot_phonebook", iot_phonebook_message)

    #Groundstation Phonebook Updater
    for ground_id in shared_storage["grstns"]:
        latitude = shared_storage["grstns"][ground_id]["location"]["latitude"]
        longitude = shared_storage["grstns"][ground_id]["location"]["longitude"]
        altitude = shared_storage["grstns"][ground_id]["location"]["altitude"]
        if orekit_utils.check_iot_in_range(self_orbit_propagator, latitude, longitude, altitude, orekit_utils.absolute_time_converter_utc_string(shared_storage["time"])):
            shared_storage["grstn_phonebook"][ground_id] = True
        else:
            shared_storage["grstn_phonebook"][ground_id] = False
    # Sending updated phonebook
    grstn_phonebook_message = nats_handler.create_message(shared_storage["grstn_phonebook"], MessageSchemas.PHONEBOOK_MESSAGE)
    await nats_handler.send_message("internal.grnst_phonebook", grstn_phonebook_message)


@simulation.subscribe_nats_callback("command.point", MessageSchemas.POINTING_MESSAGE)
@check_internal
async def cubesat_X_point_to_cubesat_Y(message, nats_handler, shared_storage, logger):
    """
    Updates Attitude Law to point to a specific satellite given its orbit parameters

    Args:
        message (natsmessage): message
            message.data dictionary with structure as described in message_structure.json
            message.data should contain attitude provider information or orbit parameters, or the satellite id
            that needs to be tracked
        nats_handler (natsHandler): distributes callbacks according to the message subject
        shared_storage: dictionary containing information on on the entire swarm, the time, and the particular satellites phonebook
    """

    content = message.data
    cubesat_id = nats_handler.sender_id
    # Only accepts the command if the command is not to point at oneself
    if content != cubesat_id:
        shared_storage["swarm"][cubesat_id]["orbit"]["attitude"] = content
        message = nats_handler.create_message({"time":shared_storage["time"], "attitude":content, "id":cubesat_id}, MessageSchemas.ATTITUDE_MESSAGE)
        await nats_handler.send_message("state.attitude", message)
    else:
        raise Exception("Satellite cannot point to itself.")
    


@simulation.subscribe_nats_callback("internal.rl-action.mode", MessageSchemas.TRANSMISSION_MODE_MESSAGE)
@check_internal
async def update_transmission_mode(message, nats_handler, shared_storage, logger):
    """
    Updates the current transmission mode of the satellite

    Args:
        message (Message): incoming message with new mode
        nats_handler (NatsHandler): NatsHandler used to interact with NATS
        shared_storage (dict): Dictionary to persist memory across callbacks
        logger (JSONLogger): Logger that can be used to log info, error, etc,

    Returns:
        None
    """
    assert message.data == "receiving" or message.data == "sending"
    shared_storage["swarm"][nats_handler.sender_id]["mode"] = message.data
