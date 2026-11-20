package com.urbanwater.controller;

import com.urbanwater.service.WaterAnalyticsService;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import java.io.IOException;
import java.util.List;
import java.util.Map;

@RestController
@RequestMapping("/api/water")
public class WaterAnalyticsController {

    private final WaterAnalyticsService waterAnalyticsService;

    public WaterAnalyticsController(WaterAnalyticsService waterAnalyticsService) {
        this.waterAnalyticsService = waterAnalyticsService;
    }

    @GetMapping("/summary")
    public Map<String, Object> getSummary() throws IOException {
        return waterAnalyticsService.getSummary();
    }

    @GetMapping("/zones")
    public List<Map<String, Object>> getZoneAnalytics() throws IOException {
        return waterAnalyticsService.getZoneAnalytics();
    }
}