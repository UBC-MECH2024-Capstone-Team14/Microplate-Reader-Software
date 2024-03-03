from loguru import logger
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QTextCursor
from PySide6.QtSerialPort import QSerialPort
from PySide6.QtWidgets import (
    QDockWidget,
    QHBoxLayout,
    QMainWindow,
    QMenuBar,
    QPushButton,
    QSpinBox,
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

        self.__serial_port: QSerialPort = None  # type: ignore

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
        self.__central_widget.signal_serial_send.connect(self.__slot_comport_send)
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
        while self.__serial_port.canReadLine():
            logger.info(self.__serial_port.readLine().toStdString())

    def __slot_comport_send(self, data: str):
        data = "/" + data + "\n"
        logger.info(f"Comport send:\n{data}")
        if not self.__serial_port:
            logger.error("Comport not connected")
            return
        self.__serial_port.write(data.encode("ascii"))


class MR_main_window_central_widget(QWidget):
    signal_serial_send = Signal(str)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.__home_button = QPushButton("Home")
        self.__home_button.clicked.connect(self.__slot_home_button_clicked)
        self.__read_button = QPushButton("Read")
        self.__read_button.clicked.connect(self.__slot_read_button_clicked)
        self.__read_all_button = QPushButton("Read All")
        self.__read_all_button.clicked.connect(self.__slot_read_all_button_clicked)

        # Debug Utilities
        self.__move_abs_spinbox = QSpinBox()
        self.__move_abs_spinbox.setMinimum(-(2**31))
        self.__move_abs_spinbox.setMaximum(2**31 - 1)
        self.__move_abs_spinbox.setValue(0)

        self.__move_abs_button = QPushButton("Move Absolute")

        self.__top_layout = QHBoxLayout()
        self.__top_layout.addWidget(self.__home_button)
        self.__top_layout.addWidget(self.__read_button)
        self.__top_layout.addWidget(self.__read_all_button)

        self.__top_layout.addWidget(self.__move_abs_spinbox)
        self.__top_layout.addWidget(self.__move_abs_button)
        self.__move_abs_button.clicked.connect(self.__slot_move_abs_button_clicked)

        self.__table_widget = QTableWidget(12, 8)

        self.__table_widget.setHorizontalHeaderLabels(
            [str(chr(ord("A") + i)) for i in range(self.__table_widget.columnCount())]
        )
        self.__table_widget.setVerticalHeaderLabels(
            [f"{i+1}" for i in range(self.__table_widget.rowCount())]
        )

        self.__table_widget.cellClicked.connect(self.__slot_cell_clicked)
        self.__table_widget.itemSelectionChanged.connect(
            self.__slot_item_selection_changed
        )

        self.setLayout(QVBoxLayout())
        self.layout().addLayout(self.__top_layout)  # type: ignore
        self.layout().addWidget(self.__table_widget)

    def __slot_home_button_clicked(self):
        logger.info("Home button clicked")
        self.signal_serial_send.emit("home")

    def __slot_read_button_clicked(self):
        logger.info("Read button clicked")
        for item in self.__table_widget.selectedIndexes():
            self.signal_serial_send.emit(f"scan_well {item.row()} {item.column()}")

    def __slot_read_all_button_clicked(self):
        logger.info("Read all button clicked")
        self.signal_serial_send.emit("scan_all")

    def __slot_move_abs_button_clicked(self):
        logger.info("Move absolute button clicked")
        self.signal_serial_send.emit(f"move_abs {self.__move_abs_spinbox.value()}")

    def __slot_cell_clicked(self, row: int, col: int):
        cell_text = (
            self.__table_widget.horizontalHeaderItem(col).text()
            + self.__table_widget.verticalHeaderItem(row).text()
        )
        logger.info(f"Cell {cell_text} clicked")

    def __slot_item_selection_changed(self):
        selected_items = self.__table_widget.selectedIndexes()
        selected_items_strings = [
            self.__table_widget.horizontalHeaderItem(i.column()).text()
            + self.__table_widget.verticalHeaderItem(i.row()).text()
            for i in selected_items
        ]
        logger.info(f"Selected items: {selected_items_strings}")
