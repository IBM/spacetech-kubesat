import json
import asyncio
from kubesat.message import Message
import czml_utils as gutils
import kubesat.orekit as orekit_utils
from kubesat.base_simulation import BaseSimulation
from kubesat.services import ServiceTypes
from kubesat.validation import MessageSchemas, SharedStorageSchemas

simulation = BaseSimulation(ServiceTypes.Czml, SharedStorageSchemas.GRAPHICS_SERVICE_STORAGE)

# These are hyperparameters, should be fine?
# STEP_COUNT = 5
# STEP_SIZE = 300.0
PACKET_FREQUENCY = 5
# MESSAGE_SENT = False

@simulation.subscribe_nats_callback("state", MessageSchemas.STATE_MESSAGE)
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
    shared_storage["swarm"][target_sat_id] = state[target_sat_id] 

@simulation.subscribe_nats_callback("simulation.timestep", MessageSchemas.TIMESTEP_MESSAGE)
async def send_visualization_packet(message, nats_handler, shared_storage, logger):
    """
    Send packets over NATS describing the state of the swarm. Packets set include ground stations, satellites, and links when pairs 
    are in range.

    Args:
        message (natsmessage): a timestep message
        nats_handler (natsHandler): distributes callbacks according to the message subject
        shared_storage: dictionary containing information on on the entire swarm, the time, and the particular satellites phonebook
    """
    shared_storage["time"] = message.data["time"]

    # Transmit packets on a lower frequency, if desired.
    if shared_storage["packet_frequency_counter"] % PACKET_FREQUENCY != 0:
        shared_storage["packet_frequency_counter"] += 1
        return  
    
    # Create a list of packets to send to Cesium
    czml_list = []
    czml_list.extend(gutils.Generic_CZML(shared_storage["generic"], shared_storage["time"], shared_storage["packet_duration"]).list)
    for i in czml_list:
        subject = "graphics.sat"
        if i["id"] == "document":
	        subject = "graphics.doc"
        message = nats_handler.create_message(i, MessageSchemas.CESIUM_SAT_PACKET)
        sent = await nats_handler.send_message(subject, message)

    start = shared_storage["time"]
    duration = shared_storage["packet_duration"]
    
    # Loop though each ground station and create a packet
    
    for grstn in shared_storage["grstns"]:
        grstn_packet = gutils.CZML_Grstn_Packet(shared_storage["generic"], grstn, start, duration, shared_storage["grstns"][grstn]["location"])
        # czml_list.append(grstn_packet.packet)
        subject = "graphics.grstn"
        message = nats_handler.create_message(grstn_packet.packet, MessageSchemas.CESIUM_GRSTN_PACKET)
        sent = await nats_handler.send_message(subject, message)
    
    # Loop through IoT sensors and create packets

    for iot in shared_storage["iots"]:
        iot_packet = gutils.CZML_Grstn_Packet(shared_storage["generic"], iot, start, duration, shared_storage["iots"][iot]["location"])
        subject = "graphics.iot"
        message = nats_handler.create_message(iot_packet.packet, MessageSchemas.CESIUM_GRSTN_PACKET)
        sent = await nats_handler.send_message(subject, message)
    
    # Loop through satellites, creating satellite packets and links with ground stations

    for sat in shared_storage["swarm"]:

        sat_packet = gutils.CZML_Sat_Packet(shared_storage["generic"], sat, start, duration, shared_storage["swarm"][sat]["orbit"])
        sat_packet.calculate_position(shared_storage["generic"], shared_storage["packet_duration"])
        subject = "graphics.sat"
        message = nats_handler.create_message(sat_packet.packet, MessageSchemas.CESIUM_SAT_PACKET)

        sent = await nats_handler.send_message(subject, message)
        for grstn in shared_storage["grstns"]:
            s2g_packet = gutils.CZML_Sat_2_Grnd_Link_Packet(shared_storage["generic"], sat, grstn, start, shared_storage["swarm"][sat]["orbit"], shared_storage["grstns"][grstn]["location"])
            s2g_packet.update_packet(duration)
            if s2g_packet.packet["availability"]:
                subject = "graphics.grstn2sat"
                message = nats_handler.create_message(s2g_packet.packet, MessageSchemas.CESIUM_GRSTN2SAT_PACKET)
                sent = await nats_handler.send_message(subject, message)
    
    # Generate links between satellites    

    sat_2_sat_packet = gutils.CZML_Sat_2_Sat_Link_Packet(shared_storage, duration)
    sat_2_sat_packet.produce_links(save=False)
    for sat_packet in sat_2_sat_packet.packets:
        subject = "graphics.sat2sat"
        message = nats_handler.create_message(sat_packet, MessageSchemas.CESIUM_SAT2SAT_PACKET)
        sent = await nats_handler.send_message(subject, message)
    shared_storage["packet_frequency_counter"]+=1
