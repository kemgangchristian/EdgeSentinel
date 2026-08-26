"""Sinks : destinations possibles pour les événements générés par le pipeline.

Principe ouvert/fermé : le pipeline principal ne connaît que l'interface
abstraite `EventSink`. Ajouter une nouvelle destination (par exemple un
`MqttSink` en V2) ne nécessite aucune modification du code existant.
"""

from __future__ import annotations

import json
import logging
from abc import ABC, abstractmethod
from pathlib import Path

import paho.mqtt.client as mqtt

from .event_engine import Event

logger = logging.getLogger(__name__)


class EventSink(ABC):
    """Interface commune à toute destination d'événements."""

    @abstractmethod
    def publish(self, event: Event) -> None:
        """Publie un événement.

        Ne doit jamais lever d'exception bloquante : une erreur de sink ne
        doit pas interrompre le pipeline de vision (voir CompositeSink,
        qui isole les erreurs par sink).
        """
        raise NotImplementedError

    def close(self) -> None:
        """Nettoyage optionnel (fermeture de fichier, déconnexion...).

        Implémentation par défaut vide : tous les sinks n'ont pas besoin
        de nettoyage (ex: ConsoleSink), donc ce n'est pas abstrait.
        """


class ConsoleSink(EventSink):
    """Affiche les événements dans les logs — utile en développement/démo."""

    def publish(self, event: Event) -> None:
        logger.info("📡 Événement: %s", json.dumps(event.to_dict(), ensure_ascii=False))


class FileSink(EventSink):
    """Ajoute chaque événement en une ligne JSON dans un fichier (format JSONL).

    Le format JSONL (une ligne = un JSON valide) permet de "tailer" le
    fichier en direct (`tail -f events.jsonl`) et de le parser ligne par
    ligne sans charger tout le fichier en mémoire.
    """

    def __init__(self, path: str):
        self._path = Path(path)
        self._file = self._path.open("a", encoding="utf-8")

    def publish(self, event: Event) -> None:
        self._file.write(json.dumps(event.to_dict(), ensure_ascii=False) + "\n")
        self._file.flush()

    def close(self) -> None:
        self._file.close()


class CompositeSink(EventSink):
    """Diffuse chaque événement vers plusieurs sinks à la fois."""

    def __init__(self, sinks: list[EventSink]):
        self._sinks = sinks

    def publish(self, event: Event) -> None:
        for sink in self._sinks:
            try:
                sink.publish(event)
            except Exception:  # noqa: BLE001 - un sink en erreur ne doit pas bloquer les autres
                logger.exception("Échec de publication vers %s", type(sink).__name__)

    def close(self) -> None:
        for sink in self._sinks:
            sink.close()


class MqttSink(EventSink):
    """Publie les événements vers un broker MQTT (Mosquitto).

    Contrat de topic : "edge/{device_id}/events" (configurable), cohérent
    avec l'architecture définie dès le début du projet -- le backend
    Spring Boot (à venir) souscrira à ce même topic pour consommer les
    événements en temps réel.
    """

    def __init__(self, host: str, port: int, topic: str, device_id: str, qos: int = 1):
        self._topic = topic.format(device_id=device_id)
        self._qos = qos

        # client_id explicite : utile pour identifier ce client précis
        # dans les logs du broker Mosquitto, plutôt qu'un ID aléatoire.
        self._client = mqtt.Client(client_id=f"edge-sentinel-{device_id}")
        self._client.connect(host, port)
        # loop_start() : démarre un thread interne à paho-mqtt qui gère
        # la boucle réseau (envoi/réception, reconnexion automatique) --
        # sans ça, publish() bloquerait ou ne fonctionnerait pas de façon
        # fiable dans une application qui a déjà sa propre boucle
        # principale (notre run() dans main.py).
        self._client.loop_start()

        logger.info("MqttSink connecté à %s:%s, topic=%s", host, port, self._topic)

    def publish(self, event: Event) -> None:
        payload = json.dumps(event.to_dict(), ensure_ascii=False)
        result = self._client.publish(self._topic, payload, qos=self._qos)
        # rc (return code) différent de MQTT_ERR_SUCCESS signifie que la
        # publication a échoué à être mise en file d'attente localement
        # (pas nécessairement reçue par le broker -- avec QoS 1, la vraie
        # confirmation de livraison est asynchrone, gérée en interne par
        # paho-mqtt via loop_start()).
        if result.rc != mqtt.MQTT_ERR_SUCCESS:
            logger.warning("Échec de mise en file MQTT (code %s)", result.rc)

    def close(self) -> None:
        self._client.loop_stop()
        self._client.disconnect()
        logger.info("MqttSink déconnecté")
