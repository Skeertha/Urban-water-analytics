package com.urbanwater;

import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.AutoConfigureMockMvc;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.test.web.servlet.MockMvc;

import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

@SpringBootTest
@AutoConfigureMockMvc
class WaterAnalyticsApiTest {

    @Autowired
    private MockMvc mockMvc;

    @Test
    void shouldReturnWaterAnalyticsSummary() throws Exception {
        mockMvc.perform(get("/api/water/summary"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.totalRecords").value(8768))
                .andExpect(jsonPath("$.productionLiters").value(45957213436L))
                .andExpect(jsonPath("$.billedLiters").value(40703346640L))
                .andExpect(jsonPath("$.nrwLiters").value(5253866796L))
                .andExpect(jsonPath("$.nrwPercentage").value(11.43));
    }

    @Test
    void shouldReturnAnalyticsForAllEightZones() throws Exception {
        mockMvc.perform(get("/api/water/zones"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.length()").value(8))
                .andExpect(jsonPath("$[0].zoneId").value("Z01"))
                .andExpect(jsonPath("$[0].totalRecords").value(1096))
                .andExpect(jsonPath("$[7].zoneId").value("Z08"))
                .andExpect(jsonPath("$[7].totalRecords").value(1096));
    }
}