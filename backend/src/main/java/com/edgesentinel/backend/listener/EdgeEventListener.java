package com.edgesentinel.backend.listener;

import com.edgesentinel.backend.entity.EdgeEvent;
import com.edgesentinel.backend.repository.EdgeEventRepository;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.integration.annotation.ServiceActivator;
import org.springframework.stereotype.Component;

/**
 * Reçoit les événements publiés par les agents Edge sur le topic MQTT
 * edge/{device_id}/events (voir MqttConsumerConfig pour l'abonnement),
 * les désérialise depuis JSON, et les persiste en base de données.
 */
@Component
public class EdgeEventListener {

    private static final Logger logger = LoggerFactory.getLogger(EdgeEventListener.class);

    private final EdgeEventRepository repository;
    private final ObjectMapper objectMapper;

    // Injection par constructeur : Spring fournit automatiquement une
    // instance de EdgeEventRepository et d'ObjectMapper (déjà configurée
    // par Spring Boot pour Jackson) -- pas de "new" manuel, pas de couplage
    // direct à une implémentation concrète.
    public EdgeEventListener(EdgeEventRepository repository, ObjectMapper objectMapper) {
        this.repository = repository;
        this.objectMapper = objectMapper;
    }

    @ServiceActivator(inputChannel = "mqttInputChannel")
    public void handleEvent(String payload) {
        try {
            JsonNode node = objectMapper.readTree(payload);

            EdgeEvent event = new EdgeEvent(
                    node.get("deviceId").asText(),
                    node.get("eventType").asText(),
                    node.get("confidence").asDouble(),
                    node.hasNonNull("zone") ? node.get("zone").asText() : null,
                    node.get("timestamp").asText(),
                    node.get("trackId").asInt(),
                    node.hasNonNull("capturePath") ? node.get("capturePath").asText() : null
            );

            repository.save(event);
            logger.info("Événement persisté (id={}): {} / {}", event.getId(),
                    event.getDeviceId(), event.getEventType());
        } catch (Exception e) {
            // Ne jamais laisser une erreur de parsing/persistance faire
            // planter le listener MQTT -- un message malformé ne doit
            // jamais interrompre la réception des suivants (même principe
            // que CompositeSink côté agent Edge : isoler les erreurs).
            logger.error("Échec du traitement de l'événement MQTT: {}", payload, e);
        }
    }
}