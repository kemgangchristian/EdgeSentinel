"""Tests unitaires du tracker par centroïdes (`tracker.py`).

Ces tests ne nécessitent ni caméra ni GPU : on construit directement des
`Detection` factices pour vérifier la logique d'appariement en isolation.
"""

from src.detector import Detection
from src.tracker import CentroidTracker


def make_detection(x: int, y: int, label: str = "person") -> Detection:
    """Crée une détection factice centrée sur (x, y)."""
    return Detection(
        class_id=0,
        label=label,
        confidence=0.9,
        bbox=(x - 5, y - 5, x + 5, y + 5),
    )


class TestCentroidTracker:
    def test_new_detection_creates_a_track(self):
        tracker = CentroidTracker(max_match_distance=50, max_frames_missing=5)

        tracks = tracker.update([make_detection(100, 100)])

        assert len(tracks) == 1
        assert tracks[0].centroid == (100, 100)

    def test_close_detection_is_matched_to_existing_track(self):
        tracker = CentroidTracker(max_match_distance=50, max_frames_missing=5)

        tracker.update([make_detection(100, 100)])
        first_id = tracker.tracks[0].track_id

        # La personne bouge légèrement d'une frame à l'autre
        tracker.update([make_detection(110, 105)])

        assert len(tracker.tracks) == 1
        assert tracker.tracks[0].track_id == first_id  # même identité conservée
        assert tracker.tracks[0].centroid == (110, 105)

    def test_far_detection_creates_a_new_track(self):
        tracker = CentroidTracker(max_match_distance=50, max_frames_missing=5)

        tracker.update([make_detection(100, 100)])
        # Détection trop loin pour être la même personne (nouvelle entrée)
        tracker.update([make_detection(900, 900)])

        assert len(tracker.tracks) == 2

    def test_track_survives_brief_occlusion(self):
        tracker = CentroidTracker(max_match_distance=50, max_frames_missing=3)

        tracker.update([make_detection(100, 100)])
        first_id = tracker.tracks[0].track_id

        tracker.update([])  # une frame manquée (occlusion brève)
        tracker.update([make_detection(105, 100)])  # la personne réapparaît

        assert len(tracker.tracks) == 1
        assert tracker.tracks[0].track_id == first_id

    def test_track_is_removed_after_too_many_missing_frames(self):
        tracker = CentroidTracker(max_match_distance=50, max_frames_missing=2)

        tracker.update([make_detection(100, 100)])
        assert len(tracker.tracks) == 1

        # 3 frames consécutives sans aucune détection -> le track doit être purgé
        tracker.update([])
        tracker.update([])
        tracker.update([])

        assert len(tracker.tracks) == 0
