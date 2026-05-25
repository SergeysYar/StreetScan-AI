"""Lightweight constant-velocity Kalman tracking utilities."""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass
class KalmanConfig:
    """Kalman filter hyper-parameters."""

    dt: float = 0.1
    process_noise: float = 1e-2
    measurement_noise: float = 1e-1


@dataclass
class KalmanTrack:
    """One tracked object state in Kalman form."""

    track_id: int
    state: np.ndarray
    covariance: np.ndarray
    age: int
    missed_frames: int
    class_name: str
    confidence: float | None


class KalmanTracker:
    """Constant-velocity Kalman filter over XYZ positions."""

    def __init__(self, config: KalmanConfig) -> None:
        self.config = config
        dt = config.dt
        self.F = np.array(
            [
                [1, 0, 0, dt, 0, 0],
                [0, 1, 0, 0, dt, 0],
                [0, 0, 1, 0, 0, dt],
                [0, 0, 0, 1, 0, 0],
                [0, 0, 0, 0, 1, 0],
                [0, 0, 0, 0, 0, 1],
            ],
            dtype=float,
        )
        self.H = np.array([[1, 0, 0, 0, 0, 0], [0, 1, 0, 0, 0, 0], [0, 0, 1, 0, 0, 0]], dtype=float)
        self.Q = np.eye(6, dtype=float) * float(config.process_noise)
        self.R = np.eye(3, dtype=float) * float(config.measurement_noise)

    def initialize_track(self, measurement: np.ndarray, track_id: int, class_name: str = "unknown") -> KalmanTrack:
        """Initialize a new track from XYZ measurement."""
        m = np.asarray(measurement, dtype=float).reshape(-1)
        if m.shape[0] != 3 or not np.isfinite(m).all():
            raise ValueError("Measurement must be finite XYZ vector of length 3.")
        state = np.zeros(6, dtype=float)
        state[:3] = m
        cov = np.eye(6, dtype=float)
        return KalmanTrack(track_id=track_id, state=state, covariance=cov, age=1, missed_frames=0, class_name=class_name, confidence=None)

    def predict(self, track: KalmanTrack) -> KalmanTrack:
        """Prediction step: x_k|k-1 = F x_k-1|k-1."""
        track.state = self.F @ track.state
        track.covariance = self.F @ track.covariance @ self.F.T + self.Q
        track.age += 1
        track.missed_frames += 1
        return track

    def update(self, track: KalmanTrack, measurement: np.ndarray) -> KalmanTrack:
        """Update step with XYZ measurement."""
        m = np.asarray(measurement, dtype=float).reshape(-1)
        if m.shape[0] != 3 or not np.isfinite(m).all():
            return track
        y = m - (self.H @ track.state)
        s = self.H @ track.covariance @ self.H.T + self.R
        k = track.covariance @ self.H.T @ np.linalg.inv(s)
        track.state = track.state + (k @ y)
        i = np.eye(6, dtype=float)
        track.covariance = (i - k @ self.H) @ track.covariance
        track.missed_frames = 0
        return track

    def get_position(self, track: KalmanTrack) -> np.ndarray:
        """Return current XYZ position."""
        return track.state[:3].copy()

    def get_velocity(self, track: KalmanTrack) -> np.ndarray:
        """Return current XYZ velocity."""
        return track.state[3:6].copy()
