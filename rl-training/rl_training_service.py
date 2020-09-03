import gym
import asyncio
from time import sleep
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Dense, Activation, Flatten
from tensorflow.keras.optimizers import Adadelta, SGD, Adam
from rl.agents.dqn import DQNAgent
from rl.policy import BoltzmannQPolicy, EpsGreedyQPolicy
from rl.memory import SequentialMemory
from gym.envs.registration import register
from kubesat.validation import SharedStorageSchemas, MessageSchemas, validate_json
from kubesat.services import ServiceTypes
from kubesat.nats_handler import NatsHandler
from threading import Thread
from multiprocessing import Process

#Find the Gym Environment for the simulation
try:
    register(id='SwarmEnv-v0', entry_point='swarm_env:SwarmEnv', kwargs={"nats": None})
except:
    print("Could not register Swarm Environment with OpenAI gym")


class TrainSimulation:

    def __init__(self, service_type, schema):
        """
        Initializes the training simulation with a service type, schema, and ID.
        """
        self.service_type = service_type
        self.schema = schema
        self.sender_id = None


    def run(self, nats_host="nats", nats_port="4222", nats_user=None, nats_password=None, api_host="127.0.0.1", api_port=8000, redis_host="redis", redis_port=6379, redis_password=None):
        """
        Runs the app with the REST API and NATS client running to train RL Model to create weights for unique simulation. Create a model and agent,
        and runs them in a loop. Interfaces with the OpenAI Gym environment when it is running, the environment then interfaces with the rest of the
        simulation through rl service. Saves the trained weights and models to be used in predict mode.

        Args:
            nats_host (str, optional): NATS server host. Defaults to "0.0.0.0".
            nats_port (str, optional): NATS server port. Defaults to "4222".
            nats_user (str, optional): NATS user. Defaults to "a".
            nats_password (str, optional): NATS password. Defaults to "b".
            api_host (str, optional): Host to run the REST API on. Defaults to "127.0.0.1".
            api_port (int, optional): Port to run the REST API on. Defaults to 8000.
            redis_host (str, optional): Host where Redis runs. Defaults to "redis".
            redis_port (int, optional): Port where Redis runs. Defaults to 6379.
            redis_password (str, optional): Password to acess Redis. Defaults to None.
        """
        # creating NATS client
        nats = NatsHandler("default", host=nats_host, user=nats_user, password=nats_password)
        nats.loop.set_exception_handler(None)
        nats.loop.run_until_complete(nats.connect())

        # getting config from config service
        message = nats.create_message(self.service_type, MessageSchemas.SERVICE_TYPE_MESSAGE)
        config_response =  nats.loop.run_until_complete(nats.request_message("initialize.service", message, MessageSchemas.CONFIG_MESSAGE, timeout=3))

        validate_json(config_response.data["shared_storage"], self.schema)
        sender_id = config_response.data["sender_id"]
        shared_storage = config_response.data["shared_storage"]

        nats.sender_id = sender_id

        ENV_NAME = 'SwarmEnv-v0'
        # Get the environment and extract the number of actions.
        env = gym.make(ENV_NAME, nats=nats)
        #np.random.seed(123)
        #env.seed(123)
        nb_actions = env.action_space.n

        # Next, we build a very simple model.
        model = Sequential()
        model.add(Flatten(input_shape=(1,env.observation_space.n)))
        model.add(Dense(8))
        model.add(Activation('relu'))
        model.add(Dense(8))
        model.add(Activation('relu'))
        model.add(Dense(8))
        model.add(Activation('relu'))
        model.add(Dense(nb_actions))
        model.add(Activation('linear'))
        print(model.summary())
        # Finally, we configure and compile our agent. You can use every built-in tensorflow.keras optimizer and
        # even the metrics!
        memory = SequentialMemory(limit=1000, window_length=1)
        policy = EpsGreedyQPolicy()
        dqn = DQNAgent(model=model, nb_actions=nb_actions, memory=memory, nb_steps_warmup=5,
                target_model_update=1e-2, policy=policy)
        dqn.compile(Adam(lr=1e-3), metrics=['mae'])

        dqn.fit(env, nb_steps=500, visualize=True, verbose=2)

        #Save the weights and model
        dqn.save_weights(f"{shared_storage['weights_location']}/dqn_{ENV_NAME}_weights.h5f", overwrite=True)
        model.save(f"{shared_storage['model_location']}/dqn_{ENV_NAME}_model")
        dqn.test(env, nb_episodes=0, visualize=True)


simulation = TrainSimulation(ServiceTypes.RL_Training, SharedStorageSchemas.RL_TRAINING_SERVICE_STORAGE)
