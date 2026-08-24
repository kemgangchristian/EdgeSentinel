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
