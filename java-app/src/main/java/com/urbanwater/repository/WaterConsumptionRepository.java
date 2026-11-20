package com.urbanwater.repository;

import com.urbanwater.model.WaterConsumption;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.stereotype.Repository;

import java.util.List;
import java.util.Optional;

@Repository
public class WaterConsumptionRepository {

    private final JdbcTemplate jdbcTemplate;

    public WaterConsumptionRepository(JdbcTemplate jdbcTemplate) {
        this.jdbcTemplate = jdbcTemplate;
    }

    private WaterConsumption mapRow(
            java.sql.ResultSet rs,
            int rowNum
    ) throws java.sql.SQLException {

        return new WaterConsumption(
                rs.getLong("id"),
                rs.getString("date"),
                rs.getString("zone_id"),
                rs.getInt("population_est"),
                rs.getDouble("billed_consumption_liters"),
                rs.getDouble("production_volume_liters"),
                rs.getDouble("avg_pressure_bar")
        );
    }

    public List<WaterConsumption> findAll() {
        return jdbcTemplate.query(
                "SELECT * FROM water_consumption ORDER BY id",
                this::mapRow
        );
    }

    public Optional<WaterConsumption> findById(Long id) {
        List<WaterConsumption> results = jdbcTemplate.query(
                "SELECT * FROM water_consumption WHERE id = ?",
                this::mapRow,
                id
        );

        return results.stream().findFirst();
    }

    public WaterConsumption save(WaterConsumption record) {
        String sql = """
                INSERT INTO water_consumption (
                    date, zone_id, population_est,
                    billed_consumption_liters,
                    production_volume_liters,
                    avg_pressure_bar
                )
                VALUES (?, ?, ?, ?, ?, ?)
                RETURNING id
                """;

        Long id = jdbcTemplate.queryForObject(
                sql,
                Long.class,
                record.date(),
                record.zoneId(),
                record.populationEst(),
                record.billedConsumptionLiters(),
                record.productionVolumeLiters(),
                record.avgPressureBar()
        );

        return new WaterConsumption(
                id,
                record.date(),
                record.zoneId(),
                record.populationEst(),
                record.billedConsumptionLiters(),
                record.productionVolumeLiters(),
                record.avgPressureBar()
        );
    }

    public boolean update(Long id, WaterConsumption record) {
        int rows = jdbcTemplate.update(
                """
                UPDATE water_consumption
                SET date = ?,
                    zone_id = ?,
                    population_est = ?,
                    billed_consumption_liters = ?,
                    production_volume_liters = ?,
                    avg_pressure_bar = ?
                WHERE id = ?
                """,
                record.date(),
                record.zoneId(),
                record.populationEst(),
                record.billedConsumptionLiters(),
                record.productionVolumeLiters(),
                record.avgPressureBar(),
                id
        );

        return rows > 0;
    }

    public boolean delete(Long id) {
        int rows = jdbcTemplate.update(
                "DELETE FROM water_consumption WHERE id = ?",
                id
        );

        return rows > 0;
    }
}
