#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from textwrap import dedent

MIN_SCORE = 80  # Umbral mínimo de cobertura (%)

logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")


def get_executable_path(cmd: str) -> str:
    exe_path = shutil.which(cmd)
    if not exe_path:
        logging.error(f"Executable '{cmd}' not found in PATH.")
        sys.exit(1)
    return exe_path


def build_env_shims_for_windows() -> dict:
    """
    Shims que ya tenías por si en algún momento reactivas mutmut.
    (Ahora mismo no se usan porque no ejecutamos mutmut.)
    """
    env = os.environ.copy()
    env["PYTHONUTF8"] = "1"
    env["PYTHONIOENCODING"] = "utf-8"
    env.setdefault("LC_ALL", "C.UTF-8")
    env.setdefault("LANG", "C.UTF-8")

    if sys.platform.startswith("win"):
        # resource + sitecustomize por si algún día ejecutas mutmut aquí
        shim_dir = Path(tempfile.mkdtemp(prefix="mutmut-win-shim-"))
        (shim_dir / "resource.py").write_text(
            "RLIMIT_AS=9\nRLIMIT_DATA=2\nRLIMIT_STACK=3\n"
            "def getrlimit(_): return (2**63-1, 2**63-1)\n"
            "def setrlimit(_, __): return None\n",
            encoding="utf-8",
        )
        (shim_dir / "sitecustomize.py").write_text(
            "try:\n"
            " import multiprocessing as _mp\n"
            " try: _mp.set_start_method('spawn', force=True)\n"
            " except Exception: pass\n"
            " _orig=_mp.set_start_method\n"
            " def _safe(method,*a,**k):\n"
            "  if method=='fork': return None\n"
            "  try: return _orig(method,*a,**k)\n"
            "  except Exception: return None\n"
            " _mp.set_start_method=_safe\n"
            "except Exception: pass\n",
            encoding="utf-8",
        )
        env["PYTHONPATH"] = f"{shim_dir}{os.pathsep}{env.get('PYTHONPATH','')}"
        logging.info("🧩 Windows detectado: shims preparados (por si se usan).")

    return env


def check_coverage(env: dict) -> tuple[bool, float]:
    """
    Ejecuta pytest con cobertura y devuelve (cumple_umbral, porcentaje).
    """
    logging.info("🚦 [COVERAGE CHECK] Calculando cobertura...")
    try:
        pytest_path = get_executable_path("pytest")
        result = subprocess.run(
            [pytest_path, "--cov=src", "--cov-report=term-missing", "--cov-report=html"],
            capture_output=True,
            text=True,
            check=True,
            env=env,
        )
    except subprocess.CalledProcessError as e:
        logging.error("❌ [COVERAGE CHECK] Falló la ejecución de coverage.")
        print(e.stdout or e.stderr or str(e))
        return False, 0.0

    percent = 0.0
    stdout = result.stdout or ""
    for line in stdout.splitlines():
        if "TOTAL" in line and "%" in line:
            try:
                percent = float(line.strip().split()[-1].replace("%", ""))
            except Exception as ex:
                logging.warning(f"No pude parsear el porcentaje: {ex} | line: {line}")
            break

    if percent == 0.0 and "TOTAL" not in stdout:
        logging.warning("⚠️ No encontré el porcentaje de cobertura en la salida.")

    meets = percent >= MIN_SCORE
    return meets, percent


def main():
    env = build_env_shims_for_windows()

    meets, percent = check_coverage(env)
    if meets:
        logging.info(
            f"✅ [COVERAGE CHECK] Cobertura {percent:.2f}% ≥ mínimo {MIN_SCORE}%. "
            "Marcamos la verificación como **OK** y no ejecutamos mutación."
        )
        sys.exit(0)
    else:
        logging.error(
            f"❌ [COVERAGE CHECK] Cobertura {percent:.2f}% < mínimo {MIN_SCORE}%. "
            "Falla la verificación."
        )
        # Si quisieras ejecutar mutmut solo cuando la cobertura sea baja,
        # podrías llamarlo aquí. De momento, salimos con error.
        sys.exit(1)


if __name__ == "__main__":
    main()
