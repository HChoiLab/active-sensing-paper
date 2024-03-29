import gym
from utils.data import get_mnist_data

# < ---------------------------------  dataset creation and default config ------------------------------------- >

DEFAULT_CONFIG = {

    'n_samples': 6,
    'batch_size': 128,
    'val_batch_size': 128,
    'sample_dim': 8,
    'num_classes': 10,
    'num_foveated_patches': 1,
    'fovea_scale': 2,
    'valid_frac': 0.1,
    'num_workers': 1,
    'dataset': get_mnist_data()

}

# < ---------------------------------  environment registration  ------------------------------------- >

ENV_ID = 'ActiveSensing-v0'

gym.envs.register(ENV_ID, entry_point='envs.entry_points.active_sensing:ActiveSensingEnv')


# < ---------------------------------  env maker   ------------------------------------- >
def make_env(env_config=None):
    if env_config is None:
        return gym.make(ENV_ID, **DEFAULT_CONFIG).unwrapped
    else:
        return gym.make(ENV_ID, **env_config).unwrapped
