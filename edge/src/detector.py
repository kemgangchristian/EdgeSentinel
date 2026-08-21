"""Détection d'objets avec YOLOv8 (Ultralytics, open source AGPL-3.0).

On isole la librairie Ultralytics derrière une petite classe `Detection` et
`YoloDetector` afin que le reste du pipeline (tracker, event_engine) ne
dépende jamais directement d'Ultralytics. Si demain on remplace YOLOv8 par
un modèle ONNX exporté, seul ce fichier change.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import List, Optional

import numpy as np

logger = logging.getLogger(__name__)

# Sous-ensemble des classes du dataset COCO utilisées par YOLOv8 pré-entraîné.
# On ne garde ici que ce qui est utile à un cas d'usage de surveillance.
COCO_CLASS_NAMES = {
    0: "person",
    1: "bicycle",
    2: "car",
    3: "motorcycle",
    5: "bus",
    7: "truck",
    15: "cat",
    16: "dog",
}


@dataclass(frozen=True)
class Detection:
    """Une détection unique retournée par le modèle sur une frame."""

    class_id: int
    label: str
    confidence: float
    # Bounding box au format (x1, y1, x2, y2) en pixels — coin supérieur
    # gauche et coin inférieur droit du rectangle englobant l'objet détecté.
    bbox: tuple[int, int, int, int]

    @property
    def centroid(self) -> tuple[int, int]:
        """Point central de la bounding box — utilisé par le tracker (prochain fichier)
        pour associer les détections d'une frame à l'autre."""
        x1, y1, x2, y2 = self.bbox
        return (x1 + x2) // 2, (y1 + y2) // 2
