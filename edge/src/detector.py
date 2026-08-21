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


class YoloDetector:
    """Encapsule un modèle YOLOv8 pour produire une liste de `Detection`."""

    def __init__(
        self,
        model_path: str,
        confidence_threshold: float = 0.5,
        classes_of_interest: Optional[List[int]] = None,
    ):
        # Import DIFFÉRÉ (lazy import), volontaire : Ultralytics et sa
        # dépendance PyTorch sont des librairies lourdes (plusieurs centaines
        # de Mo, plusieurs secondes de chargement). En les important ici,
        # à l'INTÉRIEUR du constructeur, plutôt qu'en haut du fichier, on
        # évite de payer ce coût dès qu'on fait un simple `import detector`
        # — par exemple dans nos tests unitaires du tracker ou de
        # l'event_engine, qui n'ont jamais besoin d'un vrai modèle YOLO.
        from ultralytics import YOLO

        logger.info("Chargement du modèle YOLO: %s", model_path)
        self._model = YOLO(model_path)
        self._confidence_threshold = confidence_threshold
        self._classes_of_interest = classes_of_interest or None

    def detect(self, frame: np.ndarray) -> List[Detection]:
        """Exécute l'inférence sur une frame et retourne les détections filtrées."""
        results = self._model.predict(
            source=frame,
            conf=self._confidence_threshold,
            classes=self._classes_of_interest,
            # verbose=False : Ultralytics affiche par défaut une ligne de
            # log détaillée à CHAQUE frame traitée (dimensions, temps
            # d'inférence...). À 15 FPS, ça inonderait nos logs en quelques
            # secondes — on garde le contrôle du logging via notre propre
            # `logger`, pas celui d'Ultralytics.
            verbose=False,
        )

        detections: List[Detection] = []
        if not results:
            return detections

        # results[0] : Ultralytics retourne une liste de résultats (un par
        # image passée en entrée) — ici on ne passe qu'une seule frame à la
        # fois, donc toujours l'élément [0].
        boxes = results[0].boxes
        for box in boxes:
            class_id = int(box.cls[0])
            confidence = float(box.conf[0])
            x1, y1, x2, y2 = map(int, box.xyxy[0].tolist())
            label = COCO_CLASS_NAMES.get(class_id, f"class_{class_id}")

            detections.append(
                Detection(
                    class_id=class_id,
                    label=label,
                    confidence=confidence,
                    bbox=(x1, y1, x2, y2),
                )
            )

        return detections
