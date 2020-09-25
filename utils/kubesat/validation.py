import asyncio
from jsonschema import validate
from jsonschema.exceptions import ValidationError


class MessageSchemas:
    """
    JSON Schemas for all the different message types. Used in validating the messages sent.
    Meant to be used on message objects (look at the message class for more info)
    """

    MESSAGE = {
        "name": "message",
        "type": "object",
        "additionalProperties": True,
        "required": ["sender_ID", "time_sent", "origin_ID", "message_type", "data"],
        "properties": {
            "sender_ID": {
                "type": "string",
            },
            "time_sent": {
                "type": "string"
            },
            "origin_ID": {
                "type": "string"
            },
            "message_type": {
                "type": "string"
            }
        }
    }

    CONFIG_MESSAGE = {
        "name": "config_message",
        "type": "object",
        "additionalProperties": False,
        "required": ["sender_ID", "time_sent", "data", "origin_ID", "message_type"],
        "properties": {
            "sender_ID": {
                "type": "string",
            },
            "time_sent": {
                "type": "string"
            },
            "origin_ID": {
                "type": "string"
            },
            "message_type": {
                "type": "string"
            },
            "data": {
                "type": "object"
            }
        }
    }

    API_MESSAGE = {
        "name": "api_message",
        "type": "object",
        "additionalProperties": False,
        "required": ["sender_ID", "time_sent", "data", "origin_ID", "message_type"],
        "properties": {
            "sender_ID": {
                "type": "string",
            },
            "time_sent": {
                "type": "string"
            },
            "origin_ID": {
                "type": "string"
            },
            "message_type": {
                "type": "string"
            },
            "data": {
                "type": "object",
                "additionalProperties": False,
                "required": ["host", "port", "route", "data_id"],
                "properties": {
                    "host": {
                        "type": "string"
                    },
                    "port": {
                        "type": "string"
                    },
                    "route": {
                        "type": "string"
                    },
                    "data_id": {
                        "type": "string"
                    }
                }
            }
        }
    }

    LOG_MESSAGE = {
        "name": "log_message",
        "type": "object",
        "additionalProperties": False,
        "required": ["sender_ID", "time_sent", "data", "origin_ID", "message_type"],
        "properties": {
            "sender_ID": {
                "type": "string",
            },
            "time_sent": {
                "type": "string"
            },
            "origin_ID": {
                "type": "string"
            },
            "message_type": {
                "type": "string"
            },
            "data": {
                "type": "object",
                "additionalProperties": False,
                "required": ["logged_at", "line_number", "function", "level", "msg"],
                "properties": {
                    "logged_at": {
                        "type": "string"
                    },
                    "line_number": {
                        "type": "integer"
                    },
                    "function": {
                        "type": "string"
                    },
                    "level": {
                        "type": "string"
                    },
                    "msg": {
                        "type": "string"
                    }
                }
            }
        }
    }

    TEST_MESSAGE = {
        "name": "test_message",
        "type": "object",
        "additionalProperties": False,
        "required": ["sender_ID", "time_sent", "data", "origin_ID", "message_type"],
        "properties": {
            "sender_ID": {
                "type": "string",
            },
            "time_sent": {
                "type": "string"
            },
            "origin_ID": {
                "type": "string"
            },
            "message_type": {
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

    STATE_MESSAGE = {
        "name": "state_message",
        "type": "object",
        "additionalProperties": False,
        "required": ["sender_ID", "time_sent", "data", "origin_ID", "message_type"],
        "properties": {
            "sender_ID": {
                "type": "string",
            },
            "time_sent": {
                "type": "string"
            },
            "origin_ID": {
                "type": "string"
            },
            "message_type": {
                "type": "string"
            },
            "data": {
                "type": "object"
            }
        }
    }

    STATUS_MESSAGE = {
        "name": "send_data_message",
        "type": "object",
        "additionalProperties": False,
        "required": ["sender_ID", "time_sent", "data", "origin_ID", "message_type"],
        "properties": {
            "sender_ID": {
                "type": "string",
            },
            "time_sent": {
                "type": "string"
            },
            "origin_ID": {
                "type": "string"
            },
            "message_type": {
                "type": "string"
            },
            "data": {
                "type": "string"
            }
        }
    }

    SEND_DATA_MESSAGE = {
        "name": "send_data_message",
        "type": "object",
        "additionalProperties": False,
        "required": ["sender_ID", "time_sent", "data", "origin_ID", "message_type"],
        "properties": {
            "sender_ID": {
                "type": "string",
            },
            "time_sent": {
                "type": "string"
            },
            "origin_ID": {
                "type": "string"
            },
            "message_type": {
                "type": "string"
            },
            "data": {
                "type": "null"
            }
        }
    }

    ORBIT_MESSAGE = {
        "name": "orbit_message",
        "type": "object",
        "additionalProperties": False,
        "required": ["sender_ID", "time_sent", "data", "origin_ID", "message_type"],
        "properties": {
            "sender_ID": {
                "type": "string",
            },
            "time_sent": {
                "type": "string"
            },
            "origin_ID": {
                "type": "string"
            },
            "message_type": {
                "type": "string"
            },
            "data": {
                "type": "object",
                "additionalProperties": False,
                "required": ["id", "orbit", ],
                "properties": {
                    "id": {
                        "type": "string"
                    },
                    "orbit": {
                        "type": "object",
                        "additionalProperties": False,
                        "required": ["eccentricity", "semimajor_axis", "inclination", "perigee_argument", "right_ascension_of_ascending_node", "anomaly", "anomaly_type", "orbit_update_date", "frame", "attitude"],
                        "properties": {
                            "eccentricity": {
                                "type": "number",
                            },
                            "semimajor_axis": {
                                "type": "number",
                            },
                            "inclination": {
                                "type": "number"
                            },
                            "perigee_argument": {
                                "type": "number"
                            },
                            "right_ascension_of_ascending_node": {
                                "type": "number"
                            },
                            "anomaly": {
                                "type": "number"
                            },
                            "anomaly_type": {
                                "type": "string"
                            },
                            "orbit_update_date": {
                                "type": "string"
                            },
                            "frame": {
                                "type": "string"
                            },
                            "attitude": {
                                "type": "string"
                            }
                        }
                    }
                }
            }
        }
    }

    ATTITUDE_MESSAGE = {
        "name": "attitude_message",
        "type": "object",
        "additionalProperties": False,
        "required": ["sender_ID", "time_sent", "data", "origin_ID", "message_type"],
        "properties": {
            "sender_ID": {
                "type": "string",
            },
            "time_sent": {
                "type": "string"
            },
            "origin_ID": {
                "type": "string"
            },
            "message_type": {
                "type": "string"
            },
            "data": {
                "type": "object",
                "additionalProperties": False,
                "required": ["id", "attitude", "time"],
                "properties": {
                    "id": {
                        "type": "string"
                    },
                    "attitude": {
                        "type": "string"
                    },
                    "time": {
                        "type": "string"
                    }
                }
            }
        }
    }

    TIMESTEP_MESSAGE = {
        "name": "timestep_message",
        "type": "object",
        "additionalProperties": False,
        "required": ["sender_ID", "time_sent", "data", "origin_ID", "message_type"],
        "properties": {
            "sender_ID": {
                "type": "string",
            },
            "time_sent": {
                "type": "string"
            },
            "origin_ID": {
                "type": "string"
            },
            "message_type": {
                "type": "string"
            },
            "data": {
                "type": "object",
                "additionalProperties": False,
                "required": ["time"],
                "properties": {
                    "time": {
                        "type": "string"
                    }
                }
            }
        }
    }

    SERVICE_TYPE_MESSAGE = {
        "name": "service_type_message",
        "type": "object",
        "additionalProperties": True,
        "required": ["data"],
        "properties": {
            "data": {
                "type": "string"
            }
        }
    }

    PORT_NO_MESSAGE = {
        "name": "port_no_message",
        "type": "object",
        "additionalProperties": True,
        "required": ["data"],
        "properties": {
            "data": {
                "type": "string"
            }
        }
    }

    CLUSTER_MESSAGE = {
        "name": "cluster_message",
        "type": "object",
        "additionalProperties": False,
        "required": ["sender_ID", "origin_ID", "data", "time_sent", "message_type"],
        "properties": {
            "sender_ID": {
                "type": "string"
            },
            "origin_ID": {
                "type": "string"
            },
            "data": {
                "type": "object"
            },
            "time_sent": {
                "type": "string"
            },
            "message_type": {
                "type": "string"
            }
        }
    }

    POINTING_MESSAGE = {
        "name": "point_message",
        "type": "object",
        "additionalProperties": False,
        "required": ["sender_ID", "time_sent", "data", "origin_ID", "message_type"],
        "properties": {
            "sender_ID": {
                "type": "string",
            },
            "time_sent": {
                "type": "string"
            },
            "data": {
                "type": "string"
            },
            "origin_ID": {
                "type": "string"
            },
            "message_type": {
                "type": "string"
            }
        }
    }

    CUBESAT_POINT_MESSAGE = {
        "name": "point_message",
        "type": "object",
        "additionalProperties": False,
        "required": ["sender_ID", "time_sent", "data", "origin_ID", "message_type"],
        "properties": {
            "sender_ID": {
                "type": "string",
            },
            "time_sent": {
                "type": "string"
            },
            "data": {
                "type": "object"
            },
            "origin_ID": {
                "type": "string"
            },
            "message_type": {
                "type": "string"
            }
        }
    }

    IP_ADDRESS_MESSAGE = {
        "name": "ip_address_message",
        "type": "object",
        "additionalProperties": False,
        "required": ["sender_ID", "time_sent", "data", "origin_ID", "message_type"],
        "properties": {
            "sender_ID": {
                "type": "string",
            },
            "time_sent": {
                "type": "string"
            },
            "data": {
                "type": "string"
            },
            "origin_ID": {
                "type": "string"
            },
            "message_type": {
                "type": "string"
            }
        }
    }

    IOT_LOCATION_MESSAGE = {
        "name": "iot_location_message",
        "type": "object",
        "additionalProperties": False,
        "required": ["sender_ID", "time_sent", "data", "origin_ID", "message_type"],
        "properties": {
            "sender_ID": {
                "type": "string",
            },
            "time_sent": {
                "type": "string"
            },
            "origin_ID": {
                "type": "string"
            },
            "message_type": {
                "type": "string"
            },
            "data": {
                "type": "object",
                "additionalProperties": False,
                "required": ["latitude", "longitude", "altitude"],
                "properties": {
                    "latitude": {
                        "type": "number"
                    },
                    "longitude": {
                        "type": "number"
                    },
                    "altitude": {
                        "type": "number"
                    }
                }
            }
        }
    }

    IOT_DATA_MESSAGE = {
        "name": "iot_data_message",
        "type": "object",
        "additionalProperties": False,
        "required": ["data", "sender_ID", "time_sent", "origin_ID", "message_type"],
        "properties": {
            "data": {
                "type": "number"
            },
            "sender_ID": {
                "type": "string"
            },
            "time_sent": {
                "type": "string"
            },
            "origin_ID": {
                "type": "string"
            },
            "message_type": {
                "type": "string"
            },
        }
    }

    ROUTE_MESSAGE = {
        "name": "route_message",
        "type": "object",
        "additionalProperties": False,
        "required": ["sender_ID", "time_sent", "data", "origin_ID", "message_type"],
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
                "required": ["data_route"],
                "properties": {
                    "data_route": {
                        "type": "string"
                    }
                }
            },
            "origin_ID": {
                "type": "string"
            },
            "message_type": {
                "type": "string"
            }
        }
    }

    APPLICATION_WARNING_MESSAGE = {
        "name": "application_warning_message",
        "type": "object",
        "additionalProperties": False,
        "required": ["time_sent", "sender_ID", "data", "origin_ID", "message_type"],
        "properties": {
            "time_sent": {
                "type": "string"
            },
            "sender_ID": {
                "type": "string"
            },
            "data": {
                "type": "string"
            },
            "origin_ID": {
                "type": "string"
            },
            "message_type": {
                "type": "string"
            }
        }
    }

    IOT_PHONEBOOK_MESSAGE = {
        "name": "iot_phonebook_message",
        "type": "object",
        "additionalProperties": False,
        "required": ["time_sent", "sender_ID", "data", "origin_ID", "message_type"],
        "properties": {
            "time_sent": {
                "type": "string"
            },
            "sender_ID": {
                "type": "string"
            },
            "data": {
                "type": "array"
            },
            "origin_ID": {
                "type": "string"
            },
            "message_type": {
                "type": "string"
            }
        }
    }

    RL_MESSAGE = {
        "name": "rl_message",
        "type": "object",
        "additionalProperties": False,
        "required": ["data", "sender_ID", "time_sent", "origin_ID", "message_type"],
        "properties": {
            "data": {
                "type": "null"
            },
            "sender_ID": {
                "type": "string"
            },
            "time_sent": {
                "type": "string"
            },
            "origin_ID": {
                "type": "string"
            },
            "message_type": {
                "type": "string"
            }
        }
    }

    RL_ACTION_MESSAGE = {
        "type": "object",
        "additionalProperties": False,
        "required": ["data", "sender_ID", "time_sent", "origin_ID", "message_type"],
        "properties": {
            "data": {
                "type": "string",
                "type": "object",
                "additionalProperties": False,
                "required": ["action", "id"],
                "properties": {
                    "action": {
                        "type": "string"
                    },
                    "id": {
                        "type": "string"
                    }
                }
            },
            "sender_ID": {
                "type": "string"
            },
            "time_sent": {
                "type": "string"
            },
            "origin_ID": {
                "type": "string"
            },
            "message_type": {
                "type": "string"
            }
        }
    }

    RL_UPDATE_MESSAGE = {
        "name": "rl_update_message",
        "type": "object",
        "additionalProperties": False,
        "required": ["data", "sender_ID", "time_sent", "origin_ID", "message_type"],
        "properties": {
            "data": {
                "type": "object",
                "additionalProperties": False,
                "required": ["phonebook", "iot_phonebook", "ground_phonebook", "buffered_packets"],
                "properties": {
                    "phonebook": {
                        "type": "object"
                    },
                    "iot_phonebook": {
                        "type": "object"
                    },
                    "ground_phonebook": {
                        "type": "object"
                    },
                    "buffered_packets": {
                        "type": "integer"
                    }
                }
            },
            "sender_ID": {
                "type": "string"
            },
            "time_sent": {
                "type": "string"
            },
            "origin_ID": {
                "type": "string"
            },
            "message_type": {
                "type": "string"
            }
        }
    }

    RL_REWARD_MESSAGE = {
        "name": "rl_reward_message",
        "type": "object",
        "additionalProperties": False,
        "required": ["data", "sender_ID", "time_sent", "origin_ID", "message_type"],
        "properties": {
            "data": {
                "type": "number"
            },
            "sender_ID": {
                "type": "string"
            },
            "time_sent": {
                "type": "string"
            },
            "origin_ID": {
                "type": "string"
            },
            "message_type": {
                "type": "string"
            }
        }
    }

    NUM_MESSAGE = {
        "name": "num_message",
        "type": "object",
        "additionalProperties": False,
        "required": ["data", "sender_ID", "time_sent", "origin_ID", "message_type"],
        "properties": {
            "data": {
                "type": "number"
            },
            "sender_ID": {
                "type": "string"
            },
            "time_sent": {
                "type": "string"
            },
            "origin_ID": {
                "type": "string"
            },
            "message_type": {
                "type": "string"
            }
        }
    }

    PHONEBOOK_MESSAGE = {
        "name": "phonebook_message",
        "type": "object",
        "additionalProperties": False,
        "required": ["time_sent", "sender_ID", "data", "origin_ID", "message_type"],
        "properties": {
            "time_sent": {
                "type": "string"
            },
            "sender_ID": {
                "type": "string"
            },
            "data": {
                "type": "object"
            },
            "origin_ID": {
                "type": "string"
            },
            "message_type": {
                "type": "string"
            }
        }
    }

    GROUND_PHONEBOOK_MESSAGE = {
        "name": "ground_phonebook_message",
        "type": "object",
        "additionalProperties": False,
        "required": ["time_sent", "sender_ID", "data", "origin_ID", "message_type"],
        "properties": {
            "time_sent": {
                "type": "string"
            },
            "sender_ID": {
                "type": "string"
            },
            "data": {
                "type": "object"
            },
            "origin_ID": {
                "type": "string"
            },
            "message_type": {
                "type": "string"
            }
        }
    }

    TRANSMISSION_MODE_MESSAGE = {
        "name": "transmission_mode_message",
        "type": "object",
        "additionalProperties": False,
        "required": ["data", "sender_ID", "time_sent", "origin_ID", "message_type"],
        "properties": {
            "data": {
                "type": "string"
            },
            "sender_ID": {
                "type": "string"
            },

            "data": {
                "type": "string"
            },
            "time_sent": {
                "type": "string"
            },
            "origin_ID": {
                "type": "string"
            },
            "message_type": {
                "type": "string"
            }
        }
    }

    BUFFER_MESSAGE = {
        "name": "buffer_message",
        "type": "object",
        "additionalProperties": False,
        "required": ["data", "sender_ID", "time_sent", "origin_ID", "message_type"],
        "properties": {
            "data": {
                "type": "integer"
            },
            "sender_ID": {
                "type": "string"
            },
            "time_sent": {
                "type": "string"
            },
            "origin_ID": {
                "type": "string"
            },
            "message_type": {
                "type": "string"
            }
        }
    }

    CESIUM_GRSTN_PACKET = {
        "name": "cesium_groundstation_packet",
        "type": "object",
        "additionalProperties": False,
        "required": ["data", "sender_ID", "time_sent", "origin_ID", "message_type"],
        "properties": {
            "data": {
                "type": "object"
            },
            "sender_ID": {
                "type": "string"
            },
            "time_sent": {
                "type": "string"
            },
            "origin_ID": {
                "type": "string"
            },
            "message_type": {
                "type": "string"
            }
        }
    }

    CESIUM_SAT_PACKET = {
        "name": "cesium_sat_packet",
        "type": "object",
        "additionalProperties": False,
        "required": ["data", "sender_ID", "time_sent", "origin_ID", "message_type"],
        "properties": {
            "data": {
                "type": "object"
            },
            "sender_ID": {
                "type": "string"
            },
            "time_sent": {
                "type": "string"
            },
            "origin_ID": {
                "type": "string"
            },
            "message_type": {
                "type": "string"
            }
        }
    }

    CESIUM_SAT2SAT_PACKET = {
        "name": "cesium_sat2sat_packet",
        "type": "object",
        "additionalProperties": False,
        "required": ["data", "sender_ID", "time_sent", "origin_ID", "message_type"],
        "properties": {
            "data": {
                "type": "object"
            },
            "sender_ID": {
                "type": "string"
            },
            "time_sent": {
                "type": "string"
            },
            "origin_ID": {
                "type": "string"
            },
            "message_type": {
                "type": "string"
            }
        }
    }

    CESIUM_GRSTN2SAT_PACKET = {
        "name": "cesium_grstn2sat_packet",
        "type": "object",
        "additionalProperties": False,
        "required": ["data", "sender_ID", "time_sent", "origin_ID", "message_type"],
        "properties": {
            "data": {
                "type": "object"
            },
            "sender_ID": {
                "type": "string"
            },
            "time_sent": {
                "type": "string"
            },
            "origin_ID": {
                "type": "string"
            },
            "message_type": {
                "type": "string"
            }
        }
    }


class SharedStorageSchemas:
    """
    Json schemas for the shared storage dictionaries used by each microservice. Meant to validate
    that the shared storages from the config files have the right structure to be used by each service. 
    """

    STORAGE = {
        "type": "object",
        "additionalProperties": True
    }

    TEMPLATE_STORAGE = {
        "type": "object",
        "additionalProperties": False,
        "required": ["test_value"],
        "properties": {
            "test_value": {
                "type": "string",
            }
        }
    }

    LOGGING_SERVICE_STORAGE = {
        "type": "object",
        "additionalProperties": False,
        "required": ["log_path"],
        "properties": {
            "log_path": {
                "type": "string",
            }
        }
    }

    RL_TRAINING_SERVICE_STORAGE = {
        "type": "object",
        "additionalProperties": False,
        "required": ["model_location", "weights_location"],
        "properties": {
            "model_location": {
                "type": "string",
            },
            "weights_location": {
                "type": "string"
            }
        }
    }

    CLOCK_SERVICE_STORAGE = {
        "type": "object",
        "additionalProperties": False,
        "required": ["start_time", "time_step"],
        "properties": {
            "time_step": {
                "type": "number",
            },
            "start_time": {
                "type": "string"
            }
        }
    }

    ORBIT_SERVICE_STORAGE = {
        "type": "object",
        "additionalProperties": False,
        "required": ["sat_phonebook", "iot_phonebook", "swarm", "time", "range", "grstns", "iots"],
        "properties": {
            "sat_phonebook": {
                "type": "object"
            },
            "iot_phonebook": {
                "type": "object"
            },
            "grstns": {
                "type": "object"
            },
            "iots": {
                "type": "object"
            },
            "grstn_phonebook": {
                "type": "object"
            },
            "swarm": {
                "type": "object",
            },
            "time": {
                "type": "string"
            },
            "range": {
                "type": "number"
            }
        }
    }

    IOT_SERVICE_STORAGE = {
        "type": "object",
        "additionalProperties": False,
        "required": ["latitude", "longitude", "altitude", "pointing", "data_rate"],
        "properties": {
            "latitude": {
                "type": "number"
            },
            "longitude": {
                "type": "number"
            },
            "altitude": {
                "type": "number"
            },
            "pointing": {
                "type": "array",
                "items": {
                    "type": "string"
                }
            },
            "data_rate": {
                "type": "integer"
            },
            "timestep": {
                "type": "number"
            }
        }
    }

    GROUND_STATION_SERVICE_STORAGE = {
        "type": "object",
        "additionalProperties": False,
        "required": ["latitude", "longitude", "altitude", "pointing", "packets_received", "ip_map", "ip_cluster_map"],
        "properties": {
            "latitude": {
                "type": "number"
            },
            "longitude": {
                "type": "number"
            },
            "altitude": {
                "type": "number"
            },
            "pointing": {
                "type": "array",
                "items": {
                    "type": "string"
                }
            },
            "packets_received": {
                "type": "integer"
            },
            "ip_map": {
                "type": "object"
            },
            "ip_cluster_map": {
                "type": "object"
            }
        }
    }

    DATA_SERVICE_STORAGE = {
        "type": "object",
        "additionalProperties": False,
        "required": ["pointing", "mode", "pointing_to", "data_rate", "timestep"],
        "properties": {
            "pointing": {
                "type": "array",
                "items": {
                    "type": "string"
                }
            },
            "mode": {
                "type": "string"
            },
            "pointing_to": {
                "type": "string"
            },
            "data_rate": {
                "type": "integer"
            },
            "timestep": {
                "type": "number"
            }
        }
    }

    CONFIG_SERVICE_STORAGE = {
        "type": "object",
        "additionalProperties": False,
        "required": ["config_path", "cubesats", "iots", "simulation", "groundstations"],
        "properties": {
            "simulation": {
                "type": "object"
            },
            "cubesats": {
                "type": "object"
            },
            "iots": {
                "type": "object"
            },
            "groundstations": {
                "type": "object"
            },
            "config_path": {
                "type": "string"
            }
        }
    }

    APPLICATION_SERVICE_STORAGE = {
        "type": "object",
        "additionalProperties": False,
        "required": ["data_rate"],
        "properties": {
            "data_rate": {
                "type": "integer"
            }
        }
    }

    CLUSTER_SERVICE_STORAGE = {
        "type": "object",
        "additionalProperties": False,
        "required": [],
        "properties": {
        }
    }

    RL_SERVICE_STORAGE = {
        "type": "object",
        "additionalProperties": False,
        "required": ["phonebook", "iot_phonebook", "ground_phonebook", "buffered_packets", "packets_received", "mode", "weights_location", "new_phonebook", "new_iot_phonebook", "new_ground_phonebook", "model_location"],
        "properties": {
            "phonebook": {
                "type": "object"
            },
            "iot_phonebook": {
                "type": "object"
            },
            "ground_phonebook": {
                "type": "object",
            },
            "buffered_packets": {
                "type": "number"
            },
            "packets_received": {
                "type": "object"
            },
            "last_buffered_packets": {
                "type": "number"
            },
            "mode": {
                "type": "string"
            },
            "weights_location": {
                "type": "string"
            },
            "model_location": {
                "type": "string"
            },
            "new_phonebook": {
                "type": "boolean"
            },
            "new_iot_phonebook": {
                "type": "boolean"
            },
            "new_ground_phonebook": {
                "type": "boolean"
            }


        }
    }

    GRAPHICS_SERVICE_STORAGE = {
        "type": "object",
        "additionalProperties": False,
        "required": ["swarm", "grstns", "iots", "time", "range", "packet_duration", "packet_frequency_counter", "generic"],
        "properties": {
            "swarm": {
                "type": "object"
            },
            "grstns": {
                "type": "object"
            },
            "iots": {
                "type": "object"
            },
            "time": {
                "type": "string"
            },
            "range": {
                "type": "number"
            },
            "packet_duration": {
                "type": "number",
            },
            "packet_frequency_counter": {
                "type": "number"
            },
            "generic": {
                "type": "object"
            }
        }
    }


def validate_json(data, schema):
    """
    Validates a json dictionary according to the schemas
    Args:
        data: json dictionary
        schema: json schema
    """
    # TODO: Adapt to overarching exception handling strategy
    validate(instance=data, schema=schema)
    return True


def check_omni_in_range(callback_function):
    """
    Check to see if sender is in range
    Args:
        callback_function (function): callback function to be called
    """
    async def decorator(msg, nats, shared_storage, logger):
        id = msg.sender_id
        if shared_storage["sat_phonebook"][id]:
            await callback_function(msg, nats, shared_storage, logger)
    return decorator


def check_pointing(callback_function):
    """
    Check to see whether the message comes from an object pointing at an object

    Args:
        callback_function (function): Callback function to be called
    """
    async def decorator(msg, nats, shared_storage, logger):
        if msg.sender_id in shared_storage["pointing"]:
            await callback_function(msg, nats, shared_storage, logger)
    return decorator


def check_pointing_data(msg, nats, shared_storage, logger):
    """
    Check to see whether the message comes from an object pointing at an object

    Args:
        msg: nats message
        nats: nats handler object
        shared_storage: shared storage dictionary
        logger: logger object
    """

    if msg.sender_id in shared_storage["pointing"]:
        return True
    return False


def check_pointing_and_mode(msg, nats, shared_storage, logger):
    """
    Check to see whether the two nodes are pointing at each other and that the
    mode is receiving

    Args:
        msg: nats message
        nats: nats handler object
        shared_storage: shared storage dictionary
        logger: logger object
    """
    if msg.sender_id in shared_storage["pointing"] and shared_storage["mode"] == "receiving" and msg.sender_id == shared_storage["pointing_to"]:
        return True
    return False


def check_internal(callback_function):
    """
    Check to see whether the message comes the same origin (ie: in the same node)

    Args:
        callback_function (function): Callback function to be called
    """
    async def decorator(msg, nats, shared_storage, logger):
        if msg.origin_id == nats.sender_id:
            await callback_function(msg, nats, shared_storage, logger)
    return decorator


def check_internal_data(msg, nats, shared_storage, logger):
    """
    Check to see whether the message comes the same origin (ie: in the same node)

    Args:
        msg: nats message
        nats: nats handler object
        shared_storage: shared storage dictionary
        logger: logger object
    """
    if msg.sender_id == nats.sender_id:
        return True
    return False
