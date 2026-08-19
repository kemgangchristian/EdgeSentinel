"""
# *******************************************************
# Chargement et validation de la configuration de l'agent Edge: `config.yaml` correspond à une dataclass Python dédiée.
# *******************************************************
"""

# Permet d'écrire des types comme "int | str" même sur des versions de Python antérieures à 3.10.
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List


@dataclass
class CameraConfig:
    """Correspond à la section `camera:` du fichier YAML."""

    source: int | str
    width: int
    height: int
    target_fps: int


@dataclass
class DetectorConfig:
    """Correspond à la section `detector:` du fichier YAML."""

    model_path: str
    confidence_threshold: float
    # `field(default_factory=list)` plutôt que `= []` : en Python
    classes_of_interest: List[int] = field(default_factory=list)


@dataclass
class TrackerConfig:
    """Correspond à la section `tracker:` du fichier YAML."""

    max_match_distance: float
    max_frames_missing: int


@dataclass
class Zone:
    """Une zone interdite définie par un polygone.

    Représente UNE entrée de la liste `event_engine.zones` du YAML.
    """

    name: str
    # Liste de points (x, y) en pixels formant le contour du polygone.
    polygon: List[tuple[int, int]]


@dataclass
class EventEngineConfig:
    """Correspond à la section `event_engine:` du fichier YAML."""

    zones: List[Zone]
    deduplicate_events: bool
