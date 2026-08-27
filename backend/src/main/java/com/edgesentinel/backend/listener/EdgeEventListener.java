package com.edgesentinel.backend.listener;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.integration.annotation.ServiceActivator;
import org.springframework.stereotype.Component;

/**
 * Reçoit les événements publiés par les agents Edge sur le topic MQTT
 * edge/{device_id}/events (voir MqttConsumerConfig pour l'abonnement).
 *
 * Pour l'instant, se contente de loguer chaque message reçu -- la
 * persistance en base et l'exposition via WebSocket viendront dans une
 * prochaine étape, une fois ce premier maillon validé de bout en bout.
 */
@Component
public class EdgeEventListener {

    private static final Logger logger = LoggerFactory.getLogger(EdgeEventListener.class);

    @ServiceActivator(inputChannel = "mqttInputChannel")
    public void handleEvent(String payload) {
        logger.info("Événement Edge reçu: {}", payload);
    }
}
