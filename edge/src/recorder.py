"""Enregistrement d'images annotées au moment des événements détectés.

Contrairement au flux vidéo continu (jamais transmis, pour respecter le
principe Edge Computing du projet), ce module capture une image UNIQUEMENT
au moment où un événement se produit (INTRUSION/PERSON_DETECTED), avec la
bounding box et les métadonnées dessinées dessus -- une "preuve visuelle"
légère plutôt qu'un flux permanent.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from pathlib import Path

import cv2
import numpy as np

from .event_engine import Event
from .tracker import Track

logger = logging.getLogger(__name__)


class EventRecorder:
    """Dessine une bounding box annotée et sauvegarde l'image sur événement."""

    def __init__(self, output_dir: str):
        self._output_dir = Path(output_dir)
        # Créé le dossier de sortie (et ses parents) s'il n'existe pas déjà.
        # exist_ok=True : ne lève pas d'erreur si le dossier existe déjà
        # (idempotent, important puisque l'agent peut redémarrer plusieurs
        # fois sur le même dossier de captures).
        self._output_dir.mkdir(parents=True, exist_ok=True)
        logger.info("EventRecorder initialisé, sortie: %s", self._output_dir)

    def record(self, frame: np.ndarray, track: Track, event: Event) -> Path:
        """Dessine la bounding box annotée et sauvegarde l'image.

        Retourne le chemin du fichier créé -- utile pour plus tard
        (par exemple joindre ce chemin à l'événement publié via MQTT en V2).
        """
        annotated = frame.copy()

        x1, y1, x2, y2 = track.bbox
        # Couleur au format BGR (pas RGB -- convention OpenCV historique) :
        # rouge pour une intrusion (alerte), vert pour une simple détection.
        color = (0, 0, 255) if event.event_type == "INTRUSION" else (0, 200, 0)

        cv2.rectangle(annotated, (x1, y1), (x2, y2), color, thickness=2)

        label = f"{event.event_type} {event.confidence:.0%}"
        if event.zone:
            label += f" [{event.zone}]"

        # Le texte est positionné juste au-dessus du rectangle. max(y1-10, 20)
        # évite que le texte sorte du cadre de l'image si la détection est
        # tout en haut de la frame (y1 proche de 0).
        text_y = max(y1 - 10, 20)
        cv2.putText(
            annotated,
            label,
            (x1, text_y),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            color,
            thickness=2,
        )

        # Sous-étape 2/2 : sauvegarde du fichier, ajoutée juste après.
        return self._save(annotated, event)
