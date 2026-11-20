CREATE TABLE IF NOT EXISTS water_consumption (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date TEXT NOT NULL,
    zone_id TEXT NOT NULL,
    population_est INTEGER NOT NULL,
    billed_consumption_liters REAL NOT NULL,
    production_volume_liters REAL NOT NULL,
    avg_pressure_bar REAL NOT NULL
);
