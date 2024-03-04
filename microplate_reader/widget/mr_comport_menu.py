from loguru import logger
from PySide6.QtCore import QIODeviceBase, Signal
from PySide6.QtGui import QAction, QActionGroup
from PySide6.QtSerialPort import QSerialPort, QSerialPortInfo
from PySide6.QtWidgets import QMenu


class MRComportMenu(QMenu):
    signal_comport_connected = Signal(QSerialPort)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.__serial_port_info: QSerialPortInfo | None = None

        self.aboutToShow.connect(self.__slot_comport_scan)
        self.__slot_comport_scan()

        self.triggered.connect(self.__slot_connect_serial_port)

    def __slot_comport_scan(self):
        self.clear()

        if not QSerialPortInfo().availablePorts():
            action = QAction("No Comport", self)
            self.addAction(action)
            return

        action_group = QActionGroup(self)

        for serial_port_info in QSerialPortInfo().availablePorts():
            action = QAction(serial_port_info.portName(), self)
            action.setCheckable(True)
            action.setData(serial_port_info)

            if (
                self.__serial_port_info
                and serial_port_info.portName() == self.__serial_port_info.portName()
            ):
                action.setChecked(True)

            action_group.addAction(action)

        for action in action_group.actions():
            self.addAction(action)

    def __slot_connect_serial_port(self, action: QAction):
        self.__serial_port_info = action.data()
        serial_port = QSerialPort(self.__serial_port_info.portName())
        serial_port.setBaudRate(9600)
        serial_port.setDataBits(QSerialPort.DataBits.Data8)
        serial_port.setParity(QSerialPort.Parity.NoParity)
        serial_port.setStopBits(QSerialPort.StopBits.OneStop)
        serial_port.setFlowControl(QSerialPort.FlowControl.NoFlowControl)
        serial_port.open(QIODeviceBase.OpenModeFlag.ReadWrite)

        logger.debug(f"{serial_port.portName()}")

        self.signal_comport_connected.emit(serial_port)
