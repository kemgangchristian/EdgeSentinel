"""Capture vidéo via OpenCV, en thread dédié.

Pourquoi un thread dédié : `cv2.VideoCapture.read()` est bloquant. Sans
isolation, le temps de capture s'ajoute au temps d'inférence dans la boucle
principale, et le flux prend un retard croissant sur le direct.

En isolant la capture dans un thread qui tourne en continu et ne conserve
que la DERNIÈRE frame lue, la boucle principale consomme les frames à son
propre rythme (limité par l'inférence), sans jamais bloquer sur la lecture
caméra.
"""

from __future__ import annotations

import logging
import threading
import time
from typing import Optional

import cv2
import numpy as np

logger = logging.getLogger(__name__)


class VideoStream:
    """Flux vidéo lu en continu dans un thread, exposant la dernière frame."""
