#!/bin/bash

cd "$(dirname "$0")"

echo "=== FamilyFinance ==="

# Reset database
rm -f family_finance.db
echo "✓ DB reseteada"

# Kill old server
pkill -f "uvicorn main:app" 2>/dev/null
sleep 1

# Start server
echo "✓ Iniciando servidor..."
python3 -m uvicorn main:app --host 0.0.0.0 --port 8000 &
SERVER_PID=$!

sleep 2

# Check if server started
if curl -s http://localhost:8000/api/auth/status > /dev/null 2>&1; then
    echo "✓ Servidor corriendo en http://localhost:8000"
    
    # Open browser (Linux)
    if command -v xdg-open &> /dev/null; then
        xdg-open http://localhost:8000
    elif command -v open &> /dev/null; then
        open http://localhost:8000
    fi
else
    echo "✗ Error al iniciar servidor"
    exit 1
fi

echo ""
echo "Presiona Ctrl+C para detener el servidor"
echo ""

# Wait for interrupt
wait $SERVER_PID
