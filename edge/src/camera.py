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

    def __init__(self, source: int | str, width: int, height: int, target_fps: int):
        self._source = source
        self._width = width
        self._height = height
        # Convertit le FPS cible en intervalle minimum entre deux lectures
        # (en secondes). Ex : 15 FPS -> 1/15 ≈ 0.067s entre chaque frame.
        self._min_frame_interval = 1.0 / target_fps if target_fps > 0 else 0.0

        # None tant que start() n'a pas été appelé — évite d'initialiser
        # la caméra dans le constructeur (principe de responsabilité unique :
        # __init__ configure l'objet, start() déclenche l'action réelle).
        self._capture: Optional[cv2.VideoCapture] = None
        self._latest_frame: Optional[np.ndarray] = None

        # Un verrou (Lock) est indispensable dès qu'un thread écrit une
        # donnée qu'un autre thread lit en parallèle — ici, le thread de
        # capture écrit _latest_frame pendant que la boucle principale
        # (autre thread) le lit via read(). Sans lock, on risquerait de
        # lire une frame à moitié écrite (rare mais possible en Python).
        self._lock = threading.Lock()

        # Un Event plutôt qu'un simple booléen : thread-safe nativement,
        # et permet d'attendre proprement l'arrêt (contrairement à un
        # booléen qu'il faudrait aussi protéger par un lock).
        self._stopped = threading.Event()
        self._thread: Optional[threading.Thread] = None

    def start(self) -> "VideoStream":
        """Ouvre la caméra et démarre la capture en arrière-plan."""
        self._capture = cv2.VideoCapture(self._source)
        if not self._capture.isOpened():
            raise RuntimeError(f"Impossible d'ouvrir la source vidéo: {self._source}")

        self._capture.set(cv2.CAP_PROP_FRAME_WIDTH, self._width)
        self._capture.set(cv2.CAP_PROP_FRAME_HEIGHT, self._height)

        # daemon=True : ce thread s'arrêtera automatiquement si le programme
        # principal se termine, même si stop() n'a pas été appelé
        # explicitement (évite un processus fantôme qui empêcherait l'arrêt
        # propre de l'agent Edge).
        self._thread = threading.Thread(target=self._update_loop, daemon=True)
        self._thread.start()
        logger.info(
            "VideoStream démarré (source=%s, %sx%s)", self._source, self._width, self._height
        )
        return self
