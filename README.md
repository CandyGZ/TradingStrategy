# 🤖 Trading Strategy Emulator con IA

Sistema avanzado de trading automático con dinero ficticio que utiliza Inteligencia Artificial, análisis técnico (incluyendo Fibonacci) y precios en tiempo real para tomar decisiones de compra y venta de acciones y criptomonedas.

![TradingStrategy Chart](https://github.com/CandyGZ/TradingStrategy/raw/main/chartBTC.png)

## ✨ Características

- 💰 **Cuenta Ficticia**: Opera con dinero virtual sin riesgo real
- 🤖 **IA de Trading**: Toma decisiones automáticas basadas en análisis técnico
- 📊 **Análisis Fibonacci**: Identifica niveles clave de soporte y resistencia
- 📈 **Indicadores Técnicos**: RSI, MACD, Medias Móviles, Bandas de Bollinger
- 💹 **Precios en Tiempo Real**: Datos actualizados del mercado vía yfinance
- 📉 **Gestión de Riesgo**: Stop-loss automático y take-profit
- 📋 **Historial Completo**: Registro detallado de todas las operaciones
- 📊 **Reportes Personalizados**: Análisis por hora, día, semana y mes
- 📈 **Visualizaciones**: Gráficos de performance y evolución del balance
- 💸 **Comisiones Realistas**: Simula costos de operaciones reales

## 🚀 Instalación

### 1. Clonar el repositorio

```bash
git clone https://github.com/CandyGZ/TradingStrategy.git
cd TradingStrategy
```

### 2. Instalar dependencias

```bash
pip install -r requirements.txt
```

### Dependencias principales:
- `yfinance` - Obtención de datos de mercado
- `pandas` - Análisis de datos
- `numpy` - Cálculos numéricos
- `matplotlib` - Visualizaciones

## 📖 Uso

### Modo Continuo (Recomendado)

Ejecuta el emulador de forma continua, tomando decisiones cada cierto intervalo:

```bash
python trading_emulator.py --symbol BTC-USD --mode continuous --interval 300
```

### Ejecución Única

Ejecuta una sola iteración de análisis y decisión:

```bash
python trading_emulator.py --symbol ETH-USD --mode single
```

### Ver Reportes

Generar reportes de performance:

```bash
# Reporte del último día
python trading_emulator.py --mode report --period day

# Reporte de la última semana
python trading_emulator.py --mode report --period week

# Reporte completo con gráficos
python trading_emulator.py --mode report --period all
```

### Ver Estrategia

Mostrar la descripción de la estrategia utilizada:

```bash
python trading_emulator.py --mode strategy
```

### Reiniciar Cuenta

Reinicia la cuenta al balance inicial:

```bash
python trading_emulator.py --mode reset
```

## ⚙️ Parámetros de Configuración

### Parámetros Principales

| Parámetro | Alias | Descripción | Default |
|-----------|-------|-------------|---------|
| `--symbol` | `-s` | Símbolo del activo (BTC-USD, ETH-USD, AAPL, etc.) | BTC-USD |
| `--balance` | `-b` | Balance inicial ficticio | 10000.0 |
| `--commission` | `-c` | Tasa de comisión por operación (0.001 = 0.1%) | 0.001 |
| `--risk` | `-r` | Tolerancia al riesgo (0.0 a 1.0) | 0.5 |
| `--confidence` | `-conf` | Confianza mínima para operar (0-100) | 60 |
| `--interval` | `-i` | Intervalo entre operaciones (segundos) | 300 |

### Modos de Ejecución

| Modo | Descripción |
|------|-------------|
| `continuous` | Ejecuta el emulador continuamente |
| `single` | Ejecuta una sola iteración |
| `report` | Genera reportes de performance |
| `strategy` | Muestra descripción de la estrategia |
| `reset` | Reinicia la cuenta |

### Períodos para Reportes

| Período | Descripción |
|---------|-------------|
| `hour` | Última hora |
| `day` | Último día |
| `week` | Última semana |
| `month` | Último mes |
| `all` | Histórico completo |

## 💡 Ejemplos de Uso

### Trading de Bitcoin con balance de $50,000

```bash
python trading_emulator.py --symbol BTC-USD --balance 50000 --risk 0.7 --confidence 65
```

### Trading de Ethereum con bajo riesgo

```bash
python trading_emulator.py --symbol ETH-USD --risk 0.3 --confidence 75 --interval 600
```

### Trading de acciones (Apple)

```bash
python trading_emulator.py --symbol AAPL --balance 20000 --commission 0.002
```

### Trading agresivo de Dogecoin

```bash
python trading_emulator.py --symbol DOGE-USD --risk 0.8 --confidence 50 --interval 180
```

## 📊 Estrategia de Trading

La IA utiliza una combinación de indicadores técnicos para tomar decisiones:

### 1. Análisis Técnico

- **Medias Móviles**: SMA (10, 20, 50 períodos)
- **RSI**: Identifica condiciones de sobrecompra/sobreventa
- **MACD**: Detecta cambios de momento
- **Bandas de Bollinger**: Identifica volatilidad extrema
- **Fibonacci**: Niveles clave de soporte y resistencia

### 2. Criterios de Decisión

- **COMPRA**: Mínimo 2 señales alcistas coincidentes
  - Cruce alcista de medias móviles
  - RSI en sobreventa (< 30)
  - MACD cruza al alza
  - Precio toca banda inferior de Bollinger
  - Tendencia alcista fuerte

- **VENTA**: Mínimo 2 señales bajistas coincidentes
  - Cruce bajista de medias móviles
  - RSI en sobrecompra (> 70)
  - MACD cruza a la baja
  - Precio toca banda superior de Bollinger
  - Stop-loss activado (-5%)

### 3. Gestión de Riesgo

- **Stop-Loss**: Vende automáticamente si pérdida ≥ 5%
- **Take-Profit**: Considera vender si ganancia ≥ 10%
- **Tamaño de Posición**: Entre 5% y 30% del balance
- **Ajuste por Volatilidad**: Reduce exposición en alta volatilidad
- **Cooldown**: 5 minutos entre decisiones

## 📁 Estructura del Proyecto

```
TradingStrategy/
├── src/                          # Código fuente
│   ├── __init__.py              # Inicialización del paquete
│   ├── data_provider.py         # Obtención de datos de mercado
│   ├── technical_analysis.py   # Análisis técnico y Fibonacci
│   ├── trading_ai.py            # IA de trading
│   ├── account.py               # Gestión de cuenta y operaciones
│   └── reporter.py              # Generación de reportes
├── data/                        # Datos persistentes
│   └── account.json             # Estado de la cuenta
├── logs/                        # Logs y gráficos
│   ├── performance_*.png        # Gráficos de performance
│   └── trades_*.csv             # Exportaciones de historial
├── trading_emulator.py          # Script principal
├── whenBuyBTC.py               # Script original (legacy)
├── requirements.txt            # Dependencias
├── chartBTC.png               # Ejemplo de gráfico
├── LICENSE                    # Licencia GNU GPL v3
└── README.md                  # Este archivo
```

## 📈 Interpretando los Resultados

### Salida del Emulador

```
==================================================================
[2025-01-15 14:30:00]
Precio Actual BTC-USD: $43,250.00
Balance Disponible: $8,500.00

💰 Posición Actual: 0.034567 unidades @ $42,800.00
   P&L: $+15.55 (+1.05%)

🤖 Analizando mercado...

📊 Decisión de IA:
   Acción: HOLD
   Confianza: 55%
   Razones:
     • Sin señales claras
     • Confianza insuficiente (55% < 60%)

⏸️  Manteniendo posición actual

📈 Valor Total Cuenta: $10,015.55 (+0.16%)
==================================================================
```

### Reporte de Performance

```
======================================================================
REPORTE COMPARATIVO DE PERÍODOS
======================================================================
Período          Ops   P&L Bruto   Comisiones     P&L Neto       WR
----------------------------------------------------------------------
Última Hora        0      $0.00        $0.00        $0.00      0.0%
Último Día         4    $125.50       $15.30      $110.20     75.0%
Última Semana     15    $450.80       $52.40      $398.40     66.7%
Último Mes        48  $1,250.00      $180.50    $1,069.50     62.5%
Histórico         48  $1,250.00      $180.50    $1,069.50     62.5%
======================================================================
```

## 🎯 Símbolos Soportados

### Criptomonedas (Trading 24/7)
- `BTC-USD` - Bitcoin
- `ETH-USD` - Ethereum
- `BNB-USD` - Binance Coin
- `XRP-USD` - Ripple
- `ADA-USD` - Cardano
- `DOGE-USD` - Dogecoin
- `SOL-USD` - Solana

### Acciones (Horario de mercado)
- `AAPL` - Apple
- `MSFT` - Microsoft
- `GOOGL` - Google
- `TSLA` - Tesla
- `AMZN` - Amazon
- `META` - Meta (Facebook)
- `NVDA` - NVIDIA

### Más Activos
Cualquier símbolo soportado por Yahoo Finance puede ser usado.

## ⚠️ Advertencias Importantes

**DISCLAIMER**: Este es un emulador educativo que utiliza dinero ficticio.

- ❌ **NO** es un asesor financiero
- ❌ **NO** garantiza ganancias reales
- ❌ **NO** debe usarse para decisiones de inversión sin validación
- ✅ **SÍ** es útil para aprender sobre trading
- ✅ **SÍ** permite practicar estrategias sin riesgo
- ✅ **SÍ** ayuda a entender análisis técnico

**El trading de activos financieros conlleva riesgos significativos. El rendimiento pasado no garantiza resultados futuros. Consulta con un asesor financiero profesional antes de invertir dinero real.**

## 🔧 Desarrollo

### Ejecutar Tests

```bash
# Instalar dependencias de desarrollo
pip install pytest pytest-cov

# Ejecutar tests (cuando estén disponibles)
pytest tests/
```

### Contribuir

1. Fork el repositorio
2. Crea una rama para tu feature (`git checkout -b feature/nueva-funcionalidad`)
3. Commit tus cambios (`git commit -am 'Agrega nueva funcionalidad'`)
4. Push a la rama (`git push origin feature/nueva-funcionalidad`)
5. Crea un Pull Request

## 📝 Licencia

Este proyecto está bajo la Licencia GNU General Public License v3.0. Ver el archivo [LICENSE](LICENSE) para más detalles.

## 🙏 Agradecimientos

- **yfinance**: Por proporcionar datos de mercado gratuitos
- **pandas & numpy**: Por las herramientas de análisis
- **matplotlib**: Por las capacidades de visualización

## 📧 Contacto

Para preguntas, sugerencias o reportar bugs, por favor abre un issue en GitHub.

---

**¡Happy Trading! 🚀📈**

*Hecho con ❤️ para aprender sobre trading algorítmico*
