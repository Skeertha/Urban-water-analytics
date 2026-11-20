package com.urbanwater.model;

public record WaterConsumption(
        Long id,
        String date,
        String zoneId,
        int populationEst,
        double billedConsumptionLiters,
        double productionVolumeLiters,
        double avgPressureBar
) {
}
