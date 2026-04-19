# PostgreSQL Setup Script for Windows
# This script helps set up PostgreSQL for the UM CRM application

Write-Host "=== UM CRM - PostgreSQL Setup ===" -ForegroundColor Green
Write-Host ""

$options = @("1. Use Docker (Recommended)", "2. Use WSL2 PostgreSQL", "3. Install Local PostgreSQL", "4. Use Custom Connection String")
Write-Host "Select PostgreSQL setup option:" -ForegroundColor Yellow
for ($i = 0; $i -lt $options.Count; $i++) {
    Write-Host "$($options[$i])"
}
Write-Host ""

$choice = Read-Host "Enter your choice (1-4)"

switch ($choice) {
    "1" {
        Write-Host "`n=== Docker Setup ===" -ForegroundColor Cyan
        Write-Host "Make sure Docker Desktop is installed and running."
        Write-Host ""
        Write-Host "Run this command to start PostgreSQL in Docker:" -ForegroundColor Yellow
        Write-Host @"
docker run -d `
  --name um-crm-postgres `
  -e POSTGRES_USER=user `
  -e POSTGRES_PASSWORD=password `
  -e POSTGRES_DB=um_crm `
  -p 5432:5432 `
  postgres:16-alpine
"@ -ForegroundColor Gray
        
        Write-Host ""
        Write-Host "After Docker starts, the .env file is ready to use!" -ForegroundColor Green
    }
    
    "2" {
        Write-Host "`n=== WSL2 PostgreSQL Setup ===" -ForegroundColor Cyan
        Write-Host "Install PostgreSQL in WSL2:" -ForegroundColor Yellow
        Write-Host @"
wsl
sudo apt update
sudo apt install postgresql postgresql-contrib
sudo service postgresql start
sudo -u postgres psql -c "CREATE DATABASE um_crm;"
sudo -u postgres psql -c "CREATE USER user WITH PASSWORD 'password';"
sudo -u postgres psql -c "ALTER ROLE user WITH CREATEDB;"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE um_crm TO user;"
"@ -ForegroundColor Gray
        
        Write-Host ""
        Write-Host "Update .env file with WSL PostgreSQL connection:" -ForegroundColor Yellow
        Write-Host "DATABASE_URL=postgresql://user:password@localhost:5432/um_crm" -ForegroundColor Gray
    }
    
    "3" {
        Write-Host "`n=== Local PostgreSQL Installation ===" -ForegroundColor Cyan
        Write-Host "Download PostgreSQL 16 for Windows from: https://www.postgresql.org/download/windows/" -ForegroundColor Yellow
        Write-Host ""
        Write-Host "During installation:" -ForegroundColor Yellow
        Write-Host "- Set password for 'postgres' user to 'password' (or change .env)"
        Write-Host "- Port: 5432"
        Write-Host "- Locale: [Default]"
        Write-Host ""
        Write-Host "After installation, run these commands in pgAdmin or psql:" -ForegroundColor Yellow
        Write-Host @"
CREATE DATABASE um_crm;
CREATE USER ""user"" WITH PASSWORD 'password';
ALTER ROLE ""user"" WITH CREATEDB;
GRANT ALL PRIVILEGES ON DATABASE um_crm TO ""user"";
"@ -ForegroundColor Gray
    }
    
    "4" {
        Write-Host "`n=== Custom Connection String ===" -ForegroundColor Cyan
        $dbUrl = Read-Host "Enter your PostgreSQL connection string (postgresql://user:password@host:port/dbname)"
        
        # Update .env file
        Set-Content -Path "backend\.env" -Value "DATABASE_URL=$dbUrl"
        Write-Host "✓ .env file updated!" -ForegroundColor Green
    }
    
    default {
        Write-Host "Invalid choice!" -ForegroundColor Red
        exit 1
    }
}

Write-Host ""
Write-Host "=== Next Steps ===" -ForegroundColor Green
Write-Host "1. Make sure PostgreSQL is running"
Write-Host "2. Run the backend:"
Write-Host "   cd backend"
Write-Host "   python -m uvicorn main:app --reload"
Write-Host "3. The database tables will be created automatically on first run"
Write-Host ""
