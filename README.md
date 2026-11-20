# Urban Water Analytics REST API

A Java-based REST API for analyzing urban water supply data across eight service zones. The application provides water consumption analytics, Non-Revenue Water (NRW) calculations, and CRUD operations backed by SQLite.

## Technology Stack

- Java 21
- Spring Boot 3.5.7
- Spring Web
- Spring JDBC
- SQLite
- Maven
- JUnit 5
- Spring Boot Test
- MockMvc
- Jackson

## Features

- Water production and billed consumption analytics
- Non-Revenue Water (NRW) calculations
- Zone-level analytics across eight service zones
- REST API health endpoint
- Water consumption record management
- Create, read, update, and delete operations
- SQLite database persistence
- Centralized exception handling
- Structured JSON error responses
- Automated API integration tests
- GitHub Actions CI workflow
- Request input validation using Jakarta Bean Validation
- HTTP 400 responses for invalid API request data

## REST API Endpoints

| HTTP Method | Endpoint | Description |
|---|---|---|
| GET | `/api/health` | Check application health |
| GET | `/api/water/summary` | Retrieve overall water analytics |
| GET | `/api/water/zones` | Retrieve zone-level analytics |
| POST | `/api/water/records` | Create a consumption record |
| GET | `/api/water/records` | Retrieve all records |
| GET | `/api/water/records/{id}` | Retrieve a record by ID |
| PUT | `/api/water/records/{id}` | Update a record |
| DELETE | `/api/water/records/{id}` | Delete a record |

## Sample API Request

**POST** `/api/water/records`

```json
{
  "date": "2023-01-01",
  "zoneId": "Z01",
  "populationEst": 48000,
  "billedConsumptionLiters": 4532180,
  "productionVolumeLiters": 5085205,
  "avgPressureBar": 3.47
}
```

## Error Handling

The application uses a custom `ResourceNotFoundException` and centralized exception handling through `@RestControllerAdvice`.

Example: requesting a record that does not exist returns HTTP 404.

```json
{
  "status": 404,
  "error": "Not Found",
  "message": "Water consumption record not found: -1"
}
```

## Project Analytics

The analytics API processes 8,768 daily consumption records across eight service zones.

| Metric | Result |
|---|---:|
| Daily consumption records | 8,768 |
| Water production | 45,957,213,436 liters |
| Billed consumption | 40,703,346,640 liters |
| Non-Revenue Water | 5,253,866,796 liters |
| NRW percentage | 11.43% |
| Records per zone | 1,096 |

## Application Architecture

The application follows a layered architecture:

**REST Controller → Service → Repository → SQLite Database**

- **Controller Layer:** Exposes REST endpoints and handles HTTP requests.
- **Service Layer:** Implements analytics and business logic.
- **Repository Layer:** Performs database operations using Spring JDBC and `JdbcTemplate`.
- **Model Layer:** Represents water consumption records.
- **Exception Layer:** Provides centralized API error handling.

## Project Structure

```text
Urban-water-analytics/
├── .github/
│   └── workflows/
│       └── java-ci.yml
├── data/
│   └── raw/
│       ├── consumption_daily.csv
│       └── zones.csv
├── java-app/
│   ├── pom.xml
│   └── src/
│       ├── main/
│       │   ├── java/com/urbanwater/
│       │   │   ├── UrbanWaterApplication.java
│       │   │   ├── controller/
│       │   │   ├── exception/
│       │   │   ├── model/
│       │   │   ├── repository/
│       │   │   └── service/
│       │   └── resources/
│       │       ├── application.properties
│       │       └── schema.sql
│       └── test/java/com/urbanwater/
│           ├── WaterAnalyticsApiTest.java
│           └── WaterConsumptionCrudTest.java
└── README.md
```

## Run Locally

### Prerequisites

- Java 21
- Apache Maven 3.10.1 or compatible version

## Testing

The project includes seven automated API integration tests using JUnit 5, Spring Boot Test, and MockMvc.

Test coverage includes:

- Water analytics API responses
- Creating, retrieving, updating, and deleting water consumption records
- Handling requests for non-existent records with HTTP 404 responses
- Rejecting blank date and zone ID values
- Rejecting negative population values with HTTP 400 responses

Run the tests from the `java-app` directory:

```bash
mvn clean verify
```

The test suite completed successfully with **7 tests, 0 failures, and 0 errors** in the local environment.

## AI-Assisted Engineering

AI assistance was used as a development support tool throughout this project.

Areas where AI assistance supported the engineering workflow:

- Understanding Java OOP concepts and Spring Boot application structure
- Supporting implementation of REST controllers, service classes, and JDBC repository operations
- Troubleshooting SQLite database connectivity and API errors
- Improving input validation and centralized exception handling
- Supporting the creation and review of JUnit integration tests
- Reviewing README documentation and GitHub Actions CI configuration

All generated or suggested changes were reviewed, executed, and tested in the local development environment before being committed and pushed to GitHub.

AI assistance supported development and learning; it did not replace implementation verification or test execution.