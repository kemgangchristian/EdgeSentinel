"""
Chargement et validation de la configuration de l'agent Edge
`config.yaml` correspond à une dataclass Python dédiée.
"""

# Permet d'écrire des types comme "int | str" même sur des versions de Python antérieures à 3.10.
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import List

import yaml


@dataclass
class CameraConfig:
    """Correspond à la section `camera:` du fichier YAML."""

    source: int | str
    width: int
    height: int
    target_fps: int


@dataclass
class DetectorConfig:
    """Correspond à la section `detector:` du fichier YAML."""

    model_path: str
    confidence_threshold: float
    # `field(default_factory=list)` plutôt que `= []` : en Python
    classes_of_interest: List[int] = field(default_factory=list)


@dataclass
class TrackerConfig:
    """Correspond à la section `tracker:` du fichier YAML."""

    max_match_distance: float
    max_frames_missing: int


@dataclass
class Zone:
    """Une zone interdite définie par un polygone.

    Représente UNE entrée de la liste `event_engine.zones` du YAML.
    """

    name: str
    # Liste de points (x, y) en pixels formant le contour du polygone.
    polygon: List[tuple[int, int]]


@dataclass
class EventEngineConfig:
    """Correspond à la section `event_engine:` du fichier YAML."""

    zones: List[Zone]
    deduplicate_events: bool


@dataclass
class FileSinkConfig:
    """Correspond à la sous-section `sinks.file:` du fichier YAML."""

    enabled: bool
    path: str


@dataclass
class SinksConfig:
    """Correspond à la section `sinks:` du fichier YAML.

    Note : on "aplatit" volontairement `console.enabled` en un simple
    booléen `console_enabled` plutôt que de créer une classe
    `ConsoleSinkConfig` à un seul champ — inutile de sur-modéliser une
    config aussi simple.
    """

    console_enabled: bool
    file: FileSinkConfig


@dataclass
class RecorderConfig:
    """Correspond à la section `recorder:` du fichier YAML."""

    enabled: bool
    output_dir: str


@dataclass
class MqttConfig:
    """Correspond à la section `mqtt:` du fichier YAML."""

    enabled: bool
    host: str
    port: int
    topic: str
    qos: int


@dataclass
class AppConfig:
    """Configuration complète de l'agent Edge — le point d'entrée unique.

    Une seule instance de cette classe est créée au démarrage (voir
    `main.py`, étape suivante) et transmise à tous les composants du
    pipeline (caméra, détecteur, tracker, moteur de règles, sinks).
    """

    device_id: str
    camera: CameraConfig
    detector: DetectorConfig
    tracker: TrackerConfig
    event_engine: EventEngineConfig
    sinks: SinksConfig
    recorder: RecorderConfig
    mqtt: MqttConfig
    log_level: str

    @staticmethod
    def from_yaml(path: str | Path) -> "AppConfig":
        """Charge le fichier YAML et construit un `AppConfig` validé.
        Lecture brute du fichier. `yaml.safe_load` (et non `yaml.load`)
        pour éviter l'exécution de code arbitraire.
        """
        raw = yaml.safe_load(Path(path).read_text(encoding="utf-8"))

        return AppConfig._build_from_raw_dict(raw, source_path=path)

    @staticmethod
    def _build_from_raw_dict(raw: dict, source_path: str | Path) -> "AppConfig":
        """Construit les objets à partir du dictionnaire brut."""
        try:
            # Les zones sont la partie la plus imbriquée : une liste de
            # dictionnaires, chacun transformé en instance `Zone`. Le
            # polygone (liste de listes [x, y] en YAML) est converti en
            # liste de tuples (x, y), plus adapté pour un usage
            # géométrique immuable en Python.
            zones = [
                Zone(name=z["name"], polygon=[tuple(p) for p in z["polygon"]])
                for z in raw["event_engine"]["zones"]
            ]

            # Étape 3/3 (assemblage final) : ajoutée juste après.
            return AppConfig._assemble(raw, zones)

        except KeyError as exc:
            raise KeyError(
                f"Section de configuration manquante ou invalide dans "
                f"{source_path}: clé {exc} introuvable"
            ) from exc

    @staticmethod
    def _assemble(raw: dict, zones: List[Zone]) -> "AppConfig":
        """
        Chaque `raw["section"]["clé"]` correspond directement à une ligne du `config.yaml`
        """
        return AppConfig(
            device_id=raw["device"]["id"],
            camera=CameraConfig(
                source=raw["camera"]["source"],
                width=raw["camera"]["width"],
                height=raw["camera"]["height"],
                target_fps=raw["camera"]["target_fps"],
            ),
            detector=DetectorConfig(
                model_path=raw["detector"]["model_path"],
                confidence_threshold=raw["detector"]["confidence_threshold"],
                # .get(..., []) : cette clé a une valeur par défaut dans le
                # YAML lui-même (liste vide = "toutes les classes"), donc
                # on tolère son absence ici plutôt que de lever une
                # KeyError.
                classes_of_interest=raw["detector"].get("classes_of_interest", []),
            ),
            tracker=TrackerConfig(
                max_match_distance=raw["tracker"]["max_match_distance"],
                max_frames_missing=raw["tracker"]["max_frames_missing"],
            ),
            event_engine=EventEngineConfig(
                zones=zones,
                deduplicate_events=raw["event_engine"].get("deduplicate_events", True),
            ),
            sinks=SinksConfig(
                console_enabled=raw["sinks"]["console"]["enabled"],
                file=FileSinkConfig(
                    enabled=raw["sinks"]["file"]["enabled"],
                    path=raw["sinks"]["file"]["path"],
                ),
            ),
            recorder=RecorderConfig(
                enabled=raw.get("recorder", {}).get("enabled", False),
                output_dir=raw.get("recorder", {}).get("output_dir", "captures"),
            ),
            mqtt=MqttConfig(
                enabled=raw.get("mqtt", {}).get("enabled", False),
                host=raw.get("mqtt", {}).get("host", "localhost"),
                port=raw.get("mqtt", {}).get("port", 1883),
                topic=raw.get("mqtt", {}).get("topic", "edge/{device_id}/events"),
                qos=raw.get("mqtt", {}).get("qos", 1),
            ),
            log_level=raw.get("logging", {}).get("level", "INFO"),
        )
