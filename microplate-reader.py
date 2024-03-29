import sys
from contextlib import redirect_stderr, redirect_stdout
from os import path
from pathlib import Path

from loguru import logger
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication

from microplate_reader.window.mr_main_window import MRMainWindow

if __name__ == "__main__":
    app = QApplication([])

    main_window = MRMainWindow()
    try:
        with open("./style.qss") as style_file:
            main_window.setStyleSheet(style_file.read())
    except FileNotFoundError:
        pass

    if path.exists(Path(__file__).parent / "icon.png"):
        main_window.setWindowIcon(QIcon("./icon.png"))

    with redirect_stdout(main_window), redirect_stderr(main_window):  # type: ignore
        logger.remove()
        logger.add(sys.stdout)
        main_window.setWindowFilePath(__file__)
        main_window.show()
        logger.info(f"Starting {main_window.windowTitle()}...")
        sys.exit(app.exec())
