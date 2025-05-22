# 🧪 UnitTest_demo

Este proyecto demuestra una configuración moderna para testing, análisis estático y validaciones automáticas en Python. Incluye cobertura, complejidad, y mutation testing📂 Estructura del proyecto

---
```bash
UnitTest_demo/
├── .pre-commit-config.yaml
├── pyproject.toml
├── requirements.txt / Pipfile
├── scripts/
│ └── check_mutation_threshold.py
├── src/
│ └── [demo.py](http://demo.py/)
├── tests/
└── cosmic-ray-report.json
```

---

## 📌 Fase 1: Preparación y Configuración Inicial

### 1. Crear entorno virtual

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 2. Instalar dependencias

```bash
pip install -r requirements.txt
# o si usas pipenv:
pipenv install --dev
```

### 3. Herramientas configuradas (en `pyproject.toml`)

- **Code style**: `black`, `flake8`, `isort`
- **Testing**: `pytest`, `pytest-cov`, `hypothesis`
- **Complejidad**: `xenon`
- **Mutation Testing**: `cosmic-ray`

---

## 📌 Fase 2: Control de Calidad Automático

### 4. Dar permisos al script personalizado

```bash
chmod +x scripts/check_mutation_threshold.py
```

### 5. Instalar `pre-commit` y sus hooks

```bash
pre-commit install
```

### 6. Ejecutar los hooks manualmente (opcional)

```bash
pre-commit run --all-files
```

---

## 🧪 Testing y Validaciones Manuales

### Ejecutar tests

```bash
pytest
```

### Ejecutar análisis de mutaciones

```bash
cosmic-ray run config.toml  # o usando el alias pipenv run mutate
cosmic-ray report > cosmic-ray-report.json
```

### Validar el umbral de mutación mínimo

```bash
python scripts/check_mutation_threshold.py
```

---

## 🛠 Scripts útiles (si usas pipenv)

```bash
pipenv run test      # Ejecuta todos los tests
pipenv run lint      # Ejecuta black, isort, flake8
pipenv run mutate    # Corre cosmic-ray + genera el informe
```

---

## ✅ Estado del Pre-commit

```bash
black .......................................................... Passed
flake8 ......................................................... Passed
isort .......................................................... Passed
xenon complexity check ......................................... Passed
check mutation score ........................................... Passed
```

---

## ✨ Autor

Desarrollado por ***Ismael Sanromán***🧑‍💻