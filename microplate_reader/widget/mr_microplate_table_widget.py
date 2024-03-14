from PySide6.QtCore import Qt
from PySide6.QtGui import QPainter
from PySide6.QtWidgets import QHeaderView, QTableWidget, QTableWidgetItem


class MRMicroplateTableWidget(QTableWidget):
    def __init__(self, rows, columns):
        super().__init__(rows, columns)

        # header
        self.verticalHeader().setDefaultAlignment(Qt.AlignmentFlag.AlignCenter)
        self.horizontalHeader().setDefaultAlignment(Qt.AlignmentFlag.AlignCenter)

        self.verticalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)

        self.setVerticalHeaderLabels(
            [str(chr(ord("A") + i)) for i in range(self.rowCount())]
        )
        self.setHorizontalHeaderLabels([f"{i+1}" for i in range(self.columnCount())])

        # set text align center for all cells
        for row in range(self.rowCount()):
            for column in range(self.columnCount()):
                item = QTableWidgetItem("")
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.setItem(row, column, item)

    def paintEvent(self, event):
        super().paintEvent(event)
        painter = QPainter(self.viewport())
        pen = painter.pen()
        pen.setWidth(1)
        painter.setPen(pen)

        for row in range(self.rowCount()):
            for column in range(self.columnCount()):
                rect = self.visualRect(self.model().index(row, column))
                circle_diameter = min(rect.width(), rect.height())
                circle_radius = circle_diameter / 2
                circle_center = rect.center()
                circle_center.setX(circle_center.x())
                circle_center.setY(circle_center.y())
                painter.drawEllipse(circle_center, circle_radius, circle_radius)
