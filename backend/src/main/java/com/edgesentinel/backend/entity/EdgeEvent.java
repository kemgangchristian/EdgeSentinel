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

    // Constructeur utilisé par notre code (le listener) pour créer une
    // instance à partir du JSON désérialisé, avant persistance.
    public EdgeEvent(
            String deviceId,
            String eventType,
            Double confidence,
            String zone,
            String timestamp,
            Integer trackId,
            String capturePath) {
        this.deviceId = deviceId;
        this.eventType = eventType;
        this.confidence = confidence;
        this.zone = zone;
        this.timestamp = timestamp;
        this.trackId = trackId;
        this.capturePath = capturePath;
    }

    public Long getId() {
        return id;
    }

    public String getDeviceId() {
        return deviceId;
    }

    public String getEventType() {
        return eventType;
    }

    public Double getConfidence() {
        return confidence;
    }

    public String getZone() {
        return zone;
    }

    public String getTimestamp() {
        return timestamp;
    }

    public Integer getTrackId() {
        return trackId;
    }

    public String getCapturePath() {
        return capturePath;
    }
}
