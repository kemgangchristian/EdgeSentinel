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
