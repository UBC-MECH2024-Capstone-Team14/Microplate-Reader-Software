import tomllib
from loguru import logger
from PySide6.QtCore import QIODeviceBase, Qt, Signal
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
    QTableWidgetItem,
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
        self.__serial_port.open(QIODeviceBase.OpenModeFlag.ReadWrite)
        self.__serial_port.readyRead.connect(self.__slot_comport_ready_read)

    def __slot_comport_ready_read(self):
        while self.__serial_port.canReadLine():
            reply = self.__serial_port.readLine().data().decode("ascii").strip()
            logger.debug(reply)
            if reply.startswith("@scan_well"):
                row_index, col_index, intensity = [
                    int(word) for word in reply.split(" ")[1:4]
                ]
                self.__central_widget.update_cell(row_index, col_index, str(intensity))

    def __slot_comport_send(self, data: str):
        data = "/" + data + "\n"
        logger.debug(f"Comport send:\n{data}")
        if not self.__serial_port:
            logger.error("Comport not connected")
            return
        self.__serial_port.write(data.encode("ascii"))


class MR_main_window_central_widget(QWidget):
    signal_serial_send = Signal(str)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # load config data
        with open("./microplate-reader-config.toml", "rb") as f:
            config = tomllib.load(f)
            self.__row_positions: list[int] = config["row_positions"]
            self.__led_intensities: list[int] = config["led_intensities"]
            self.__open_position: int = config["open_position"]

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

    # update the display value in the table widget cell
    def update_cell(self, row: int, column: int, value: str):
        self.__table_widget.setItem(row, column, QTableWidgetItem(value))

    # write row positions and intensities through serial port
    def __write_settings(self):
        row_pos_string = " ".join([str(int(n)) for n in self.__row_positions])
        self.signal_serial_send.emit(f"set_row_pos {row_pos_string}")

        intensity_string = " ".join([str(int(n)) for n in self.__led_intensities])
        self.signal_serial_send.emit(f"set_led_pwr {intensity_string}")

    def __slot_home_button_clicked(self):
        self.signal_serial_send.emit("home")

    def __slot_read_button_clicked(self):
        self.__write_settings()
        for item in self.__table_widget.selectedIndexes():
            self.signal_serial_send.emit(f"scan_well {item.row()} {item.column()}")

    def __slot_read_all_button_clicked(self):
        self.__write_settings()
        self.signal_serial_send.emit("scan_all")

    def __slot_move_abs_button_clicked(self):
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
