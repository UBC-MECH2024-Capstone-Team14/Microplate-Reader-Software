# Microplate-Reader-Software

## Develop Environment

This project uses [poetry](https://python-poetry.org/) as the package manager. Please follow poetry [instructions](https://python-poetry.org/docs/#installation) to install poetry.

Or, `pip install` the packages listed in `pyproject.toml`.

### Dependencies

"""
poetry install
"""

## Run

"""
poetry run python ./microplate-reader.py
"""

Or, for Windows, download the compiled `.exe` from the release page. The following files need to be placed in the same directory as the `.exe`:

- `microplate-reader-config.toml`
- `icon.png`
- `style.qss`
