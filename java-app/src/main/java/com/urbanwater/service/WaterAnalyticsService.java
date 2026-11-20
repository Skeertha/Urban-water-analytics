package com.urbanwater.service;

import org.springframework.stereotype.Service;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

@Service
public class WaterAnalyticsService {

    private Path getDataPath(String fileName) throws IOException {
        Path path = Path.of("..", "data", "raw", fileName);

        if (!Files.exists(path)) {
            path = Path.of("data", "raw", fileName);
        }

        if (!Files.exists(path)) {
            throw new IOException("CSV file not found: " + fileName);
        }

        return path;
    }

    public Map<String, Object> getSummary() throws IOException {
        Path csvPath = getDataPath("consumption_daily.csv");

        long totalRecords = 0;
        double totalProduction = 0;
        double totalBilled = 0;

        try (var reader = Files.newBufferedReader(csvPath)) {
            String line = reader.readLine();

            while ((line = reader.readLine()) != null) {
                if (line.isBlank()) {
                    continue;
                }

                String[] columns = line.split(",");

                totalProduction += Double.parseDouble(columns[4]);
                totalBilled += Double.parseDouble(columns[3]);
                totalRecords++;
            }
        }

        double nrw = totalProduction - totalBilled;
        double nrwPercentage = totalProduction == 0
                ? 0
                : (nrw / totalProduction) * 100;

        return Map.of(
                "totalRecords", totalRecords,
                "productionLiters", totalProduction,
                "billedLiters", totalBilled,
                "nrwLiters", nrw,
                "nrwPercentage", Math.round(nrwPercentage * 100.0) / 100.0
        );
    }

    public List<Map<String, Object>> getZoneAnalytics() throws IOException {

        Map<String, Map<String, Object>> zones = new LinkedHashMap<>();

        Path zonesPath = getDataPath("zones.csv");

        try (var reader = Files.newBufferedReader(zonesPath)) {
            String line = reader.readLine();

            while ((line = reader.readLine()) != null) {
                if (line.isBlank()) {
                    continue;
                }

                String[] columns = line.split(",");

                Map<String, Object> zone = new LinkedHashMap<>();
                zone.put("zoneId", columns[0]);
                zone.put("zoneName", columns[1]);
                zone.put("zoneType", columns[2]);
                zone.put("population", Integer.parseInt(columns[3]));
                zone.put("households", Integer.parseInt(columns[4]));
                zone.put("areaSqKm", Double.parseDouble(columns[5]));
                zone.put("totalProductionLiters", 0.0);
                zone.put("totalBilledLiters", 0.0);
                zone.put("totalRecords", 0L);

                zones.put(columns[0], zone);
            }
        }

        Path consumptionPath = getDataPath("consumption_daily.csv");

        try (var reader = Files.newBufferedReader(consumptionPath)) {
            String line = reader.readLine();

            while ((line = reader.readLine()) != null) {
                if (line.isBlank()) {
                    continue;
                }

                String[] columns = line.split(",");

                Map<String, Object> zone = zones.get(columns[1]);

                if (zone == null) {
                    throw new IOException(
                            "Unknown zone ID in consumption data: " + columns[1]
                    );
                }

                double billed = Double.parseDouble(columns[3]);
                double production = Double.parseDouble(columns[4]);

                double currentBilled =
                        (double) zone.get("totalBilledLiters");
                double currentProduction =
                        (double) zone.get("totalProductionLiters");
                long currentRecords =
                        (long) zone.get("totalRecords");

                zone.put("totalBilledLiters", currentBilled + billed);
                zone.put("totalProductionLiters",
                        currentProduction + production);
                zone.put("totalRecords", currentRecords + 1);
            }
        }

        List<Map<String, Object>> results = new ArrayList<>();

        for (Map<String, Object> zone : zones.values()) {

            double production =
                    (double) zone.get("totalProductionLiters");
            double billed =
                    (double) zone.get("totalBilledLiters");

            double nrw = production - billed;
            double nrwPercentage = production == 0
                    ? 0
                    : (nrw / production) * 100;

            zone.put("nrwLiters", nrw);
            zone.put("nrwPercentage",
                    Math.round(nrwPercentage * 100.0) / 100.0);

            results.add(zone);
        }

        return results;
    }
}
