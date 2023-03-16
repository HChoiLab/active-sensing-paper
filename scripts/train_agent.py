"""
A script for training the Bayesian Active Sensor
"""

import torch
import os
from copy import deepcopy
import numpy as np

from envs.active_sensing import mnist_active_sensing
from utils.data import get_mnist_data, get_fashion_mnist

from models import perception
from models.perception import PerceptionModel

from models.action import ActionNetworkStrategy, DirectEvaluationStrategy, RandomActionStrategy

from nets import DecisionNetwork, FFDecisionNetwork, RNNDecisionNetwork

from agents.active_sensor import BayesianActiveSensor

device = 'cuda' if torch.cuda.is_available() else 'cpu'

project_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# create the environment
config = deepcopy(mnist_active_sensing.DEFAULT_CONFIG)
config['batch_size'] = 64
config['val_batch_size'] = 1000
config['n_samples'] = n = 5
config['sample_dim'] = d = 8
config['num_foveated_patches'] = nfov = 1
config['fovea_scale'] = fovsc = 1
config['num_workers'] = 0
config['valid_frac'] = 0.1
config['dataset'] = get_fashion_mnist()
env = mnist_active_sensing.make_env(config)

# create or load the perception model
model_dir = f"../perception_runs/perception_fashionMNIST_n=5_d=8_nfov=1_fovsc=1/last.ckpt"

if model_dir is None:
    z_dim = 32
    s_dim = 64
    d_action = 2
    d_obs = env.observation_space.shape[-1]

    # create the perception model
    vae1_params = perception.DEFAULT_VAE1_PARAMS.copy()
    vae1_params['type'] = 'mlp'
    vae1_params['layers'] = [256, 256]

    vae2_params = {
        'layers': [256, 256],
        'rnn_hidden_size': 512,
        'rnn_num_layers': 1
    }

    perception_model = PerceptionModel(z_dim, s_dim, d_action, d_obs, vae1_params=vae1_params,
                                       vae2_params=vae2_params, lr=0.001, use_latents=True).to(device)
else:
    perception_model = PerceptionModel.load_from_checkpoint(model_dir).to(device)

# create the actor
action_strategy = 'action_network'
action_grid_size = (21, 21)

if action_strategy == 'action_network':
    actor = ActionNetworkStrategy(perception_model, action_grid_size, layers=[64, 32], lr=0.001, out_dist='gaussian',
                                  action_std=0.05)
else:
    actor = DirectEvaluationStrategy(perception_model, action_grid_size)

# create the decider
decision_mode = 'perception'  # options: 'perception', 'raw'
h_layers = [256, 256]
rnn_decider = RNNDecisionNetwork(env.observation_space.shape[-1] - 2,
                                 h_layers,
                                 env.num_classes,
                                 hidden_size=256,
                                 lr=0.001).to(device)
ff_decider = FFDecisionNetwork(perception_model.s_dim,
                               h_layers,
                               env.num_classes,
                               lr=0.001).to(device)

# create the active sensor model
log_dir = f'../runs/bas_perception_fashionMNIST_n={n}_d={d}_nfov={nfov}_fovsc={fovsc}_{action_strategy}_run3'
active_sensor = BayesianActiveSensor(env, perception_model, actor, ff_decider,
                                     log_dir=log_dir, checkpoint_dir=log_dir,
                                     device=device, decider_input=decision_mode)

# train
n_epochs = 200
active_sensor.learn(num_epochs=n_epochs, beta_sched=np.ones((n_epochs,)) * 0.1, num_random_epochs=0,
                    validate_every=3)
