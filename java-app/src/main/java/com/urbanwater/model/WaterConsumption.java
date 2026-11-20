package com.urbanwater.model;

import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.PositiveOrZero;

public record WaterConsumption(
        Long id,

        @NotBlank(message = "Date is required")
        String date,

        @NotBlank(message = "Zone ID is required")
        String zoneId,

        @PositiveOrZero(message = "Population cannot be negative")
        int populationEst,

        @PositiveOrZero(message = "Billed consumption cannot be negative")
        double billedConsumptionLiters,

        @PositiveOrZero(message = "Production volume cannot be negative")
        double productionVolumeLiters,

        @PositiveOrZero(message = "Average pressure cannot be negative")
        double avgPressureBar
) {
}