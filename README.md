# Microplate-Reader-Software

## Develop Environment

This project uses [poetry](https://python-poetry.org/) as the package manager. Please follow poetry [instructions](https://python-poetry.org/docs/#installation) to install poetry.

Or, `pip install` the packages listed in `pyproject.toml`.

### Dependencies

```
poetry install
```

## Run

```
poetry run python ./microplate-reader.py
```

Or, for Windows, download the compiled `.exe` from the release page. The following files need to be placed in the same directory as the `.exe`:

- `microplate-reader-config.toml`
- `icon.png`
- `style.qss`

## Usage

> For the TMC5130 driver, supply 12V motor power before plug in the USB cable

1. After startup, press `Retract` to home the tray
2. Press `Eject` to eject the tray
3. Load the microplate and place it in the tray
4. Press `Retract`
5. Press `Read All` to scan all the wells, or
6. Select the wells you want to scan, and press `Read`
7. `Eject`, remove the microplate, and `Retract`
