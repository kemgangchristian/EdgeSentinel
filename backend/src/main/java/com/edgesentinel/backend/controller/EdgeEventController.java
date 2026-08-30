package com.edgesentinel.backend.controller;

import com.edgesentinel.backend.entity.EdgeEvent;
import com.edgesentinel.backend.repository.EdgeEventRepository;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.data.domain.Sort;
import org.springframework.data.web.PageableDefault;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

/**
 * API REST de consultation des événements persistés -- lecture seule
 * (la seule voie d'écriture est le listener MQTT, EdgeEventListener).
 */
@RestController
@RequestMapping("/api/events")
public class EdgeEventController {

    private final EdgeEventRepository repository;

    public EdgeEventController(EdgeEventRepository repository) {
        this.repository = repository;
    }

    // GET /api/events?page=0&size=20 -- pagination automatique fournie
    // par Spring Data, triée par id décroissant (les plus récents en tête)
    // par défaut si l'appelant ne précise rien.
    @GetMapping
    public Page<EdgeEvent> listEvents(
            @PageableDefault(size = 20, sort = "id", direction = Sort.Direction.DESC) Pageable pageable) {
        return repository.findAll(pageable);
    }

    @GetMapping("/{id}")
    public ResponseEntity<EdgeEvent> getEvent(@PathVariable Long id) {
        return repository.findById(id)
                .map(ResponseEntity::ok)
                .orElse(ResponseEntity.notFound().build());
    }
}
