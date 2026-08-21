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
        # (autre thread) le lit via read(). Lock évite les accès concurrents
        # non coordonnés à l'objet partagé et les comportements difficiles à garantir.
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

    def _update_loop(self) -> None:
        """Boucle exécutée dans le thread : lit en continu la dernière frame."""
        while not self._stopped.is_set():
            start = time.monotonic()
            ok, frame = self._capture.read()
            if not ok:
                # Échec ponctuel de lecture (caméra débranchée un instant,
                # flux réseau RTSP qui hoquette...) : on ne lève PAS
                # d'exception ici, ce n'est pas fatal — on retente à la
                # prochaine itération, après une courte pause.
                logger.warning("Lecture de frame échouée, nouvelle tentative...")
                time.sleep(0.1)
                continue

            with self._lock:
                self._latest_frame = frame

            # Cadencement : si la lecture a été plus rapide que l'intervalle
            # cible (caméra rapide, peu de traitement), on attend le temps
            # restant pour ne pas lire plus vite que target_fps ne le demande
            # (évite de saturer le CPU inutilement).
            elapsed = time.monotonic() - start
            sleep_time = self._min_frame_interval - elapsed
            if sleep_time > 0:
                time.sleep(sleep_time)

    def read(self) -> Optional[np.ndarray]:
        """Retourne une copie de la dernière frame disponible (ou None)."""
        with self._lock:
            if self._latest_frame is None:
                return None
            return self._latest_frame.copy()

    def stop(self) -> None:
        """Arrête proprement le thread de capture et libère la caméra."""
        self._stopped.set()
        if self._thread is not None:
            # join() attend que le thread se termine réellement avant de
            # continuer — sans ça, on pourrait tenter de libérer la caméra
            # (self._capture.release()) PENDANT que le thread essaie encore
            # de lire dessus, provoquant une erreur ou un comportement
            # indéfini.
            self._thread.join(timeout=2.0)
        if self._capture is not None:
            self._capture.release()
        logger.info("VideoStream arrêté")

    def __enter__(self) -> "VideoStream":
        return self.start()

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.stop()
