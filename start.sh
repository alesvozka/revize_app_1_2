#!/bin/bash

# =============================================================================
# REVIZE APP - Start Script for Railway/Production Deployment
# =============================================================================
# Tento skript:
#   1. Spustí database migraci
#   2. Pokud migrace uspěje, spustí aplikaci
#   3. Loguje všechny kroky
#
# Použití:
#   chmod +x start.sh
#   ./start.sh
# =============================================================================

set -e  # Ukončit při jakékoliv chybě

# Barvy pro výstup
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Funkce pro logování
log_info() {
    echo -e "${BLUE}ℹ [INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}✓ [SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}⚠ [WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}✗ [ERROR]${NC} $1"
}

# Header
echo ""
echo "=============================================================================="
echo "  🚀 REVIZE APP - DEPLOYMENT START"
echo "=============================================================================="
echo ""

# 1. Kontrola environment variables
log_info "Kontroluji environment variables..."

if [ -z "$DATABASE_URL" ]; then
    log_error "DATABASE_URL není nastavena!"
    log_error "Nastav ji pomocí: export DATABASE_URL='postgresql://...'"
    exit 1
fi

log_success "DATABASE_URL je nastavena"

# 2. Kontrola Python závislostí
log_info "Kontroluji Python závislosti..."

if ! command -v python3 &> /dev/null; then
    log_error "Python3 není nainstalován!"
    exit 1
fi

# Instalace závislostí (pokud ještě nejsou)
if [ -f "requirements.txt" ]; then
    log_info "Instaluji Python závislosti..."
    pip install --quiet --no-cache-dir -r requirements.txt
    log_success "Závislosti nainstalovány"
else
    log_warning "requirements.txt nenalezen"
fi

# 3. Spuštění database migrace
echo ""
log_info "Spouštím database migraci..."
echo "------------------------------------------------------------------------------"

if python3 migrate_db.py; then
    echo "------------------------------------------------------------------------------"
    log_success "Database migrace úspěšně dokončena"
else
    echo "------------------------------------------------------------------------------"
    log_error "Database migrace selhala!"
    log_error "Zkontroluj logy výše pro detaily"
    exit 1
fi

# 4. Kontrola main.py
echo ""
log_info "Kontroluji aplikační soubory..."

if [ ! -f "main.py" ]; then
    log_error "main.py nenalezen!"
    exit 1
fi

log_success "Aplikační soubory OK"

# 5. Spuštění aplikace
echo ""
echo "=============================================================================="
echo "  🎯 SPOUŠTÍM APLIKACI"
echo "=============================================================================="
echo ""

# Pokud je nastavený PORT (Railway), použij ho, jinak 8000
PORT=${PORT:-8000}
HOST=${HOST:-0.0.0.0}

log_info "Host: $HOST"
log_info "Port: $PORT"
echo ""

# Spusť uvicorn
log_success "Aplikace běží!"
echo ""

exec uvicorn main:app --host "$HOST" --port "$PORT"
