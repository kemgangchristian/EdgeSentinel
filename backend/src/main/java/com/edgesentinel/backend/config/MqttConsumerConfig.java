package com.edgesentinel.backend.config;

import org.springframework.beans.factory.annotation.Value;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

/**
 * Configuration Spring Integration pour la consommation des événements MQTT
 * publiés par les agents Edge (topic edge/{device_id}/events).
 *
 * Contrat de message : le même format JSON que celui défini côté agent
 * Edge (voir edge/src/event_engine.py, Event.to_dict()) — deviceId,
 * eventType, confidence, zone, timestamp, trackId, capturePath.
 */
@Configuration
public class MqttConsumerConfig {

    @Value("${mqtt.broker.url}")
    private String brokerUrl;

    @Value("${mqtt.broker.clientId}")
    private String clientId;

    @Value("${mqtt.topic}")
    private String topic;

    // Les beans (client factory, adaptateur, canal) sont ajoutés
    // méthode par méthode dans les étapes suivantes.
}
