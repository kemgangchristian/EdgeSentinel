"""Tests unitaires du moteur de règles métier (`event_engine.py`).

Ces tests ne nécessitent ni caméra ni modèle YOLO : on construit directement
des objets `Track` factices pour vérifier la logique de zones en isolation.
"""

from src.config import EventEngineConfig, Zone
from src.event_engine import EventEngine, point_in_polygon
from src.tracker import Track

SQUARE_ZONE = Zone(name="ZONE_A", polygon=[(0, 0), (100, 0), (100, 100), (0, 100)])


def make_track(track_id: int, centroid: tuple[int, int], confidence: float = 0.9) -> Track:
    return Track(
        track_id=track_id,
        label="person",
        centroid=centroid,
        confidence=confidence,
        bbox=(centroid[0] - 5, centroid[1] - 5, centroid[0] + 5, centroid[1] + 5),
    )


class TestPointInPolygon:
    def test_point_inside_square_is_inside(self):
        assert point_in_polygon((50, 50), SQUARE_ZONE.polygon) is True

    def test_point_outside_square_is_outside(self):
        assert point_in_polygon((200, 200), SQUARE_ZONE.polygon) is False

    def test_point_far_outside_is_outside(self):
        assert point_in_polygon((-50, -50), SQUARE_ZONE.polygon) is False


class TestEventEngine:
    def test_new_track_outside_zone_generates_initial_event(self):
        """Test de non-régression : c'est le bug historique de ce projet.

        Un track flambant neuf, déjà hors de toute zone, doit générer son
        événement PERSON_DETECTED initial -- sans le sentinel
        NOT_YET_EVALUATED, ce cas échouait silencieusement.
        """
        engine = EventEngine(
            device_id="PI-TEST",
            config=EventEngineConfig(zones=[SQUARE_ZONE], deduplicate_events=True),
        )
        track = make_track(track_id=1, centroid=(500, 500))

        events = engine.process([track])

        assert len(events) == 1
        assert events[0].event_type == "PERSON_DETECTED"
        assert events[0].zone is None

    def test_new_track_inside_zone_generates_intrusion(self):
        engine = EventEngine(
            device_id="PI-TEST",
            config=EventEngineConfig(zones=[SQUARE_ZONE], deduplicate_events=True),
        )
        track = make_track(track_id=1, centroid=(50, 50))

        events = engine.process([track])

        assert len(events) == 1
        assert events[0].event_type == "INTRUSION"
        assert events[0].zone == "ZONE_A"

    def test_deduplication_skips_unchanged_state(self):
        engine = EventEngine(
            device_id="PI-TEST",
            config=EventEngineConfig(zones=[SQUARE_ZONE], deduplicate_events=True),
        )
        track = make_track(track_id=1, centroid=(50, 50))

        first_pass = engine.process([track])
        second_pass = engine.process([track])  # même position, même zone

        assert len(first_pass) == 1
        assert len(second_pass) == 0  # pas de nouvel événement, état inchangé

    def test_zone_transition_generates_new_event(self):
        engine = EventEngine(
            device_id="PI-TEST",
            config=EventEngineConfig(zones=[SQUARE_ZONE], deduplicate_events=True),
        )
        track = make_track(track_id=1, centroid=(50, 50))

        engine.process([track])  # entre en zone -> INTRUSION
        track.centroid = (500, 500)  # sort de la zone
        events = engine.process([track])

        assert len(events) == 1
        assert events[0].event_type == "PERSON_DETECTED"

    def test_without_deduplication_every_frame_emits_event(self):
        engine = EventEngine(
            device_id="PI-TEST",
            config=EventEngineConfig(zones=[SQUARE_ZONE], deduplicate_events=False),
        )
        track = make_track(track_id=1, centroid=(50, 50))

        first_pass = engine.process([track])
        second_pass = engine.process([track])

        assert len(first_pass) == 1
        assert len(second_pass) == 1
