#!/usr/bin/env python3
import json
import sys
from pathlib import Path

file_path = Path("cosmic-ray-report.json")
threshold = 70

if not file_path.exists():
    print("❌ Archivo 'cosmic-ray-report.json' no encontrado.")
    sys.exit(1)

try:
    with file_path.open() as f:
        report = json.load(f)
except json.JSONDecodeError:
    print("❌ Error al leer el JSON. Formato inválido.")
    sys.exit(1)

mutation_score = report.get("mutation_score", 0)

if mutation_score < threshold:
    print(f"❌ Mutation score {mutation_score}% < {threshold}%")
    sys.exit(1)

print(f"✅ Mutation score {mutation_score}% ≥ {threshold}%")
