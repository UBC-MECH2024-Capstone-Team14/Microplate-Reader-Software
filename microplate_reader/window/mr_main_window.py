from itertools import product

import numpy as np
import tomllib
from loguru import logger
from pyqtgraph import DataTreeWidget
from PySide6.QtCore import QIODeviceBase, Qt, QTimer, Signal
from PySide6.QtGui import QTextCursor
from PySide6.QtSerialPort import QSerialPort
from PySide6.QtWidgets import (
    QDockWidget,
    QFileDialog,
    QHBoxLayout,
    QMainWindow,
    QMenuBar,
    QPushButton,
    QSpinBox,
    QSplitter,
    QTextBrowser,
    QVBoxLayout,
    QWidget,
)

from ..widget.mr_comport_menu import MRComportMenu
from ..widget.mr_microplate_table_widget import MRMicroplateTableWidget


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
            elif reply.startswith("@home"):
                self.__central_widget.homed()

    def __slot_comport_send(self, data: str):
        data = "/" + data + "\n"
        logger.debug(f"Comport send:\n{data}")
        if not self.__serial_port:
            logger.error("Comport not connected")
            return
        self.__serial_port.write(data.encode("ascii"))
        self.__serial_port.flush()


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

        # Internal Data
        self.__data_dict = {
            (s1, s2): [] for (s1, s2) in product("ABCDEFGH", range(1, 13))
        }

        # Control Buttons
        self.__home_button = QPushButton("Home")
        self.__home_button.clicked.connect(self.__slot_home_button_clicked)
        self.__eject_button = QPushButton("Eject Tray")
        self.__eject_button.clicked.connect(self.__slot_eject_button_clicked)
        self.__read_button = QPushButton("Read")
        self.__read_button.clicked.connect(self.__slot_read_button_clicked)
        self.__read_all_button = QPushButton("Read All")
        self.__read_all_button.clicked.connect(self.__slot_read_all_button_clicked)
        self.__clear_data_button = QPushButton("Clear Data")
        self.__clear_data_button.clicked.connect(self.__slot_clear_data_button_clicked)

        self.__export_data_button = QPushButton("Export Data")
        self.__export_data_button.clicked.connect(
            self.__slot_export_data_button_clicked
        )

        # Debug Utilities
        self.__move_abs_spinbox = QSpinBox()
        self.__move_abs_spinbox.setMinimum(-(2**31))
        self.__move_abs_spinbox.setMaximum(2**31 - 1)
        self.__move_abs_spinbox.setValue(0)
        self.__move_abs_button = QPushButton("Move Absolute")
        self.__move_abs_button.clicked.connect(self.__slot_move_abs_button_clicked)

        # Top Layout
        self.__top_layout = QHBoxLayout()
        self.__top_layout.addWidget(self.__home_button)
        self.__top_layout.addWidget(self.__eject_button)
        self.__top_layout.addWidget(self.__read_button)
        self.__top_layout.addWidget(self.__read_all_button)
        self.__top_layout.addWidget(self.__clear_data_button)
        self.__top_layout.addWidget(self.__move_abs_spinbox)
        self.__top_layout.addWidget(self.__move_abs_button)
        self.__top_layout.addWidget(self.__export_data_button)

        # Table Widget
        self.__table_widget = MRMicroplateTableWidget(8, 12)

        # Data Tree Widget
        self.__data_tree_widget = DataTreeWidget()
        self.__data_tree_widget.setData(self.__data_dict)

        # Layouts
        self.__main__splitter = QSplitter()
        self.__main__splitter.setOrientation(Qt.Orientation.Horizontal)
        self.__main__splitter.addWidget(self.__table_widget)
        self.__main__splitter.addWidget(self.__data_tree_widget)

        self.setLayout(QVBoxLayout())
        self.layout().addLayout(self.__top_layout)  # type: ignore
        self.layout().addWidget(self.__main__splitter)

    # update the display value in the table widget cell
    def update_cell(self, column: int, row: int, value: str):
        self.__table_widget.item(row, column).setText(value)

        # update the internal data dict
        self.__data_dict[(chr(ord("A") + row), column + 1)].append(int(value))
        self.__data_tree_widget.setData(self.__data_dict, hideRoot=True)

    # write row positions and intensities through serial port
    def __write_settings(self):
        row_pos_string = " ".join([str(int(n)) for n in self.__row_positions])
        self.signal_serial_send.emit(f"set_row_pos {row_pos_string}")

        intensity_string = " ".join([str(int(n)) for n in self.__led_intensities])
        self.signal_serial_send.emit(f"set_led_pwr {intensity_string}")

    def __slot_home_button_clicked(self):
        self.signal_serial_send.emit("home")
        self.__home_button.setDisabled(True)
        self.__home_timer = QTimer()
        self.__home_timer.setSingleShot(True)
        self.__home_timer.setInterval(15000)
        self.__home_timer.timeout.connect(self.__slot_homed_timeout)
        self.__home_timer.start()

    def homed(self):
        self.__home_timer.stop()
        self.__home_button.setEnabled(True)

    def __slot_homed_timeout(self):
        logger.error("Device home timeout")
        self.__home_button.setEnabled(True)

    def __slot_read_button_clicked(self):
        self.__write_settings()
        for item in self.__table_widget.selectedIndexes():
            self.signal_serial_send.emit(f"scan_well {item.column()} {item.row()}")

    def __slot_read_all_button_clicked(self):
        self.__write_settings()
        self.signal_serial_send.emit("scan_all")

    def __slot_move_abs_button_clicked(self):
        self.signal_serial_send.emit(f"move_abs {self.__move_abs_spinbox.value()}")

    def __slot_eject_button_clicked(self):
        self.signal_serial_send.emit(f"move_abs {self.__open_position}")

    def __slot_clear_data_button_clicked(self):
        self.__data_dict = {
            (s1, s2): [] for (s1, s2) in product("ABCDEFGH", range(1, 13))
        }
        self.__data_tree_widget.setData(self.__data_dict, hideRoot=True)

    def __slot_export_data_button_clicked(self):
        data = np.zeros(
            (self.__table_widget.rowCount(), self.__table_widget.columnCount())
        )
        for k, v in self.__data_dict.items():
            data[int(ord(k[0]) - ord("A")), k[1] - 1] = np.mean(v) if v else np.nan

        path, _ = QFileDialog.getSaveFileName(
            self, caption="Save Data", dir="data.csv", filter="CSV Files (*.csv)"
        )
        np.savetxt(path, data, delimiter=",")
