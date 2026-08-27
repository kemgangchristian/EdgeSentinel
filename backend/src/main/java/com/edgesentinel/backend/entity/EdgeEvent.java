package com.edgesentinel.backend.entity;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.GeneratedValue;
import jakarta.persistence.GenerationType;
import jakarta.persistence.Id;
import jakarta.persistence.Table;

/**
 * Représentation persistée d'un événement reçu depuis l'agent Edge via
 * MQTT. Les champs correspondent exactement au contrat JSON défini dans
 * edge/src/event_engine.py (Event.to_dict()) -- deviceId, eventType,
 * confidence, zone, timestamp, trackId, capturePath.
 */
@Entity
@Table(name = "edge_events")
public class EdgeEvent {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(name = "device_id", nullable = false)
    private String deviceId;

    @Column(name = "event_type", nullable = false)
    private String eventType;

    @Column(nullable = false)
    private Double confidence;

    // Nullable : un événement PERSON_DETECTED (hors zone) n'a pas de zone.
    private String zone;

    @Column(nullable = false)
    private String timestamp;

    @Column(name = "track_id", nullable = false)
    private Integer trackId;

    @Column(name = "capture_path")
    private String capturePath;

    // Constructeur par défaut requis par JPA/Hibernate -- jamais appelé
    // directement dans notre code, mais le framework en a besoin pour
    // reconstruire les objets depuis la base.
    protected EdgeEvent() {
    }
}
