# FamilyFinance

Aplicación de gestión financiera familiar con IA integrada.

## Stack Tecnológico

- **Backend**: FastAPI + SQLAlchemy + SQLite
- **Frontend**: HTML/CSS/JavaScript (Tailwind CSS)
- **Testing**: pytest + e2e tests

## Inicio Rápido

```bash
# Clonar repositorio
git clone https://github.com/DiogenesPolanco/FamilyFinance.git
cd FamilyFinance

# Crear entorno virtual
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate   # Windows

# Instalar dependencias
pip install -r requirements.txt

# Ejecutar
python3 -m uvicorn main:app --host 0.0.0.0 --port 8000
# O usar el script
./run.sh
```

Abrir `http://localhost:8000` en el navegador.

## Estructura del Proyecto

```
family-finance/
├── main.py          # API FastAPI
├── ai_engine.py     # Motor de IA
├── models.py        # Modelos SQLAlchemy
├── tests_e2e.py     # Tests end-to-end
├── run.sh           # Script de inicio
├── static/
│   └── index.html   # Frontend SPA
├── requirements.txt
└── readme.md
```

## API Endpoints

### Autenticación
- `POST /api/setup` - Crear usuario inicial
- `POST /api/auth/login` - Iniciar sesión
- `GET /api/auth/status` - Estado de autenticación

### Transacciones
- `GET/POST /api/income` - Ingresos
- `GET/POST /api/expense` - Gastos
- `GET /api/expense/kakebo` - Resumen Kakebo

### Deudas y Crédito
- `GET/POST /api/debt` - Deudas
- `POST /api/debt/{id}/pay` - Registrar pago
- `GET /api/debt/{id}/projection` - Proyección de deuda
- `GET /api/debt/{id}/interest` - Cálculo de intereses
- `GET /api/debt/comparison` - Comparativa de deudas

### Tarjetas
- `GET/POST /api/credit-card` - Tarjetas de crédito
- `POST /api/credit-card/{id}/charge` - Agregar cargo
- `GET /api/credit-card/{id}/projection` - Proyección de tarjeta

### Servicios
- `GET/POST /api/service` - Servicios del hogar
- `POST /api/service/{id}/pay` - Marcar como pagado

### Reportes
- `GET /api/reports/fortnightly` - Reporte quincenal
- `GET /api/reports/monthly` - Reporte mensual
- `GET /api/reports/quarterly` - Reporte cuatrimestral

### IA
- `GET /api/ai/recommendations` - Recomendaciones
- `GET /api/ai/insights` - Insights
- `GET /api/ai/anomalies` - Detección de anomalías
- `GET /api/ai/debt-strategy?strategy=avalanche|snowball` - Estrategia de pago
- `POST /api/ai/simulate` - Simulador what-if

### Dashboard
- `GET /api/dashboard/summary` - Resumen general
- `GET /api/dashboard/upcoming` - Próximos pagos

### Utilidades
- `GET /api/export/csv?resource=...` - Exportar CSV
- `POST /api/seed/dummy` - Cargar datos de prueba
- `GET /api/budget` - Presupuesto

## Tests

```bash
# Ejecutar todos los tests
python3 tests_e2e.py

# Tests: 148 pruebas pasando
```

## Contribución

1. Fork del repositorio
2. Crear branch: `git checkout -b feature/nueva-funcion`
3. Hacer cambios y agregar tests
4. Ejecutar tests: `python3 tests_e2e.py`
5. Commit: `git commit -m "Agrega nueva función"`
6. Push: `git push origin feature/nueva-funcion`
7. Crear Pull Request

## Funcionalidades Principales

### Método Kakebo
Sistema de categorización de gastos japonés:
- **Necesidades** - Gastos esenciales
- **Deseos** - Gastos opcionales
- **Cultura** - Educación y desarrollo
- **Inesperado** - Emergencias

### IA Financiera
- Detección de anomalías (gastos duplicados, spikes inusuales)
- Alertas de servicios inactivos
- Recomendaciones personalizadas
- Estrategias de pago (Avalancha/Bola de Nieve)

### Proyecciones
- Simulador what-if para decisiones financieras
- Cálculo de intereses reales
- Comparativa de deudas
- Proyección de tarjetas de crédito

## Configuración

Variables de entorno (opcional):
```env
SECRET_KEY=tu-clave-secreta
```

## Licencia

MIT
