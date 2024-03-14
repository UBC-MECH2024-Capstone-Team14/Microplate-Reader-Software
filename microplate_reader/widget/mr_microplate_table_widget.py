from PySide6.QtCore import QModelIndex, QPersistentModelIndex, Qt
from PySide6.QtGui import QBrush, QPainter
from PySide6.QtWidgets import (
    QHeaderView,
    QStyle,
    QStyledItemDelegate,
    QStyleOptionViewItem,
    QTableWidget,
    QTableWidgetItem,
)


class CircleDelegate(QStyledItemDelegate):
    def paint(
        self,
        painter: QPainter,
        option: QStyleOptionViewItem,
        _index: QModelIndex | QPersistentModelIndex,
    ):
        painter.save()

        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        pen = painter.pen()
        pen.setWidth(1)
        painter.setPen(pen)

        # Draw background
        if QStyle.StateFlag.State_Selected in option.state:  # type: ignore
            painter.fillRect(option.rect, option.palette.base())  # type: ignore

        # Draw circle
        rect = option.rect  # type: ignore
        circle_diameter = min(rect.width(), rect.height())
        circle_radius = circle_diameter / 2
        circle_center = rect.center()
        circle_center.setX(circle_center.x())
        circle_center.setY(circle_center.y())

        if option.state & QStyle.StateFlag.State_Selected:  # type: ignore
            painter.setBrush(QBrush(option.palette.highlight()))  # type: ignore
        else:
            painter.setBrush(QBrush(Qt.GlobalColor.white))
        painter.drawEllipse(circle_center, circle_radius - 1, circle_radius - 1)

        painter.restore()


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

        self.setItemDelegate(CircleDelegate())

        for row in range(self.rowCount()):
            for column in range(self.columnCount()):
                item = QTableWidgetItem("")

                # set text align center
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)

                # set item not editable
                item.setFlags(item.flags() & (~Qt.ItemFlag.ItemIsEditable))

                self.setItem(row, column, item)
