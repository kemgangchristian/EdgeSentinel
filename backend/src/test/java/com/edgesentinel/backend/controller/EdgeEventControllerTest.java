package com.edgesentinel.backend.controller;

import com.edgesentinel.backend.entity.EdgeEvent;
import com.edgesentinel.backend.repository.EdgeEventRepository;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.webmvc.test.autoconfigure.WebMvcTest;
import org.springframework.test.context.bean.override.mockito.MockitoBean;
import org.springframework.data.domain.PageImpl;
import org.springframework.test.web.servlet.MockMvc;

import java.util.List;
import java.util.Optional;

import static org.mockito.ArgumentMatchers.any;
import static org.mockito.ArgumentMatchers.eq;
import static org.mockito.Mockito.when;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

/**
 * Teste EdgeEventController isolément : le repository est mocké (Mockito),
 * aucune vraie base de données n'est démarrée -- rapide et reproductible,
 * cohérent avec le principe déjà appliqué côté agent Edge (mock de
 * paho-mqtt dans test_sinks.py).
 */
@WebMvcTest(EdgeEventController.class)
class EdgeEventControllerTest {

    @Autowired
    private MockMvc mockMvc;

    @MockitoBean
    private EdgeEventRepository repository;

    private EdgeEvent sampleEvent() {
        return new EdgeEvent(
                "PI-001", "INTRUSION", 0.9, "ZONE_A",
                "2026-08-27T22:19:16Z", 1, "captures/sample.jpg"
        );
    }

    @Test
    void listEvents_returnsPagedEvents() throws Exception {
        when(repository.findAll(any(org.springframework.data.domain.Pageable.class)))
                .thenReturn(new PageImpl<>(List.of(sampleEvent())));

        mockMvc.perform(get("/api/events"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.content[0].deviceId").value("PI-001"))
                .andExpect(jsonPath("$.content[0].eventType").value("INTRUSION"));
    }

    @Test
    void getEvent_returnsEventWhenFound() throws Exception {
        when(repository.findById(eq(1L))).thenReturn(Optional.of(sampleEvent()));

        mockMvc.perform(get("/api/events/1"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.eventType").value("INTRUSION"));
    }

    @Test
    void getEvent_returns404WhenNotFound() throws Exception {
        when(repository.findById(eq(9999L))).thenReturn(Optional.empty());

        mockMvc.perform(get("/api/events/9999"))
                .andExpect(status().isNotFound());
    }
}
