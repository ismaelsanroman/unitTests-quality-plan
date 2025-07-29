#!/usr/bin/env python
# scripts/mutmut_check.py

import os
import re
import subprocess
import sys

MIN_SCORE = 80  # Umbral mínimo tanto para cobertura como para % de killed


def check_coverage() -> bool:
    print("🚦 [MUTATION CHECK] Comprobando cobertura mínima antes de mutaciones...")
    try:
        result = subprocess.run(
            ["pytest", "--cov=src", "--cov-report=term-missing", "--cov-report=html"],
            capture_output=True,
            text=True,
            check=True,
        )
    except subprocess.CalledProcessError as e:
        print("❌ [MUTATION CHECK] Error al ejecutar cobertura")
        # En algunas configs la cobertura se imprime en stdout
        print(e.stdout or e.stderr or str(e))
        return False

    stdout = result.stdout or ""
    for line in stdout.splitlines():
        if "TOTAL" in line and "%" in line:
            try:
                percent = float(line.strip().split()[-1].replace("%", ""))
            except Exception:
                continue
            if percent >= MIN_SCORE:
                print("✅ [MUTATION CHECK] Cobertura OK. ¡Seguimos con mutmut!")
                return True
            print(
                f"❌ [MUTATION CHECK] Cobertura insuficiente: {percent:.2f}% (mínimo {MIN_SCORE}%)"
            )
            return False

    print("⚠️ [MUTATION CHECK] No pude extraer el % de cobertura de la salida de pytest.")
    return False


def run_mutmut():
    print("🧬 Lanzando mutaciones sobre el código fuente...")

    # Evita interferencias de plugins de pytest
    os.environ["PYTEST_ADDOPTS"] = "-q -x --disable-warnings"

    # 1) Ejecuta mutmut y CAPTURA stdout para poder parsear los contadores
    try:
        run_res = subprocess.run(
            ["mutmut", "run"],
            capture_output=True,
            text=True,
            check=True,  # mutmut devuelve 0 aunque haya sobrevivientes
        )
    except subprocess.CalledProcessError as e:
        print("❌ Error al ejecutar: mutmut run")
        print(e.stdout or "")
        print(e.stderr or "")
        sys.exit(1)

    run_out = run_res.stdout or ""
    # 2) Saca killed y survived del “ticker” final: … 🎉 <killed> … 🙁 <survived> …
    killed = survived = None
    # Buscamos la ÚLTIMA ocurrencia (por si la línea aparece varias veces)
    matches = list(re.finditer(r"(\d+)/(\d+).*?🎉\s+(\d+).*?🙁\s+(\d+)", run_out, flags=re.DOTALL))
    if matches:
        _, _, k_str, s_str = matches[-1].groups()
        try:
            killed = int(k_str)
            survived = int(s_str)
        except ValueError:
            killed = survived = None

    # 3) Guardamos el listado de sobrevivientes (como te gusta, en MD)
    print("🧾 Generando reporte de mutaciones sobrevivientes...")
    os.makedirs("Logs", exist_ok=True)
    res_res = subprocess.run(["mutmut", "results"], capture_output=True, text=True)
    results_text = res_res.stdout or ""
    with open("Logs/mutmut_survivors.md", "w", encoding="utf-8") as f:
        f.write(results_text)

    # 4) Si no pudimos extraer los contadores del “run”, al menos mostramos sobrevivientes
    if killed is None or survived is None:
        print("⚠️ No se pudo extraer el resumen de 'mutmut run'.")
        surv_count = sum(1 for ln in results_text.splitlines() if ": survived" in ln)
        print(f"📊 Sobrevivientes detectados: {surv_count} (no se puede calcular % killed).")
        # Si hay sobrevivientes, fallamos igualmente
        if surv_count > 0:
            print("❌ Mutaciones sobrevivieron. El pre-commit debe fallar.")
            sys.exit(1)
        print("✅ No hay sobrevivientes.")
        sys.exit(0)

    # 5) Calcula y muestra el % killed (solo con killables: killed + survived)
    killable = killed + survived
    killed_percent = (killed / killable) * 100 if killable > 0 else 0.0
    print(
        f"📊 Mutaciones — Killed: {killed} | Survived: {survived} | % killed: {killed_percent:.2f}% "
        f"(mín {MIN_SCORE}%)"
    )

    # 6) Decide el resultado del hook
    if killed_percent < MIN_SCORE:
        print(f"❌ Ratio de killed ({killed_percent:.2f}%) menor al mínimo ({MIN_SCORE}%).")
        sys.exit(1)

    # Extra: si pasan el % pero aún quedan sobrevivientes, seguimos fallando (opcional)
    if survived > 0:
        print("❌ Aún quedan mutaciones sobrevivientes. Mejora los tests.")
        sys.exit(1)

    print("✅ Todas las mutaciones fueron eliminadas. ¡Buen trabajo!")
    sys.exit(0)


if __name__ == "__main__":
    if not check_coverage():
        sys.exit(1)
    run_mutmut()
