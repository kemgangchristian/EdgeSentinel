package com.edgesentinel.backend.config;

import org.eclipse.paho.client.mqttv3.MqttConnectOptions;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.integration.channel.DirectChannel;
import org.springframework.integration.mqtt.core.DefaultMqttPahoClientFactory;
import org.springframework.integration.mqtt.core.MqttPahoClientFactory;
import org.springframework.integration.mqtt.inbound.MqttPahoMessageDrivenChannelAdapter;
import org.springframework.messaging.MessageChannel;

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

    @Bean
    public MqttPahoClientFactory mqttClientFactory() {
        DefaultMqttPahoClientFactory factory = new DefaultMqttPahoClientFactory();
        MqttConnectOptions options = new MqttConnectOptions();
        options.setServerURIs(new String[] { brokerUrl });
        // Session propre à chaque connexion : ne conserve pas les messages
        // en attente d'un abonnement précédent -- cohérent avec un backend
        // qui redémarre proprement plutôt que de reprendre un état MQTT
        // potentiellement obsolète.
        options.setCleanSession(true);
        factory.setConnectionOptions(options);
        return factory;
    }

    @Bean
    public MqttPahoMessageDrivenChannelAdapter mqttInboundAdapter() {
        MqttPahoMessageDrivenChannelAdapter adapter =
                new MqttPahoMessageDrivenChannelAdapter(clientId, mqttClientFactory(), topic);
        // QoS 1 côté consommateur également, cohérent avec la publication
        // QoS 1 déjà configurée côté agent Edge (config.yaml, section mqtt).
        adapter.setQos(1);
        adapter.setCompletionTimeout(5000);
        adapter.setOutputChannel(mqttInputChannel());
        return adapter;
    }

    @Bean
    public MessageChannel mqttInputChannel() {
        return new DirectChannel();
    }
}
