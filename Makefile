.PHONY: mutants

# === Variables ===
PYTHON := .venv/bin/python
PRECOMMIT := .venv/bin/pre-commit
MUTMUT := .venv/bin/mutmut
XENON := .venv/bin/xenon
LOGS := Logs

# === Targets ===

# 🔁 Ejecuta to.do
all: check bandit ruff format codespell xenon coverage mutate

# ✅ Pre-commit: archivos grandes
check:
	$(PRECOMMIT) run check-added-large-files --all-files

# 🦺 Seguridad con Bandit
bandit:
	$(PRECOMMIT) run bandit --all-files

# 🎯 Linter con Ruff
ruff:
	$(PRECOMMIT) run ruff --all-files

# 🧹 Formateo automático
format:
	$(PRECOMMIT) run ruff-format --all-files

# 🔤 Revisión ortográfica
codespell:
	$(PRECOMMIT) run codespell --all-files

# 🧠 Complejidad ciclomática
xenon:
	$(XENON) --max-absolute B --max-modules A --max-average A src

# 📊 Cobertura de tests
coverage:
	$(PYTHON) -m pytest --cov=src --cov-report=term-missing --cov-report=html

# 🧬 Mutation Testing + Check
mutate:
	MUTMUT=$(MUTMUT) PATH=$$PATH:$(dir $(realpath $(MUTMUT))) $(PYTHON) scripts/mutmut_check.py

# 🧟‍♂️ Diffs de mutantes sobrevivientes (solo markdown)
.PHONY: mutants

mutants:
	@echo "🧟‍♂️ Generando informe de mutantes sobrevivientes..."
	@mkdir -p $(LOGS)
	@rm -f $(LOGS)/mutmut_survivors_diffs.md
	@$(MUTMUT) results | grep survived | cut -d ':' -f1 | \
		while read survivor; do \
			echo "## $$survivor" >> $(LOGS)/mutmut_survivors_diffs.md; \
			$(MUTMUT) show $$survivor >> $(LOGS)/mutmut_survivors_diffs.md; \
			echo "\n---\n" >> $(LOGS)/mutmut_survivors_diffs.md; \
		done
	@echo "✅ Informe guardado en $(LOGS)/mutmut_survivors_diffs.md"

# 🧪 QA (sin tests)
qa: check bandit ruff format codespell xenon

# 🧼 Limpieza de logs
clean:
	rm -rf $(LOGS) htmlcov .pytest_cache .mypy_cache .coverage