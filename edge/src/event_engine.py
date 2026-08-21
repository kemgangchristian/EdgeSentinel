"""Moteur de règles métier : transforme des `Track` en `Event` métier.

C'est la brique qui donne du sens business au pipeline de vision : on ne se
contente pas de dire "il y a une personne", on dit "il y a une INTRUSION en
ZONE_A avec 94% de confiance".
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import List, Optional

from .config import EventEngineConfig
from .tracker import Track

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class Event:
    """Événement métier prêt à être publié par un sink (console, fichier, MQTT...)."""

    device_id: str
    event_type: str  # "PERSON_DETECTED" | "INTRUSION"
    confidence: float
    zone: Optional[str]
    timestamp: str
    track_id: int

    def to_dict(self) -> dict:
        """Sérialisation vers un dictionnaire — format prêt pour JSON."""
        return {
            "deviceId": self.device_id,
            "eventType": self.event_type,
            "confidence": round(self.confidence, 4),
            "zone": self.zone,
            "timestamp": self.timestamp,
            "trackId": self.track_id,
        }
