package com.edgesentinel.backend.config;

import org.springframework.beans.factory.annotation.Value;
import org.springframework.context.annotation.Configuration;
import org.springframework.web.servlet.config.annotation.ResourceHandlerRegistry;
import org.springframework.web.servlet.config.annotation.WebMvcConfigurer;

/**
 * Expose le dossier de captures de l'agent Edge (edge/captures/) via HTTP,
 * pour que le frontend puisse afficher les images annotées. Le chemin est
 * externalisé (application.properties), jamais codé en dur.
 */
@Configuration
public class WebConfig implements WebMvcConfigurer {

    @Value("${app.captures.directory}")
    private String capturesDirectory;

    @Override
    public void addResourceHandlers(ResourceHandlerRegistry registry) {
        String location = capturesDirectory.endsWith("/") ? capturesDirectory : capturesDirectory + "/";
        // Une requête vers /captures/xxx.jpg sert directement le fichier
        // edge/captures/xxx.jpg -- cohérent avec capturePath déjà stocké
        // en base sous la forme "captures/xxx.jpg" (recorder.py).
        registry.addResourceHandler("/captures/**").addResourceLocations("file:" + location);
    }
}
