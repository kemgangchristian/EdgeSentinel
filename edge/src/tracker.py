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

    def update(self, detections: List[Detection]) -> List[Track]:
        """Met à jour les tracks à partir des détections de la frame courante."""
        unmatched_detections = list(detections)
        matched_track_ids: set[int] = set()

        # Sous-étape 1/4 : appariement glouton. Pour chaque track existant,
        # on cherche la détection la plus proche PARMI CELLES ENCORE
        # DISPONIBLES (une détection ne peut être associée qu'à un seul
        # track). "Glouton" signifie qu'on ne cherche pas l'appariement
        # global optimal (ce qui serait plus coûteux à calculer) — on
        # prend le meilleur choix track par track, dans l'ordre. Suffisant
        # pour notre cas d'usage (peu d'objets simultanés).
        for track in self._tracks.values():
            best_detection = None
            best_distance = self._max_match_distance

            for detection in unmatched_detections:
                distance = self._euclidean_distance(track.centroid, detection.centroid)
                if distance < best_distance:
                    best_distance = distance
                    best_detection = detection

            if best_detection is not None:
                track.centroid = best_detection.centroid
                track.confidence = best_detection.confidence
                track.bbox = best_detection.bbox
                track.label = best_detection.label
                track.frames_missing = 0
                matched_track_ids.add(track.track_id)
                unmatched_detections.remove(best_detection)

        # Sous-étapes 2/4, 3/4, 4/4 : ajoutées juste après.

        # Sous-étape 2/4 : les tracks non appariés cette frame vieillissent
        # d'un cran. Un track peut ne pas être apparié parce que l'objet
        # est temporairement occulté (passe derrière un obstacle), pas
        # forcément parce qu'il a définitivement quitté le champ.
        for track in self._tracks.values():
            if track.track_id not in matched_track_ids:
                track.frames_missing += 1

        # Sous-étapes 3/4, 4/4 : ajoutées juste après.

        # Sous-étape 3/4 : on supprime les tracks perdus depuis trop
        # longtemps — l'objet a très probablement quitté définitivement le
        # champ de la caméra, on arrête de le suivre.
        self._tracks = {
            tid: t
            for tid, t in self._tracks.items()
            if t.frames_missing <= self._max_frames_missing
        }

        # Sous-étape 4/4 : ajoutée juste après.

        # Sous-étape 4/4 : les détections qui n'ont trouvé aucun track à
        # leur proximité (donc restées dans unmatched_detections après la
        # sous-étape 1) sont de nouveaux objets entrant dans le champ —
        # on leur crée un track avec un ID jamais utilisé auparavant.
        for detection in unmatched_detections:
            new_id = next(_id_generator)
            self._tracks[new_id] = Track(
                track_id=new_id,
                label=detection.label,
                centroid=detection.centroid,
                confidence=detection.confidence,
                bbox=detection.bbox,
            )

        return self.tracks

    @staticmethod
    def _euclidean_distance(p1: tuple[int, int], p2: tuple[int, int]) -> float:
        """Distance euclidienne classique entre deux points 2D."""
        return math.dist(p1, p2)
