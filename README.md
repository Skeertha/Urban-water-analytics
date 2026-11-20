# Urban Water Analytics REST API

A Java-based REST API that analyzes urban water supply data across eight service zones. The application processes CSV datasets and calculates water production, billed consumption and Non-Revenue Water (NRW).

## Technology Stack

- Java 21
- Spring Boot 3.5.7
- Spring Web
- Maven 3.10.1
- JUnit 5
- MockMvc
- CSV file processing

## Features

- REST API development using Spring Boot
- Application health monitoring
- Water production and billed consumption analysis
- Non-Revenue Water (NRW) calculation
- Zone-level analytics across eight service zones
- CSV data processing
- Automated API testing

## REST API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| GET | `/api/health` | Checks application health |
| GET | `/api/water/summary` | Returns overall water analytics |
| GET | `/api/water/zones` | Returns analytics for all eight zones |

## Project Results

The API processes 8,768 daily consumption records across eight zones.

| Metric | Result |
|---|---:|
| Daily records | 8,768 |
| Water production | 45,957,213,436 liters |
| Billed consumption | 40,703,346,640 liters |
| Non-Revenue Water | 5,253,866,796 liters |
| NRW percentage | 11.43% |
| Records per zone | 1,096 |

## Project Structure

```text
urban-water-analytics/
├── java-app/
│   ├── pom.xml
│   └── src/
│       ├── main/
│       │   └── java/com/urbanwater/
│       │       ├── UrbanWaterApplication.java
│       │       ├── controller/
│       │       │   ├── HealthController.java
│       │       │   └── WaterAnalyticsController.java
│       │       └── service/
│       │           └── WaterAnalyticsService.java
│       └── test/
│           └── java/com/urbanwater/
│               └── WaterAnalyticsApiTest.java
├── data/
│   └── raw/
│       ├── consumption_daily.csv
│       └── zones.csv
└── README.md
