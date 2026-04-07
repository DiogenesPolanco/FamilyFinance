# FamilyFinance

Aplicación de gestión financiera familiar con IA integrada y análisis predictivo.

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
├── ai_engine.py     # Motor de IA con análisis predictivo
├── models.py        # Modelos SQLAlchemy
├── tests_e2e.py     # Tests end-to-end
├── run.sh           # Script de inicio
├── static/
│   └── index.html   # Frontend SPA con UI futurista
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
- `GET /api/expense/payments` - Historial de pagos de gastos

### Deudas y Crédito
- `GET/POST /api/debt` - Deudas
- `GET /api/debt/payments` - Historial de pagos de deudas
- `POST /api/debt/{id}/pay` - Registrar pago
- `GET /api/debt/{id}/projection` - Proyección de deuda
- `GET /api/debt/{id}/interest` - Cálculo de intereses
- `GET /api/debt/comparison` - Comparativa de deudas

### Tarjetas
- `GET/POST /api/credit-card` - Tarjetas de crédito
- `GET /api/credit-card/payments` - Historial de pagos de tarjetas
- `GET /api/credit-card/charges` - Historial de cargos
- `POST /api/credit-card/{id}/charge` - Agregar cargo
- `POST /api/credit-card/{id}/pay` - Registrar pago
- `GET /api/credit-card/{id}/projection` - Proyección de tarjeta

### Servicios
- `GET/POST /api/service` - Servicios del hogar
- `GET /api/service/payments` - Historial de pagos de servicios
- `POST /api/service/{id}/pay` - Marcar como pagado

### Reportes
- `GET /api/reports/fortnightly` - Reporte quincenal
- `GET /api/reports/monthly` - Reporte mensual
- `GET /api/reports/quarterly` - Reporte cuatrimestral
- `GET /api/reports/kakebo` - Reporte Kakebo
- `GET /api/reports/debts` - Reporte de deudas

### IA (Motor de Análisis)
- `GET /api/ai/recommendations` - Recomendaciones personalizadas
- `GET /api/ai/insights` - Insights del estado financiero
- `GET /api/ai/anomalies` - Detección de anomalías
- `GET /api/ai/cashflow` - Proyección de flujo de caja
- `GET /api/ai/behavior` - Análisis de patrones de comportamiento
- `GET /api/ai/coach` - Coach de ahorro (Regla 50/30/20)
- `GET /api/ai/actionable` - Acciones prioritarias
- `GET /api/ai/forecast` - Pronóstico financiero
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

# Tests: 148+ pruebas pasando
```

## Funcionalidades Principales

### Método Kakebo
Sistema de categorización de gastos japonés:
- **Necesidades** (50%) - Gastos esenciales (vivienda, comida, salud)
- **Deseos** (30%) - Gastos opcionales (entretenimiento, caprichos)
- **Cultura** - Educación y desarrollo personal
- **Inesperado** - Emergencias y reservas

### Asistente IA 🚀
Motor de inteligencia artificial con análisis predictivo y comportamiento:

#### Predicción de Flujo de Caja
- Proyección de balances a 6 meses
- Alertas cuando el ahorro se agotará
- Indicadores de estado (bien/cuidado/alerta)

#### Análisis de Patrones de Comportamiento
- Detecta patrones de gasto por día de la semana
- Identifica posibles compras impulsivas (>3x promedio)
- Detecta tendencias crecientes en categorías
- Encuentra suscripciones recurrentes

#### Coach de Ahorro (Regla 50/30/20)
- Presupuesto visual para cada categoría
- Barras de progreso en tiempo real
- Tips personalizados para alcanzar metas
- Alertas de presupuesto excedido

#### Acciones Prioritarias
- Top 5 acciones urgentes basadas en análisis
- Cada una con: título, descripción y acción a tomar
- Ordenadas por prioridad

#### Experiencia Futurista
- Animaciones de carga con efecto glitch
- Sonidos robóticos generados con Web Audio API
- Cards cerrables con persistencia en localStorage
- Efecto de "revelación" al cargar cada sección

### Reportes Visuales
- **Mensual**: Pie chart de gastos + timeline de meses
- **Kakebo**: Barras horizontales con colores de estado
- **Deudas**: Resumen + historial con indicadores de riesgo

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

## Contribución

1. Fork del repositorio
2. Crear branch: `git checkout -b feature/nueva-funcion`
3. Hacer cambios y agregar tests
4. Ejecutar tests: `python3 tests_e2e.py`
5. Commit: `git commit -m "Agrega nueva función"`
6. Push: `git push origin feature/nueva-funcion`
7. Crear Pull Request

## Licencia

MIT
