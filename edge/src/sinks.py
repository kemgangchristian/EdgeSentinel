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
