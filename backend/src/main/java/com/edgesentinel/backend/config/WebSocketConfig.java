package com.edgesentinel.backend.config;

import org.springframework.context.annotation.Configuration;
import org.springframework.messaging.simp.config.MessageBrokerRegistry;
import org.springframework.web.socket.config.annotation.EnableWebSocketMessageBroker;
import org.springframework.web.socket.config.annotation.StompEndpointRegistry;
import org.springframework.web.socket.config.annotation.WebSocketMessageBrokerConfigurer;

/**
 * Configuration WebSocket/STOMP pour la diffusion des événements en temps
 * réel vers le frontend. Complète (ne remplace pas) la persistance déjà
 * assurée par EdgeEventListener -- chaque événement MQTT est à la fois
 * sauvegardé en base ET diffusé en direct aux clients connectés.
 */
@Configuration
@EnableWebSocketMessageBroker
public class WebSocketConfig implements WebSocketMessageBrokerConfigurer {

    @Override
    public void registerStompEndpoints(StompEndpointRegistry registry) {
        // Point d'entrée que le frontend utilisera pour se connecter.
        // withSockJS() : repli automatique si le navigateur/réseau ne
        // supporte pas les WebSockets natifs (proxy d'entreprise, etc.).
        registry.addEndpoint("/ws")
                .setAllowedOrigins("http://localhost:5173")
                .withSockJS();
    }

    @Override
    public void configureMessageBroker(MessageBrokerRegistry registry) {
        // "/topic" : préfixe conventionnel STOMP pour les messages
        // broadcastés à plusieurs abonnés (par opposition à "/queue" pour
        // un message ciblant un seul destinataire, non utilisé ici).
        registry.enableSimpleBroker("/topic");
    }
}
