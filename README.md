# 🧪 UnitTest_demo

Este proyecto muestra una configuración moderna, robusta y eficiente para automatizar pruebas, garantizar calidad de código y realizar análisis estáticos avanzados en Python. Incluye cobertura de pruebas, análisis de complejidad, seguridad, corrección ortográfica y pruebas de mutación (Mutation Testing).

---

## 📂 Estructura del proyecto

```
UnitTest_demo/
├── .pre-commit-config.yaml       # Configuración de pre-commit para automatizar comprobaciones
├── pyproject.toml                # Configuración centralizada de herramientas Python
├── requirements.txt              # Dependencias del proyecto
├── scripts/
│   └── mutmut_check.py           # Script para ejecutar y validar Mutation Testing (mutmut)
├── src/
│   └── pokemon.py                # Código fuente del proyecto
├── tests/                        # Tests automáticos con pytest
├── Logs/
│   └── mutmut_survivors.md       # Reporte detallado de mutaciones sobrevivientes
└── htmlcov/                      # Reporte visual de cobertura de código

```

---

## 🔍 ¿Qué hace cada herramienta?

- **ruff**: Linter y formateador de código muy rápido que integra funcionalidades de `flake8`, `black`, `isort`, asegurando que el código cumpla estándares altos de calidad y estilo.
- **pytest**: Framework para ejecutar tests unitarios, de integración y funcionales en Python.
- **pytest-cov**: Complemento de pytest que mide la cobertura de código, generando reportes detallados.
- **hypothesis**: Biblioteca que permite generar tests basados en propiedades y casos aleatorios.
- **mutmut**: Herramienta de Mutation Testing que modifica automáticamente el código fuente para detectar debilidades en las pruebas.
- **codespell**: Detecta y corrige automáticamente errores ortográficos comunes en el código fuente.
- **bandit**: Herramienta para detectar problemas de seguridad en el código Python mediante análisis estático.
- **xenon**: Analiza la complejidad ciclomática del código Python y garantiza que las funciones sean fáciles de mantener.

---

## 🚀 Configuración inicial paso a paso

### 1. Preparar entorno virtual

```bash
python3 -m venv .venv
source .venv/bin/activate

```

### 2. Instalar dependencias

```bash
pip install -r requirements.txt

```

### 3. Dar permisos al script personalizado

```bash
chmod +x scripts/mutmut_check.py

```

### 4. Instalar `pre-commit` y hooks

```bash
pre-commit install

```

---

## 🛠 Uso de herramientas (manual)

### Ejecutar pruebas con pytest

```bash
pytest

```

### Generar reporte de cobertura

```bash
pytest --cov=src --cov-report=term-missing --cov-report=html

```

### Ejecutar Mutation Testing (mutmut)

```bash
mutmut run
mutmut results > Logs/mutmut_survivors.md

```

### Validar mutaciones con script personalizado

```bash
python scripts/mutmut_check.py

```

### Análisis de seguridad con Bandit

```bash
bandit -c bandit.yaml -r src/

```

### Análisis ortográfico con codespell

```bash
codespell src/

```

### Complejidad ciclomática con Xenon

```bash
xenon --max-absolute B --max-modules B --max-average A src/

```

---

## 🛠 Automatización con pre-commit

Pre-commit asegura automáticamente la calidad del código antes de cada commit, ejecutando:

- **ruff**: Verifica el estilo, formatea el código y corrige importaciones automáticamente.
- **pytest**: Ejecuta tests automáticos.
- **pytest-cov**: Valida cobertura mínima del 80%.
- **codespell**: Revisa la ortografía del código fuente.
- **bandit**: Ejecuta análisis de seguridad.
- **xenon**: Controla la complejidad máxima permitida.
- **mutmut_check.py**: Ejecuta pruebas de mutación y asegura un umbral mínimo de mutaciones detectadas (80%).

Para ejecutar manualmente todos los hooks:

```bash
pre-commit run --all-files

```

---

## ✅ Estado esperado del pre-commit

```
ruff............................................................ Passed
pytest.......................................................... Passed
coverage_check.................................................. Passed
codespell....................................................... Passed
bandit security check........................................... Passed
xenon complexity check.......................................... Passed
mutation testing (mutmut)....................................... Passed

```

---

## 📜 Reportes y registros generados

- **Logs/mutmut_survivors.md**: Contiene mutaciones que sobrevivieron indicando posibles fallos en las pruebas.
- **htmlcov/**: Reporte visual interactivo de la cobertura de código generada por pytest-cov.

---

## ⚙️ Configuración centralizada (`pyproject.toml`)

Todas las herramientas y dependencias del proyecto se configuran de forma centralizada en el archivo `pyproject.toml`, facilitando mantenimiento y lectura sencilla.

---

## ✨ Autor

Desarrollado por **Ismael Sanromán** 🧑‍💻