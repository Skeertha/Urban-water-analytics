
$ErrorActionPreference = "Stop"

Write-Host "Step 1: Running ETL pipeline..."
python .\python\05_etl_quality_pipeline.py

if ($LASTEXITCODE -ne 0) {
    throw "ETL pipeline failed."
}

Write-Host "`nStep 2: Running automated tests..."
python -m unittest discover -s tests -p "test*.py" -v

if ($LASTEXITCODE -ne 0) {
    throw "Automated ETL tests failed."
}

Write-Host "`nETL pipeline and all automated tests completed successfully."
