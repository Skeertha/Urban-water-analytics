# Urban Water Analytics

An urban water analytics project combining a **Java Spring Boot REST API** with **Python-based data analytics and data-quality validation**. The project analyzes water consumption, production, billing, infrastructure, weather, and leakage data across eight service zones.

## Project Components

1. **Java REST API:** Water analytics, NRW calculations, and CRUD operations backed by SQLite.
2. **Python Analytics:** Exploratory data analysis, demand forecasting, leak anomaly detection, and ETL data-quality validation.

## Technology Stack

### Java
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

### Python
- Python
- Pandas
- NumPy
- Matplotlib
- Seaborn
- Scikit-learn
- unittest

## Features

### Java REST API
- Water production and billed consumption analytics
- Non-Revenue Water (NRW) calculations
- Zone-level analytics across eight service zones
- REST API health endpoint
- Water consumption record management
- Create, read, update, and delete operations
- SQLite database persistence
- Centralized exception handling
- Structured JSON error responses
- Request validation using Jakarta Bean Validation
- HTTP 400 responses for invalid API request data
- GitHub Actions CI workflow
- Automated API integration tests

### Python Analytics
- Exploratory data analysis and visualization
- Water demand forecasting
- Leak anomaly detection
- ETL data-quality validation across seven CSV datasets
- Missing and blank value detection
- Duplicate business-key validation
- Numeric range and data-type validation
- Foreign-key relationship checks
- Date and business-rule validation
- JSON quality report and CSV issue report generation
- Automated unit tests for data-quality validation

## Python Analytics and ETL Pipeline

The Python workflow processes seven datasets:

| Dataset | Records |
|---|---:|
| zones | 8 |
| reservoirs | 8 |
| pipe_network | 77 |
| weather_daily | 8,768 |
| consumption_daily | 8,768 |
| leakage_incidents | 24 |
| billing_monthly | 288 |
| **Total** | **17,941** |

### Data-quality validation results

The ETL pipeline validates the datasets for completeness, uniqueness, consistency, relationships, valid dates, numeric constraints, and business rules.

| Validation metric | Result |
|---|---:|
| Datasets checked | 7 |
| Total records checked | 17,941 |
| Missing values detected | 0 |
| Duplicate business-key rows | 0 |
| Total validation issues | 0 |
| Overall pipeline status | PASS |

**Generated reports:**
- `data/processed/etl_quality_report.json`
- `data/processed/data_quality_issues.csv`

The pipeline reports validation results without modifying the original source CSV files.

## Python Scripts

| Script | Purpose |
|---|---|
| `01_generate_data.py` | Generate project datasets |
| `02_eda_and_visualization.py` | Exploratory data analysis and visualization |
| `03_demand_forecasting_model.py` | Water demand forecasting |
| `04_leak_anomaly_detection.py` | Leak anomaly detection |
| `05_data_quality_pipeline.py` | ETL data-quality validation |

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

The Java application uses a custom `ResourceNotFoundException` and centralized exception handling through `@RestControllerAdvice`.

Example: requesting a record that does not exist returns HTTP 404.

```json
{
  "status": 404,
  "error": "Not Found",
  "message": "Water consumption record not found: -1"
}
```

## Project Analytics

The Java analytics API processes 8,768 daily consumption records across eight service zones.

| Metric | Result |
|---|---:|
| Daily consumption records | 8,768 |
| Water production | 45,957,213,436 liters |
| Billed consumption | 40,703,346,640 liters |
| Non-Revenue Water | 5,253,866,796 liters |
| NRW percentage | 11.43% |
| Records per zone | 1,096 |

## Application Architecture

### Java application

The application follows a layered architecture:

**REST Controller → Service → Repository → SQLite Database**

- **Controller Layer:** Exposes REST endpoints and handles HTTP requests.
- **Service Layer:** Implements analytics and business logic.
- **Repository Layer:** Performs database operations using Spring JDBC and `JdbcTemplate`.
- **Model Layer:** Represents water consumption records.
- **Exception Layer:** Provides centralized API error handling.

### Python data pipeline

**CSV Datasets → Pandas Data Processing → Data-quality Validation → JSON and CSV Reports**

The pipeline checks data quality before reporting validation results.

## Project Structure

```text
Urban-water-analytics/
├── .github/
│   └── workflows/
│       └── java-ci.yml
├── data/
│   ├── raw/
│   │   ├── billing_monthly.csv
│   │   ├── consumption_daily.csv
│   │   ├── leakage_incidents.csv
│   │   ├── pipe_network.csv
│   │   ├── reservoirs.csv
│   │   ├── weather_daily.csv
│   │   └── zones.csv
│   └── processed/
│       ├── etl_quality_report.json
│       └── data_quality_issues.csv
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
├── python/
│   ├── 01_generate_data.py
│   ├── 02_eda_and_visualization.py
│   ├── 03_demand_forecasting_model.py
│   ├── 04_leak_anomaly_detection.py
│   ├── 05_data_quality_pipeline.py
│   └── tests/
│       ├── __init__.py
│       ├── test_data_quality_edge_cases.py
│       └── test_data_quality_pipeline.py
├── requirements.txt
├── .gitignore
└── README.md
```

## Run Locally

### Prerequisites

- Java 21
- Apache Maven 3.10.1 or compatible version
- Python 3
- pip

### Run Python ETL Pipeline

Install dependencies:

```bash
pip install -r requirements.txt
```

Run the data-quality pipeline from the project root:

```bash
python python/05_data_quality_pipeline.py
```

### Run Python Unit Tests

```bash
python -m unittest discover -s python -p "test_*.py" -v
```

### Run Java Application

Navigate to the Java application directory:

```bash
cd java-app
```

Run the application using Maven:

```bash
mvn spring-boot:run
```

## Testing

### Python tests

The Python data-quality pipeline includes nine automated unit tests covering:

- Numeric range validation
- Foreign-key validation
- Date-order validation
- Business-rule validation
- Duplicate business-key detection
- Missing-file detection
- Missing-column detection
- Blank-value detection
- Invalid-numeric detection

**Verified result: 9 tests passed, 0 failures.**

### Java tests

The Java application includes seven automated API integration tests using JUnit 5, Spring Boot Test, and MockMvc.

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

**Previously verified result: 7 tests passed, 0 failures, and 0 errors.**

## AI-Assisted Engineering

AI assistance was used as a development support tool throughout this project.

Areas where AI assistance supported the engineering workflow:

- Understanding Java OOP concepts and Spring Boot application structure
- Supporting implementation of REST controllers, service classes, and JDBC repository operations
- Troubleshooting SQLite database connectivity and API errors
- Improving input validation and centralized exception handling
- Supporting Python data-processing and validation workflows
- Creating and reviewing automated unit and integration tests
- Reviewing documentation and GitHub Actions CI configuration

All generated or suggested changes were reviewed, executed, and tested in the local development environment before being committed and pushed to GitHub.

AI assistance supported development and learning; it did not replace implementation verification or test execution.