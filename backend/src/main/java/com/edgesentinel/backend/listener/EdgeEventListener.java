package com.edgesentinel.backend.listener;

import com.edgesentinel.backend.entity.EdgeEvent;
import com.edgesentinel.backend.repository.EdgeEventRepository;
import tools.jackson.databind.JsonNode;
import tools.jackson.databind.ObjectMapper;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.integration.annotation.ServiceActivator;
import org.springframework.messaging.simp.SimpMessagingTemplate;
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
    private final SimpMessagingTemplate messagingTemplate;

    public EdgeEventListener(
            EdgeEventRepository repository,
            ObjectMapper objectMapper,
            SimpMessagingTemplate messagingTemplate) {
        this.repository = repository;
        this.objectMapper = objectMapper;
        this.messagingTemplate = messagingTemplate;
    }

    @ServiceActivator(inputChannel = "mqttInputChannel")
    public void handleEvent(String payload) {
        try {
            JsonNode node = objectMapper.readTree(payload);

            EdgeEvent event = new EdgeEvent(
                node.get("deviceId").asString(),
                node.get("eventType").asString(),
                node.get("confidence").asDouble(),
                node.hasNonNull("zone") ? node.get("zone").asString() : null,
                node.get("timestamp").asString(),
                node.get("trackId").asInt(),
                node.hasNonNull("capturePath") ? node.get("capturePath").asString() : null
            );

            EdgeEvent saved = repository.save(event);
            logger.info("Événement persisté (id={}): {} / {}", saved.getId(),
                    saved.getDeviceId(), saved.getEventType());
            // Diffusion en direct à tous les clients WebSocket abonnés à
            // /topic/events -- l'entité persistée (avec son id généré)
            // est envoyée telle quelle, Jackson la sérialise automatiquement.
            messagingTemplate.convertAndSend("/topic/events", saved);
        } catch (Exception e) {
            // Ne jamais laisser une erreur de parsing/persistance faire
            // planter le listener MQTT -- un message malformé ne doit
            // jamais interrompre la réception des suivants (même principe
            // que CompositeSink côté agent Edge : isoler les erreurs).
            logger.error("Échec du traitement de l'événement MQTT: {}", payload, e);
        }
    }
}