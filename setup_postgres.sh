#!/bin/bash

# Basketball Analytics - PostgreSQL Setup Script
# This script sets up PostgreSQL database for the basketball analytics platform

set -e

echo "🏀 Basketball Analytics - PostgreSQL Setup"
echo "==========================================="

# Default database configuration
DB_NAME="basketball_db"
DB_USER="basketball_user"
DB_PASSWORD="basketball_pass"
DB_HOST="localhost"
DB_PORT="5432"

# Check if PostgreSQL is installed
if ! command -v psql &> /dev/null; then
    echo "❌ PostgreSQL is not installed. Please install PostgreSQL first."
    echo "Ubuntu/Debian: sudo apt-get install postgresql postgresql-contrib"
    echo "macOS: brew install postgresql"
    echo "CentOS/RHEL: sudo yum install postgresql-server postgresql-contrib"
    exit 1
fi

# Check if PostgreSQL service is running
if ! pg_isready -h "$DB_HOST" -p "$DB_PORT" &> /dev/null; then
    echo "❌ PostgreSQL service is not running."
    echo "Start PostgreSQL service:"
    echo "Ubuntu/Debian: sudo systemctl start postgresql"
    echo "macOS: brew services start postgresql"
    exit 1
fi

echo "✅ PostgreSQL is installed and running"

# Create database and user
echo "📊 Creating database and user..."

# Switch to postgres user and create database
sudo -u postgres psql -c "DROP DATABASE IF EXISTS $DB_NAME;" || true
sudo -u postgres psql -c "DROP USER IF EXISTS $DB_USER;" || true

sudo -u postgres psql -c "CREATE USER $DB_USER WITH PASSWORD '$DB_PASSWORD';"
sudo -u postgres psql -c "CREATE DATABASE $DB_NAME OWNER $DB_USER;"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE $DB_NAME TO $DB_USER;"

echo "✅ Database '$DB_NAME' and user '$DB_USER' created successfully"

# Update database URL in environment
DB_URL="postgresql://$DB_USER:$DB_PASSWORD@$DB_HOST:$DB_PORT/$DB_NAME"

echo "🔧 Setting up environment..."
echo "DATABASE_URL=$DB_URL" > .env

echo "🗄️ Running database migrations..."
export DATABASE_URL="$DB_URL"

# Install Python dependencies if not already installed
if ! python -c "import alembic" &> /dev/null; then
    echo "📦 Installing required Python packages..."
    pip install alembic psycopg2-binary sqlalchemy
fi

# Update alembic.ini with PostgreSQL URL
sed -i "s|sqlalchemy.url = .*|sqlalchemy.url = $DB_URL|" alembic.ini

# Run migrations
alembic upgrade head

echo "✅ Database setup completed successfully!"
echo ""
echo "🔗 Connection Details:"
echo "Database: $DB_NAME"
echo "User: $DB_USER" 
echo "Host: $DB_HOST"
echo "Port: $DB_PORT"
echo "URL: $DB_URL"
echo ""
echo "🚀 You can now start the application:"
echo "uvicorn backend.app.main:app --host 0.0.0.0 --port 8000"
echo ""
echo "📈 Dashboard will be available at: http://localhost:8000/dashboard"