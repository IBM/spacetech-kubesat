# Reinforcement Learning Training Service

RL Training is only used when in training mode. RL Training has two parts. It contains the RL training service which contains the agent and the actual model and then the environment. The environment is how the abstracted nature of the swarm (ie: which nodes are visible) and actions (pointing and mode) get transformed into vectors that the model can use to learn. The environment gets it's observations (the phonebooks and buffered packets from the RL service). 

It also gets its reward (number of buffered packets) from the RL service and gives the action (which node to point at and whether to send or receive) to the RL service. The RL training service uses the agent to run the environment and train the model. It then creates the weights and the trained model so the RL service can use those when in predict mode. 

