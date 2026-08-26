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

import numpy as np
from scipy.optimize import linear_sum_assignment

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

        # Sous-étape 1/4 : appariement OPTIMAL par l'algorithme hongrois.
        # Contrairement à l'ancien algorithme glouton (qui associait
        # track par track, dans l'ordre, sans recul), on calcule ici
        # l'appariement qui minimise la SOMME TOTALE des distances sur
        # l'ensemble des tracks et détections -- ce qui évite les échanges
        # d'identité (ID swap) lorsque deux objets se croisent, prouvé
        # par le test TestCentroidTrackerCrossing.
        existing_tracks = list(self._tracks.values())

        if existing_tracks and unmatched_detections:
            # Matrice de coûts : cost_matrix[i][j] = distance entre le
            # track i et la détection j. linear_sum_assignment cherche
            # l'affectation qui MINIMISE la somme des coûts sélectionnés.
            cost_matrix = np.array(
                [
                    [
                        self._euclidean_distance(track.centroid, detection.centroid)
                        for detection in unmatched_detections
                    ]
                    for track in existing_tracks
                ]
            )

            # row_ind[k] / col_ind[k] : le track d'indice row_ind[k] est
            # apparié à la détection d'indice col_ind[k], pour chaque k
            # de l'appariement optimal trouvé.
            row_indices, col_indices = linear_sum_assignment(cost_matrix)

            matched_detection_indices = set()
            for row, col in zip(row_indices, col_indices):
                distance = cost_matrix[row][col]
                # Le seuil max_match_distance s'applique toujours : un
                # appariement "optimal" mais trop éloigné reste rejeté.
                if distance > self._max_match_distance:
                    continue

                track = existing_tracks[row]
                detection = unmatched_detections[col]

                track.centroid = detection.centroid
                track.confidence = detection.confidence
                track.bbox = detection.bbox
                track.label = detection.label
                track.frames_missing = 0
                matched_track_ids.add(track.track_id)
                matched_detection_indices.add(col)

            # Retire les détections appariées, dans l'ordre inverse pour
            # ne pas décaler les indices des éléments restants pendant
            # la suppression.
            for col in sorted(matched_detection_indices, reverse=True):
                unmatched_detections.pop(col)

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
