# Agent instructions

## Project

This Home Assistant integration tracks sleep sessions from a configured in-bed binary sensor. It exposes the current bed start, last sleep duration, last wake time, and brief interruptions.

## Working in this repository

- Keep session transitions and interruption handling in `custom_components/sleep_tracking/tracker.py` consistent with the configured interruption and minimum-duration options.
- Update `strings.json` and translations when changing config-flow or entity text.
- Before changing CI, check [pschmitt/ci-workflows](https://github.com/pschmitt/ci-workflows) for reusable components and preserve this repository's existing checks.

## Validation

- Run `uvx ruff check .` and `uvx ruff format --check .` for Python changes.
- CI runs Hassfest and the shared Ruff checks. There is no repository test suite or CI test job yet.
