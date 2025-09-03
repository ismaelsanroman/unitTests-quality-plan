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

MIN_SCORE = 80  # Minimum threshold for mutation score (% killed)

logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")


def get_executable_path(cmd: str) -> str:
    """Find the absolute path to an executable."""
    exe_path = shutil.which(cmd)
    if not exe_path:
        logging.error(f"Executable '{cmd}' not found in PATH.")
        sys.exit(1)
    return exe_path


def build_env_shims_for_windows() -> dict:
    """
    En Windows, mutmut:
      - importa 'resource' (solo POSIX)
      - intenta usar multiprocessing con 'fork'
    Inyectamos:
      - resource.py (no-op)
      - sitecustomize.py que fuerza 'spawn' y neutraliza 'fork'
    """
    env = os.environ.copy()

    if sys.platform.startswith("win"):
        shim_dir = Path(tempfile.mkdtemp(prefix="mutmut-win-shim-"))

        # 1) Shim de 'resource'
        (shim_dir / "resource.py").write_text(
            dedent(
                """
                # resource.py — shim no-op para Windows
                RLIMIT_AS = 9
                RLIMIT_DATA = 2
                RLIMIT_STACK = 3
                def getrlimit(_): return (2**63 - 1, 2**63 - 1)
                def setrlimit(_, __): return None
                """
            ).lstrip(),
            encoding="utf-8",
        )

        # 2) sitecustomize: se importa automáticamente al arrancar Python
        #    Aquí forzamos 'spawn' y hacemos que cualquier intento de setear 'fork' sea un no-op.
        (shim_dir / "sitecustomize.py").write_text(
            dedent(
                """
                # sitecustomize.py — ajustes tempranos para que mutmut funcione en Windows
                try:
                    import multiprocessing as _mp
                    # Fuerza 'spawn' desde el arranque
                    try:
                        _mp.set_start_method('spawn', force=True)
                    except Exception:
                        pass

                    _orig_set = _mp.set_start_method

                    def _safe_set(method, *args, **kwargs):
                        # Si alguien pide 'fork', lo ignoramos (Windows no lo soporta)
                        if method == 'fork':
                            return None
                        try:
                            return _orig_set(method, *args, **kwargs)
                        except Exception:
                            return None

                    _mp.set_start_method = _safe_set
                except Exception:
                    # Si algo falla aquí, seguimos sin romper el proceso.
                    pass
                """
            ).lstrip(),
            encoding="utf-8",
        )

        # Prependemos el shim al PYTHONPATH para que Python lo cargue primero
        env["PYTHONPATH"] = f"{shim_dir}{os.pathsep}{env.get('PYTHONPATH', '')}"
        logging.info("🧩 Windows detectado: inyectados shims 'resource' y 'sitecustomize' (spawn).")

    return env


def check_coverage(env: dict) -> bool:
    logging.info("🚦 [MUTATION CHECK] Checking minimum coverage before mutation testing...")
    try:
        pytest_path = get_executable_path("pytest")
        result = subprocess.run(
            [
                pytest_path,
                "--cov=src",
                "--cov-report=term-missing",
                "--cov-report=html",
            ],
            capture_output=True,
            text=True,
            check=True,
            env=env,
        )
    except subprocess.CalledProcessError as e:
        logging.error("❌ [MUTATION CHECK] Coverage run failed.")
        print(e.stdout or e.stderr or str(e))
        return False

    stdout = result.stdout or ""
    for line in stdout.splitlines():
        if "TOTAL" in line and "%" in line:
            try:
                percent = float(line.strip().split()[-1].replace("%", ""))
            except Exception as ex:
                logging.warning(f"Failed to parse coverage percentage: {ex} | line: {line}")
                continue
            if percent >= MIN_SCORE:
                logging.info("✅ [MUTATION CHECK] Coverage is OK. Proceeding to mutation testing.")
                return True
            logging.error(
                f"❌ [MUTATION CHECK] Coverage too low: {percent:.2f}% (minimum {MIN_SCORE}%)"
            )
            return False

    logging.warning("⚠️ [MUTATION CHECK] Could not find coverage percentage in output.")
    return False


def run_mutmut(env: dict):
    logging.info("🧬 Running mutation tests...")

    # Opciones útiles para pytest durante mutmut
    env = env.copy()
    env["PYTEST_ADDOPTS"] = "-q -x --disable-warnings"

    try:
        mutmut_path = get_executable_path("mutmut")
        run_res = subprocess.run(
            [mutmut_path, "run"],
            capture_output=True,
            text=True,
            check=True,
            env=env,
        )
    except subprocess.CalledProcessError as e:
        logging.error("❌ Error running 'mutmut run'")
        print(e.stdout or "")
        print(e.stderr or "")
        sys.exit(1)

    run_out = run_res.stdout or ""

    # Extrae estadísticas de killed/survived si están en la salida
    killed = survived = None
    matches = list(re.finditer(r"(\d+)/(\d+).*?🎉\s+(\d+).*?🙁\s+(\d+)", run_out, flags=re.DOTALL))
    if matches:
        _, _, k_str, s_str = matches[-1].groups()
        try:
            killed = int(k_str)
            survived = int(s_str)
        except ValueError:
            killed = survived = None

    # Genera informe de survivors
    logging.info("🧾 Generating survivor mutation report...")
    Path("Logs").mkdir(parents=True, exist_ok=True)
    try:
        res_res = subprocess.run(
            [mutmut_path, "results"],
            capture_output=True,
            text=True,
            check=True,
            env=env,
        )
    except subprocess.CalledProcessError as e:
        logging.error("❌ Error running 'mutmut results'")
        print(e.stdout or "")
        print(e.stderr or "")
        sys.exit(1)

    results_text = res_res.stdout or ""
    with open("Logs/mutmut_survivors.md", "w", encoding="utf-8") as f:
        f.write(results_text)

    # Si no pudimos parsear, contamos survivors por texto
    if killed is None or survived is None:
        logging.warning("⚠️ Could not extract kill/survive stats.")
        surv_count = sum(1 for ln in results_text.splitlines() if ": survived" in ln)
        logging.info(f"📊 Detected {surv_count} survivors (mutation score unavailable).")
        if surv_count > 0:
            logging.error("❌ Surviving mutations found. Pre-commit will fail.")
            sys.exit(1)
        logging.info("✅ No surviving mutations.")
        sys.exit(0)

    # Muestra mutation score
    killable = killed + survived
    killed_percent = (killed / killable) * 100 if killable > 0 else 0.0
    logging.info(
        f"📊 Mutations — Killed: {killed} | Survived: {survived} | "
        f"Killed %: {killed_percent:.2f}% (min required: {MIN_SCORE}%)"
    )

    # Enforce threshold
    if killed_percent < MIN_SCORE:
        logging.error(f"❌ Mutation score too low: {killed_percent:.2f}% < {MIN_SCORE}%")
        sys.exit(1)

    # Aviso si hay survivors pero pasó el umbral
    if survived > 0:
        logging.warning("⚠️ Some mutations survived, but score threshold passed.")

    logging.info("✅ All mutations killed. Good job!")
    sys.exit(0)


if __name__ == "__main__":
    # Prepara entorno (shims para Windows si hace falta)
    _env = build_env_shims_for_windows()

    if not check_coverage(_env):
        sys.exit(1)
    run_mutmut(_env)
