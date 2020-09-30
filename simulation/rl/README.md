## Reinforcement Learning Service

Reinforcement learning interfaces with the reinforcement learning environemnt code in the utils. RL service has three modes. It can be used to both put the simulation in training mode and train the model. In training mode, it interfaces with the gym environment in utils and runs the actual agent and model in the rl training service. It can also use the trained model and weights to determine actions for each satellite in the swarm to take. Finally, it has an automatic mode that doesn't use any reinforcement learning but just random choice. These modes can be set in the configuration.

The RL Model takes in as an input the vector of possible places to send/receive data to and whether they are in range or not. The RL Model outputs an action, and the action consists of a target to point at as well as a mode (either sending or receiving) to go into. RL service has the simple use case here of maximizing packets received by groundstations.

Reinforcement Learning Training is only used when in training mode, and creates and runs the DQN agent that actually interfaces with the environment and gym.
