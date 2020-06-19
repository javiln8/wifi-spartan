from stable_baselines import A2C
from stable_baselines.common.policies import MlpLstmPolicy
from stable_baselines.common.vec_env import DummyVecEnv
from tensorflow.python.util import deprecation
import logging

from spartan.smart.learn import Environment
import spartan.smart.state

import os
import numpy as np

# Configure AI logs and disbale other logs
logging.basicConfig(filename='spartan/smart/ai.log',level=logging.DEBUG)
logging.getLogger("requests").setLevel(logging.CRITICAL)
logging.getLogger("urllib3").setLevel(logging.CRITICAL)
logging.getLogger("tensorflow").setLevel(logging.CRITICAL)
logging.getLogger("gym").setLevel(logging.CRITICAL)

# A2C parameters
hyperparameters = {
    'gamma': 0.99,
    'n_steps': 1,
    'vf_coef': 0.25,
    'ent_coef': 0.01,
    'max_grad_norm': 0.5,
    'learning_rate':0.001,
    'alpha': 0.99,
    'epsilon': 0.00001,
    'verbose': 1,
    'lr_schedule': "constant",
}

MODEL_PATH       = 'spartan/smart/brain.nn'
TENSORBOARD_PATH = './spartan/smart/tensorboard'

# Load the AC2 model
def load_model(parameters, agent, state):
    env = Environment(agent, state)
    env = DummyVecEnv([lambda: env])
    logging.info("[smart] Gym environment generated...")

    a2c = A2C(MlpLstmPolicy, env, **hyperparameters, tensorboard_log=TENSORBOARD_PATH)
    logging.info("[smart] A2C created...")

    if os.path.exists(MODEL_PATH):
        a2c.load(MODEL_PATH, env)
        logging.info("[smart] A2C model loaded...")

    return a2c

def featurize(state):
    total_interactions = state['deauths'] + 1e-20

    return np.concatenate((
        [state['misses'] / total_interactions],
        #[state['new_aps'] / total_interactions],
        [state['hops'] / 140],
        [state['deauths'] / total_interactions],
        [state['handshakes'] / total_interactions],
    ))
