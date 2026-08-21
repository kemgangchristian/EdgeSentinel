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


def point_in_polygon(point: tuple[int, int], polygon: List[tuple[int, int]]) -> bool:
    """Algorithme du ray casting : teste si `point` est à l'intérieur du polygone.

    Principe : on trace un rayon horizontal depuis le point vers l'infini, et
    on compte combien d'arêtes du polygone il traverse. Un nombre impair de
    traversées signifie que le point est à l'intérieur ; un nombre pair
    signifie qu'il est à l'extérieur.

    Implémenté manuellement (pas de dépendance comme `shapely`) pour garder
    l'agent Edge léger — contrainte importante sur Raspberry Pi.
    """
    x, y = point
    inside = False
    n = len(polygon)

    x1, y1 = polygon[0]
    for i in range(1, n + 1):
        x2, y2 = polygon[i % n]
        if y > min(y1, y2):
            if y <= max(y1, y2):
                if x <= max(x1, x2):
                    if y1 != y2:
                        x_intersection = (y - y1) * (x2 - x1) / (y2 - y1) + x1
                    else:
                        x_intersection = x1
                    if x1 == x2 or x <= x_intersection:
                        inside = not inside
        x1, y1 = x2, y2

    return inside
