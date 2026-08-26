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


class TestCentroidTrackerCrossing:
    """Reproduit un croisement RÉALISTE (petits déplacements par frame,
    écart vertical net) pour vérifier que le tracking reste stable.

    Note de conception : avec de GRANDS déplacements par frame (position
    quasi superposée puis un saut de 100+ px), même l'algorithme hongrois
    peut "légitimement" préférer un échange si la somme des distances
    diagonales est mathématiquement plus courte -- ce n'est pas un bug,
    c'est une ambiguïté géométrique réelle sans information de vitesse.
    Ce test utilise donc des pas plus petits, représentatifs d'un
    croisement filmé à un FPS raisonnable.
    """

    def test_crossing_paths_with_small_steps_should_not_swap_identities(self):
        tracker = CentroidTracker(max_match_distance=60, max_frames_missing=5)

        # Écart vertical net (100px) qui persiste tout du long -- A reste
        # nettement au-dessus de B, seule leur position X se croise.
        tracker.update([make_detection(50, 50), make_detection(250, 150)])
        id_a = tracker.tracks[0].track_id if tracker.tracks[0].centroid == (50, 50) else tracker.tracks[1].track_id
        id_b = tracker.tracks[0].track_id if tracker.tracks[0].centroid == (250, 150) else tracker.tracks[1].track_id

        # Déplacements de 40px par frame seulement (pas 100+) -- réaliste
        # pour un FPS suffisant.
        steps = [(90, 50, 210, 150), (130, 50, 170, 150), (170, 50, 130, 150), (210, 50, 90, 150), (250, 50, 50, 150)]
        for ax, ay, bx, by in steps:
            tracker.update([make_detection(ax, ay), make_detection(bx, by)])

        final_tracks = tracker.tracks
        track_a_final = next(t for t in final_tracks if t.track_id == id_a)
        track_b_final = next(t for t in final_tracks if t.track_id == id_b)

        # A doit finir à droite (250,50) -- toujours identifiable par
        # son y=50 constant, jamais y=150.
        assert track_a_final.centroid == (250, 50)
        assert track_b_final.centroid == (50, 150)