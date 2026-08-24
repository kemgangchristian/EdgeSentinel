"""Tests unitaires de l'enregistreur d'événements (`recorder.py`).

Utilise `tmp_path` (fixture pytest) pour le dossier de sortie, et une frame
factice (tableau NumPy noir) plutôt qu'une vraie image de caméra -- on
teste ici le comportement du recorder, pas la qualité visuelle du dessin.
"""

import numpy as np

from src.event_engine import Event
from src.recorder import EventRecorder
from src.tracker import Track


def make_frame() -> np.ndarray:
    """Une frame factice 480x640 noire, format BGR standard OpenCV."""
    return np.zeros((480, 640, 3), dtype=np.uint8)


def make_track(track_id: int = 1) -> Track:
    return Track(
        track_id=track_id,
        label="person",
        centroid=(100, 100),
        confidence=0.9,
        bbox=(80, 80, 120, 120),
    )


def make_event(track_id: int = 1, event_type: str = "INTRUSION", zone="ZONE_A") -> Event:
    return Event(
        device_id="PI-TEST",
        event_type=event_type,
        confidence=0.9,
        zone=zone,
        timestamp="2026-08-24T12:00:00Z",
        track_id=track_id,
    )


class TestEventRecorder:
    def test_creates_output_directory_if_missing(self, tmp_path):
        output_dir = tmp_path / "captures"
        assert not output_dir.exists()

        EventRecorder(output_dir=str(output_dir))

        assert output_dir.exists()

    def test_record_saves_a_file(self, tmp_path):
        recorder = EventRecorder(output_dir=str(tmp_path))
        frame = make_frame()
        track = make_track()
        event = make_event()

        filepath = recorder.record(frame, track, event)

        assert filepath.exists()
        assert filepath.suffix == ".jpg"

    def test_filename_contains_device_type_and_track(self, tmp_path):
        recorder = EventRecorder(output_dir=str(tmp_path))
        frame = make_frame()
        track = make_track(track_id=42)
        event = make_event(track_id=42, event_type="INTRUSION")

        filepath = recorder.record(frame, track, event)

        assert "PI-TEST" in filepath.name
        assert "INTRUSION" in filepath.name
        assert "track42" in filepath.name

    def test_does_not_modify_original_frame(self, tmp_path):
        """La frame originale ne doit jamais être modifiée (annotated = frame.copy())."""
        recorder = EventRecorder(output_dir=str(tmp_path))
        frame = make_frame()
        original = frame.copy()
        track = make_track()
        event = make_event()

        recorder.record(frame, track, event)

        assert np.array_equal(frame, original)
