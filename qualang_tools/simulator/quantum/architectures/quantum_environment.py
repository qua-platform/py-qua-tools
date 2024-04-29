from typing import Any, Union

import gymnasium as gym
import jax
import numpy as np
from gymnasium import spaces
from gymnasium.core import ObsType
from qiskit import pulse


class QuantumEnvironment(gym.Env):
    def __init__(self, backend, device: str, num_shots=1):
        self.device = device
        jax.config.update("jax_enable_x64", True)
        jax.config.update("jax_platform_name", device)

        self.observation_space = spaces.Box(low=0., high=1.)
        self.action_space = spaces.Box(low=-2., high=2.)

        self.num_shots = num_shots
        self.backend = backend

    def step(self, action):
        num_samples = 215
        schedules = []
        rewards = []

        for a in action:
            gauss = pulse.library.Constant(num_samples, a, limit_amplitude=False)

            with pulse.build() as schedule:
                with pulse.align_sequential():
                    pulse.play(gauss, pulse.DriveChannel(0))
                    pulse.acquire(duration=1, qubit_or_channel=0, register=pulse.MemorySlot(0))

            schedules.append(schedule)

        job = self.backend.run(schedules, shots=self.num_shots)
        job_result = job.result()

        for i in range(len(action)):
            rewards.append(job_result.get_counts(i).get('1', 0) / self.num_shots -
                           job_result.get_counts(i).get('0', 0) / self.num_shots)

        if len(action) == 1:
            reward = np.mean(rewards)
            observation = reward
            terminated = True
        else:
            reward = rewards
            observation = rewards
            terminated = [True] * len(action)

        info = dict()

        return observation, reward, terminated, False, info

    def reset(self, *, seed: Union[int , None] = None, options: Union[dict[str, Any] , None] = None, ) \
            -> tuple[ObsType, dict[str, Any]]:
        self.index = 0
        return [0], dict()

    def _reset(self, **args):
        self.reset()