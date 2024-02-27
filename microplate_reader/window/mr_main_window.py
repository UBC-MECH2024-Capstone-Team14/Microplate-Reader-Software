from loguru import logger
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QTextCursor
from PySide6.QtSerialPort import QSerialPort
from PySide6.QtWidgets import (
    QDockWidget,
    QMainWindow,
    QMenuBar,
    QTableWidget,
    QTextBrowser,
    QVBoxLayout,
    QWidget,
)

from ..widget.mr_comport_menu import MRComportMenu


class MRMainWindow(QMainWindow):
    signal_write = Signal(str)

    def __init__(self):
        super().__init__()

        # Window Title
        self.setWindowTitle("Microplate Reader")

        # Menu Bar
        self.__menu_bar = QMenuBar()
        self.setMenuBar(self.__menu_bar)

        self.__comport_menu = MRComportMenu("Connection", self)
        self.__menu_bar.addMenu(self.__comport_menu)

        self.__comport_menu.signal_comport_connected.connect(
            self.__slot_comport_connected
        )

        # Dock Text Browser
        self.__text_browser = QTextBrowser()
        self.signal_write.connect(self.__slot_write)

        dock_widget = QDockWidget()
        dock_widget.setWidget(self.__text_browser)
        self.addDockWidget(Qt.DockWidgetArea.BottomDockWidgetArea, dock_widget)

        # Central Widget
        self.__central_widget = MR_main_window_central_widget()
        self.setCentralWidget(self.__central_widget)

    # Slots for Redirect stdout and stderr
    def write(self, text: str) -> None:
        self.signal_write.emit(text)

    def flush(self) -> None:
        pass

    def __slot_write(self, text: str) -> None:
        self.__text_browser.moveCursor(QTextCursor.MoveOperation.End)
        self.__text_browser.insertPlainText(text)
        self.__text_browser.ensureCursorVisible()

    # Comport Connection Slots
    def __slot_comport_connected(self, port: QSerialPort):
        logger.info(f"Comport {port.portName()} connected")

        self.__serial_port = port
        self.__serial_port.readyRead.connect(self.__slot_comport_ready_read)

    def __slot_comport_ready_read(self):
        logger.info(self.__serial_port.readAll())


class MR_main_window_central_widget(QWidget):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.__table_widget = QTableWidget()

        # 8 columns and 12 rows
        self.__table_widget.setColumnCount(8)
        self.__table_widget.setRowCount(12)

        self.__table_widget.setHorizontalHeaderLabels(
            [str(chr(ord("A") + i)) for i in range(self.__table_widget.columnCount())]
        )
        self.__table_widget.setVerticalHeaderLabels(
            [f"{i+1}" for i in range(self.__table_widget.rowCount())]
        )

        self.__table_widget.cellClicked.connect(self.__slot_cell_clicked)

        self.setLayout(QVBoxLayout())
        self.layout().addWidget(self.__table_widget)

    def __slot_cell_clicked(self, row: int, col: int):
        cell_text = (
            self.__table_widget.horizontalHeaderItem(col).text()
            + self.__table_widget.verticalHeaderItem(row).text()
        )
        logger.info(f"Cell {cell_text} clicked")
