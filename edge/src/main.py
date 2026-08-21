"""Point d'entrée de l'agent Edge AI Monitor.

Boucle principale :

    Caméra → Détecteur YOLO → Tracker → Event Engine → Sinks

Usage :
    python -m src.main --config config/config.yaml
"""

from __future__ import annotations

import argparse
import logging
import signal
import time
from types import FrameType
from typing import Optional

from .camera import VideoStream
from .config import AppConfig
from .detector import YoloDetector
from .event_engine import EventEngine
from .sinks import CompositeSink, ConsoleSink, EventSink, FileSink
from .tracker import CentroidTracker

logger = logging.getLogger(__name__)

# Drapeau global positionné par le handler de signal (Ctrl+C, arrêt système)
# pour permettre un arrêt propre de la boucle (libération caméra, flush des
# fichiers...) plutôt qu'un arrêt brutal qui pourrait corrompre des données
# en cours d'écriture.
_shutdown_requested = False


def _handle_shutdown_signal(signum: int, frame: Optional[FrameType]) -> None:
    global _shutdown_requested
    logger.info("Signal d'arrêt reçu (%s), arrêt en cours...", signum)
    _shutdown_requested = True
