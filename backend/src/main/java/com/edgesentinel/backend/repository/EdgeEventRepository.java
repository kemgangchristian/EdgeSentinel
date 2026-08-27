package com.edgesentinel.backend.repository;

import com.edgesentinel.backend.entity.EdgeEvent;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

/**
 * Accès aux événements persistés. JpaRepository fournit automatiquement
 * save(), findById(), findAll(), delete()... sans implémentation manuelle
 * -- Spring génère le code au démarrage à partir de cette seule interface.
 */
@Repository
public interface EdgeEventRepository extends JpaRepository<EdgeEvent, Long> {
}
