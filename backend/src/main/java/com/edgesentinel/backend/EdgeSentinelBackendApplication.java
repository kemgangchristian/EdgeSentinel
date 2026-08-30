package com.edgesentinel.backend;

import org.springframework.boot.SpringApplication;
import org.springframework.data.web.config.EnableSpringDataWebSupport;
import org.springframework.boot.autoconfigure.SpringBootApplication;

@SpringBootApplication
@EnableSpringDataWebSupport(pageSerializationMode = EnableSpringDataWebSupport.PageSerializationMode.VIA_DTO)
public class EdgeSentinelBackendApplication {

	public static void main(String[] args) {
		SpringApplication.run(EdgeSentinelBackendApplication.class, args);
	}

}
