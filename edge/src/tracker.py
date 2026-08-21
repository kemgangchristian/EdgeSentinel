"""Tracking multi-objets par appariement de centroïdes.

Algorithme volontairement simple (pas de filtre de Kalman, pas de
ré-identification par apparence) mais suffisant pour associer une
détection à une identité stable d'une frame à l'autre.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from itertools import count
from typing import Dict, List

from .detector import Detection

# Générateur d'identifiants uniques et croissants pour les nouveaux tracks.
# `itertools.count` produit une séquence infinie (1, 2, 3, ...) — chaque
# appel à next() donne le prochain entier, jamais réutilisé.
_id_generator = count(start=1)

# Sentinel distinct de `None` : `None` signifiera "hors de toute zone" (un
# état métier valide, défini plus tard dans event_engine.py), tandis que ce
# sentinel signifie "jamais encore évalué". Sans cette distinction, un track
# fraîchement créé et déjà hors zone serait à tort considéré comme "état
# inchangé", et ne générerait jamais son événement initial.
NOT_YET_EVALUATED = "__NOT_YET_EVALUATED__"


@dataclass
class Track:
    """Un objet suivi dans le temps, avec son historique de position."""

    track_id: int
    label: str
    centroid: tuple[int, int]
    confidence: float
    bbox: tuple[int, int, int, int]
    frames_missing: int = 0
    # Dernière zone dans laquelle le centroïde a été détecté (None = hors
    # zone, NOT_YET_EVALUATED = jamais évalué). Utilisé par l'event_engine
    # (prochain fichier) pour détecter les transitions d'état.
    last_zone: str | None = field(default=NOT_YET_EVALUATED)


class CentroidTracker:
    """Associe les détections d'une frame aux tracks existants."""

    def __init__(self, max_match_distance: float, max_frames_missing: int):
        self._max_match_distance = max_match_distance
        self._max_frames_missing = max_frames_missing
        # Dictionnaire plutôt que liste : permet de retrouver/mettre à jour
        # un track par son ID en O(1), utile dans les étapes suivantes.
        self._tracks: Dict[int, Track] = {}

    @property
    def tracks(self) -> List[Track]:
        """Vue en liste des tracks actuellement suivis."""
        return list(self._tracks.values())
