from spartan.smart import state
from spartan.utils import post
import spartan.smart

import gym
from gym import spaces
import numpy as np
import logging

# Parameters to optimize while learning
class Parameter(object):
    def __init__(self, name, value=0.0, min_value=0, max_value=2, channel=None, trainable=True):
        self.name = name
        self.channel = channel
        self.value = value
        self.min_value = min_value
        self.max_value = max_value + 1

        if self.min_value < 0:
            self.scale_factor = abs(self.min_value)
        elif self.min_value > 0:
            self.scale_factor = -self.min_value
        else:
            self.scale_factor = 0

    # Size of the parameter space
    def space_size(self):
        return self.max_value + self.scale_factor

    # Value function
    def parameter_to_value(self, policy):
        self.value = policy - self.scale_factor
        return int(self.value)

# OpenAI custom Gym Environment
class Environment(gym.Env):
    metadata = {'render.modes': ['human']}
    parameters = [
        Parameter('min_rssi', min_value=-200, max_value=-50),
        Parameter('ap_ttl', min_value=30, max_value=600),
        Parameter('station_ttl', min_value=60, max_value=300),
        Parameter('recon_time', min_value=10, max_value=60),
        Parameter('hop_recon_time', min_value=10, max_value=60),
        Parameter('min_recon_time', min_value=5, max_value=30),
    ]

    def __init__(self, agent, state):
        super(Environment, self).__init__()
        self.agent = agent
        self.state = state
        self.epoch_number = 0
        self.wifi_channels = 140
        self.observation_shape = (1,4) # 4: handshakes, misses, hops, deauths, new_aps
        self.reward_range = (-.7, 1.02)
        self.cache_state = None
        self.cache_render = None

        for channel in range(self.wifi_channels):
            Environment.parameters += [Parameter('channel_' + str(channel), min_value=0, max_value=1, channel=channel + 1)]

        # OpenAI Gym spaces
        self.action_space = spaces.MultiDiscrete([p.space_size() for p in Environment.parameters])
        self.observation_space = spaces.Box(low=0, high=1, shape=self.observation_shape, dtype=np.float32)

        self.last = {
            'reward': 0.0,
            'policy': None,
            'parameters': {},
            'state': None,
            'vectorized_state': None
        }

    # Update the model parameters given a optimization policy
    def update_parameters(policy):
        parameters = {}
        channels = []

        assert len(Environment.parameters) == len(policy)

        for i in range(len(policy)):
            parameter = Environment.parameters[i]
            if 'channel' not in parameter.name:
                parameters[parameter.name] = parameter.parameter_to_value(policy[i])
            else:
                has_channel = parameter.parameter_to_value(policy[i])
                channel = parameter.channel
                if has_channel:
                    channels.append(channel)

        parameters['channels'] = channels

        return parameters

    # Perform a iteration of the agent-environment loop
    def step(self, policy):
        new_parameters          = Environment.update_parameters(policy)
        self.last['policy']     = policy
        self.last['parameters'] = new_parameters

        # Agent performs the action
        self.agent.apply_policy(new_parameters)
        self.epoch_number += 1

        while (True):
            # Wait for state data in parallel
            if self.state.state_data and self.cache_state != self.state.state:
                logging.info('[smart] State data: ' + str(self.state.state_data))

                self.last['reward'] = self.state.state_data['reward']
                self.last['state'] = self.state.state_data
                self.last['vectorized_state'] = spartan.smart.featurize(self.last['state'])

                self.agent.model.env.render()
                self.agent.save_model()

                self.cache_state = self.state.state

                return self.last['vectorized_state'], self.last['reward'], False, {}

    # Reset the environment
    def reset(self):
        logging.info("[smart] Resetting the environment...")
        self.epoch_number = 0
        if self.state.state_data:
            self.last['state'] = self.state.state_data
            self.last['vectorized_state'] = spartan.smart.featurize(self.state.state_data)

        return self.last['vectorized_state']

    # Output environment data
    def render(self, mode='human', close=False, force=False):
        if self.cache_render == self.epoch_number:
            return

        self.cache_render = self.epoch_number

        logging.info('[smart] Training epoch: ' + str(self.epoch_number)) #self._agent.training_epochs()))')
        logging.info('[smart] Reward: ' + str(self.last['reward']))
        #print('Policy: ' + join("%s:%s" % (name, value) for name, value in self.last['parameters'].items())))

# Train the AI using A2C policy optimization
class Trainer(object):
    def __init__(self, parameters):
        self.parameters = parameters
        self.model = None

    def train(self):
        epochs_per_state = 50

        self.model = spartan.smart.load_model(self.parameters, self, self.state)

        observations = None
        while True:
            self.model.env.render()
            logging.info('[smart] Learning for ' + str(epochs_per_state) + ' epochs.')
            self.model.learn(total_timesteps=epochs_per_state, callback=self.model.env.render())

            if not observations:
                observations = self.model.env.reset()
                
            action, _ = self.model.predict(observations)
            observations, _, _, _ = self.model.env.step(action)

    # Save the A2C model
    def save_model(self):
        logging.info('[smart] Saving model')
        self.model.save(spartan.smart.MODEL_PATH)

    # Apply new parameters
    def apply_policy(self, new_parameters):
        logging.info('[smart] Updating parameters with the new policy.')
        for name, new_value in new_parameters.items():
            if name in self.parameters:
                current_value = self.parameters[name]

                # Update the parameter value
                if current_value != new_value:
                    self.parameters[name] = new_value
                    logging.info('[smart] Updating ' + str(name)+ ': ' + str(new_value))

        post('set wifi.ap.ttl ' + str(self.parameters['ap_ttl']))
        post('set wifi.sta.ttl ' + str(self.parameters['station_ttl']))
        post('set wifi.rssi.min ' + str(self.parameters['min_rssi']))
