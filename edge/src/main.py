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
from dataclasses import replace
from types import FrameType
from typing import Optional

from .camera import VideoStream
from .config import AppConfig
from .detector import YoloDetector
from .event_engine import EventEngine
from .recorder import EventRecorder
from .sinks import CompositeSink, ConsoleSink, EventSink, FileSink, MqttSink
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
    if config.mqtt.enabled:
        sinks.append(
            MqttSink(
                host=config.mqtt.host,
                port=config.mqtt.port,
                topic=config.mqtt.topic,
                device_id=config.device_id,
                qos=config.mqtt.qos,
            )
        )

    if not sinks:
        logger.warning("Aucun sink actif : les événements ne seront nulle part visibles.")

    return CompositeSink(sinks)


def run(config_path: str) -> None:
    """Point d'entrée principal : initialise et lance le pipeline complet."""
    config = AppConfig.from_yaml(config_path)

    logging.basicConfig(
        level=config.log_level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )
    logger.info("Démarrage de l'agent Edge — device_id=%s", config.device_id)

    # Chaque composant du pipeline est construit ici, une seule fois, à
    # partir de la configuration -- pas de "magie" cachée, on voit
    # explicitement tout ce qui compose le système.
    detector = YoloDetector(
        model_path=config.detector.model_path,
        confidence_threshold=config.detector.confidence_threshold,
        classes_of_interest=config.detector.classes_of_interest,
    )
    tracker = CentroidTracker(
        max_match_distance=config.tracker.max_match_distance,
        max_frames_missing=config.tracker.max_frames_missing,
    )
    event_engine = EventEngine(device_id=config.device_id, config=config.event_engine)
    sink = build_sink(config)

    # Le recorder est optionnel -- None si désactivé dans la config, pour
    # éviter de créer un dossier et solliciter cv2.imwrite() inutilement
    # si la fonctionnalité n'est pas voulue.
    recorder = EventRecorder(config.recorder.output_dir) if config.recorder.enabled else None

    # Les signal handlers doivent être enregistrés AVANT de démarrer la
    # boucle -- sinon un Ctrl+C pendant l'initialisation ne serait pas
    # intercepté proprement.
    signal.signal(signal.SIGINT, _handle_shutdown_signal)
    signal.signal(signal.SIGTERM, _handle_shutdown_signal)

    frame_count = 0
    fps_window_start = time.monotonic()

    # `with VideoStream(...) as stream:` -- le context manager (__enter__/
    # __exit__) garantit que la caméra sera libérée proprement même si une
    # exception survient au milieu de la boucle.
    with VideoStream(
        source=config.camera.source,
        width=config.camera.width,
        height=config.camera.height,
        target_fps=config.camera.target_fps,
    ) as stream:
        try:
            while not _shutdown_requested:
                frame = stream.read()
                if frame is None:
                    # Aucune frame encore disponible (juste après le
                    # démarrage) -- on attend un court instant plutôt que
                    # de boucler frénétiquement sur du vide.
                    time.sleep(0.05)
                    continue

                # Le pipeline complet, en une seule ligne lisible : chaque
                # étape transforme la sortie de la précédente. C'est
                # littéralement l'enchaînement Caméra -> YOLO -> Tracker ->
                # Event Engine -> Sinks qu'on a construit fichier par fichier.
                detections = detector.detect(frame)
                tracks = tracker.update(detections)
                events = event_engine.process(tracks)

                for event in events:
                    # On enregistre la capture AVANT de publier, pour
                    # pouvoir inclure son chemin dans l'événement publié
                    # (utile au backend pour retrouver la preuve visuelle
                    # associée à un événement MQTT reçu).
                    if recorder is not None:
                        track = next((t for t in tracks if t.track_id == event.track_id), None)
                        if track is not None:
                            capture_path = recorder.record(frame, track, event)
                            # Event est immuable (frozen=True) : on ne le
                            # modifie jamais, on produit une NOUVELLE
                            # instance enrichie via dataclasses.replace().
                            event = replace(event, capture_path=str(capture_path))
                    sink.publish(event)

                frame_count += 1
                if frame_count % 100 == 0:
                    elapsed = time.monotonic() - fps_window_start
                    fps = frame_count / elapsed if elapsed > 0 else 0.0
                    logger.info("Débit moyen: %.1f FPS (%d frames traitées)", fps, frame_count)
        finally:
            # Ce bloc s'exécute TOUJOURS, que la boucle se termine
            # normalement (_shutdown_requested devenu True) ou à cause
            # d'une exception imprévue. C'est le filet de sécurité final :
            # même si quelque chose d'inattendu casse la boucle, on ferme
            # proprement les sinks (flush du fichier, fermeture du
            # descripteur) avant de quitter.
            sink.close()
            logger.info("Agent Edge arrêté proprement.")


def main() -> None:
    """Point d'entrée en ligne de commande."""
    parser = argparse.ArgumentParser(description="Agent Edge AI Monitor")
    parser.add_argument(
        "--config",
        default="config/config.yaml",
        help="Chemin vers le fichier de configuration YAML",
    )
    args = parser.parse_args()
    run(args.config)


if __name__ == "__main__":
    main()
