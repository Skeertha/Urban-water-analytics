package com.urbanwater;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.AutoConfigureMockMvc;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.http.MediaType;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.test.web.servlet.MockMvc;
import org.springframework.test.web.servlet.MvcResult;

import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.*;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.*;

@SpringBootTest
@AutoConfigureMockMvc
class WaterConsumptionCrudTest {

    @Autowired
    private MockMvc mockMvc;

    @Autowired
    private JdbcTemplate jdbcTemplate;

    @Autowired
    private ObjectMapper objectMapper;

    @BeforeEach
    void cleanDatabase() {
        jdbcTemplate.update("DELETE FROM water_consumption");
    }

    @Test
    void shouldCreateReadUpdateAndDeleteRecord() throws Exception {

        String record = """
                {
                    "date": "2023-01-01",
                    "zoneId": "Z01",
                    "populationEst": 48000,
                    "billedConsumptionLiters": 4532180,
                    "productionVolumeLiters": 5085205,
                    "avgPressureBar": 3.47
                }
                """;

        MvcResult createResult = mockMvc.perform(post("/api/water/records")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(record))
                .andExpect(status().isCreated())
                .andExpect(jsonPath("$.zoneId").value("Z01"))
                .andReturn();

        JsonNode created = objectMapper.readTree(
                createResult.getResponse().getContentAsString()
        );

        long id = created.get("id").asLong();

        mockMvc.perform(get("/api/water/records/{id}", id))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.date").value("2023-01-01"));

        mockMvc.perform(get("/api/water/records"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.length()").value(1));

        String updatedRecord = """
                {
                    "date": "2023-01-02",
                    "zoneId": "Z01",
                    "populationEst": 48000,
                    "billedConsumptionLiters": 4028075,
                    "productionVolumeLiters": 4519588,
                    "avgPressureBar": 3.59
                }
                """;

        mockMvc.perform(put("/api/water/records/{id}", id)
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(updatedRecord))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.date").value("2023-01-02"))
                .andExpect(jsonPath("$.billedConsumptionLiters").value(4028075));

        mockMvc.perform(delete("/api/water/records/{id}", id))
                .andExpect(status().isNoContent());

        mockMvc.perform(get("/api/water/records/{id}", id))
                .andExpect(status().isNotFound());
    }

    @Test
    void shouldReturnStructuredErrorForMissingRecord() throws Exception {
        mockMvc.perform(get("/api/water/records/-1"))
                .andExpect(status().isNotFound())
                .andExpect(jsonPath("$.status").value(404))
                .andExpect(jsonPath("$.error").value("Not Found"))
                .andExpect(jsonPath("$.message")
                        .value("Water consumption record not found: -1"));
    }
}
