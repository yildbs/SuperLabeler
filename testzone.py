import sys
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QWidget, QApplication
from PyQt5.QtGui import QPixmap, QPainter, QPen, QColor, QPainterPath


class Menu(QWidget):
    def __init__(self):
        super().__init__()
        self.drawingPath = None
        self.image = QPixmap("test1.jpg")
        self.resize(self.image.width(), self.image.height())
        self.show()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.drawPixmap(self.rect(), self.image)
        if self.drawingPath:
            painter.setPen(QPen(QColor(121,252,50,50), 20, Qt.SolidLine))
            painter.drawPath(self.drawingPath)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            # start a new QPainterPath and *move* to the current point
            self.drawingPath = QPainterPath()
            self.drawingPath.moveTo(event.pos())

    def mouseMoveEvent(self, event):
        if event.buttons() and Qt.LeftButton and self.drawingPath:
            # add a line to the painter path, without "removing" the pen
            self.drawingPath.lineTo(event.pos())
            self.update()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton and self.drawingPath:
            # draw the painter path to the pixmap
            painter = QPainter(self.image)
            painter.setPen(QPen(QColor(121,252,50,50), 20, Qt.SolidLine))
            painter.drawPath(self.drawingPath)
            self.drawingPath = None
            self.update()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    mainMenu = Menu()
    sys.exit(app.exec_())