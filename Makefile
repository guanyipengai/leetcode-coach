.PHONY: check strict-check migrate-preview migrate

check:
	python3 -m py_compile .codex/skills/leetcode-coach/scripts/study.py
	python3 .codex/skills/leetcode-coach/scripts/study.py check

strict-check:
	python3 -m py_compile .codex/skills/leetcode-coach/scripts/study.py
	python3 .codex/skills/leetcode-coach/scripts/study.py check --strict

migrate-preview:
	python3 .codex/skills/leetcode-coach/scripts/study.py migrate

migrate:
	python3 .codex/skills/leetcode-coach/scripts/study.py migrate --write
