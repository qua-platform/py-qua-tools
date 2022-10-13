"""
Dataclass for holding the results after data has been run through the
two-state discriminator.
"""

import numpy as np
from dataclasses import dataclass

@dataclass
class DiscriminatorDataclass:
    """
    Dataclass for holding the results from a two state discriminator run.
    Helper method self.confusion_matrix() generates the confusion matrix from this data.
    """

    # parameters
    angle: float
    threshold: float
    fidelity: float
    gg: np.ndarray
    ge: np.ndarray
    eg: np.ndarray
    ee: np.ndarray

    # data
    ig: np.ndarray
    qg: np.ndarray
    ie: np.ndarray
    qe: np.ndarray

    def __post_init__(self):
        """
        adds rotated data to the dataclass
        @return: None
        """
        self.generate_rotation_data()

    def confusion_matrix(self):
        """
        Generates and returns the 2x2 state confusion matrix
        @return: 2x2 confusion matrix of state fidelity
        """
        return np.array([
            [self.gg, self.ge],
            [self.eg, self.ee]
        ])

    def get_params(self):
        """
        Helper method to quickly obtain useful parameters held in the dataclass
        @return: parameters obtained from the discrimination
        """
        return self.angle, self.threshold, self.fidelity, self.gg, self.ge, self.eg, self.ee

    def get_data(self):
        """
        Helper method to obtain the data stored in the dataclass
        @return: ground and excited state I/Q data.
        """
        return self.ig, self.qg, self.ie, self.qe

    def get_rotated_data(self):
        """
        Helper method to return the rotated (PCA) data from the measurement.
        @return: ground and excited state I/Q data that has been rotated so maximum information is in I plane.
        """
        return self.ig_rotated, self.qg_rotated, self.ie_rotated, self.qe_rotated

    def generate_rotation_data(self):
        """
        Generates the rotated (PCA) data from the measurement.
        @return: None
        """
        C = np.cos(self.angle)
        S = np.sin(self.angle)
        # Condition for having e > Ig
        if np.mean((self.ig - self.ie) * C - (self.qg - self.qe) * S) > 0:
            self.angle += np.pi
            C = np.cos(self.angle)
            S = np.sin(self.angle)

        self.ig_rotated = self.ig * C - self.qg * S
        self.qg_rotated = self.ig * S + self.qg * C
        self.ie_rotated = self.ie * C - self.qe * S
        self.qe_rotated = self.ie * S + self.qe * C
