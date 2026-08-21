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


def build_sink(config: AppConfig) -> EventSink:
    """Construit le sink composite à partir de la configuration.

    En V2, il suffira d'ajouter un `MqttSink` ici si `config.sinks.mqtt.enabled`
    -- le reste du pipeline n'a pas besoin d'être modifié (principe
    ouvert/fermé appliqué concrètement).
    """
    sinks: list[EventSink] = []
    if config.sinks.console_enabled:
        sinks.append(ConsoleSink())
    if config.sinks.file.enabled:
        sinks.append(FileSink(config.sinks.file.path))

    if not sinks:
        logger.warning("Aucun sink actif : les événements ne seront nulle part visibles.")

    return CompositeSink(sinks)
