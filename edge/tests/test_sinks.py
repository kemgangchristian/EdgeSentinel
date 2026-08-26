"""Tests unitaires des sinks (`sinks.py`).

Utilise `tmp_path`, une fixture pytest intégrée qui fournit un dossier
temporaire unique et automatiquement nettoyé pour chaque test -- pas besoin
de gérer manuellement la création/suppression de fichiers de test.
"""

import json

from src.event_engine import Event
from src.sinks import CompositeSink, EventSink, FileSink


def make_event(track_id: int = 1, zone: str | None = None) -> Event:
    return Event(
        device_id="PI-TEST",
        event_type="INTRUSION" if zone else "PERSON_DETECTED",
        confidence=0.9,
        zone=zone,
        timestamp="2026-08-21T12:00:00Z",
        track_id=track_id,
    )


class BrokenSink(EventSink):
    """Sink qui échoue systématiquement -- utilisé pour tester l'isolation des erreurs."""

    def publish(self, event: Event) -> None:
        raise RuntimeError("Ce sink est volontairement cassé")


class TestFileSink:
    def test_writes_one_json_line_per_event(self, tmp_path):
        path = tmp_path / "events.jsonl"
        sink = FileSink(str(path))

        sink.publish(make_event(track_id=1))
        sink.publish(make_event(track_id=2, zone="ZONE_A"))
        sink.close()

        lines = path.read_text().splitlines()
        assert len(lines) == 2

        second_event = json.loads(lines[1])
        assert second_event["eventType"] == "INTRUSION"
        assert second_event["zone"] == "ZONE_A"

    def test_appends_to_existing_file_across_sessions(self, tmp_path):
        path = tmp_path / "events.jsonl"

        first_sink = FileSink(str(path))
        first_sink.publish(make_event(track_id=1))
        first_sink.close()

        # Un "redémarrage" de l'agent Edge : nouveau FileSink, même fichier.
        second_sink = FileSink(str(path))
        second_sink.publish(make_event(track_id=2))
        second_sink.close()

        lines = path.read_text().splitlines()
        assert len(lines) == 2  # les deux sessions sont bien cumulées


class TestCompositeSink:
    def test_broadcasts_to_all_sinks(self, tmp_path):
        path = tmp_path / "events.jsonl"
        file_sink = FileSink(str(path))
        composite = CompositeSink([file_sink])

        composite.publish(make_event())
        composite.close()

        lines = path.read_text().splitlines()
        assert len(lines) == 1

    def test_isolates_errors_from_broken_sinks(self, tmp_path):
        """Un sink qui échoue ne doit jamais empêcher les autres de fonctionner."""
        path = tmp_path / "events.jsonl"
        file_sink = FileSink(str(path))
        composite = CompositeSink([BrokenSink(), file_sink])

        # Ne doit lever AUCUNE exception, malgré BrokenSink.
        composite.publish(make_event())
        composite.close()

        lines = path.read_text().splitlines()
        assert len(lines) == 1  # FileSink a bien reçu l'événement


class TestMqttSink:
    """Utilise unittest.mock pour simuler paho-mqtt, sans jamais se
    connecter à un vrai broker -- tests rapides, isolés, reproductibles."""

    def test_publishes_to_correct_topic_with_device_id_substitution(self, mocker):
        mock_client_class = mocker.patch("src.sinks.mqtt.Client")
        mock_client = mock_client_class.return_value
        mock_client.publish.return_value.rc = 0  # MQTT_ERR_SUCCESS

        from src.sinks import MqttSink

        sink = MqttSink(
            host="localhost",
            port=1883,
            topic="edge/{device_id}/events",
            device_id="PI-001",
            qos=1,
        )
        event = make_event()
        sink.publish(event)

        mock_client.publish.assert_called_once()
        call_args = mock_client.publish.call_args
        assert call_args[0][0] == "edge/PI-001/events"

    def test_publish_payload_is_valid_json_matching_event(self, mocker):
        mock_client_class = mocker.patch("src.sinks.mqtt.Client")
        mock_client = mock_client_class.return_value
        mock_client.publish.return_value.rc = 0

        from src.sinks import MqttSink

        sink = MqttSink(
            host="localhost", port=1883, topic="edge/{device_id}/events", device_id="PI-001"
        )
        event = make_event(track_id=7, zone="ZONE_A")
        sink.publish(event)

        payload = mock_client.publish.call_args[0][1]
        parsed = json.loads(payload)
        assert parsed["trackId"] == 7
        assert parsed["eventType"] == "INTRUSION"

    def test_close_stops_loop_and_disconnects(self, mocker):
        mock_client_class = mocker.patch("src.sinks.mqtt.Client")
        mock_client = mock_client_class.return_value

        from src.sinks import MqttSink

        sink = MqttSink(
            host="localhost", port=1883, topic="edge/{device_id}/events", device_id="PI-001"
        )
        sink.close()

        mock_client.loop_stop.assert_called_once()
        mock_client.disconnect.assert_called_once()
