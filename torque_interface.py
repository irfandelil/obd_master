# -*- coding: utf-8 -*-
import sys
import math
import os
from PyQt5.QtWidgets import (QApplication, QMainWindow, QVBoxLayout, QWidget, QLabel, QHBoxLayout, 
                             QPushButton, QInputDialog, QMessageBox)
from PyQt5.QtCore import Qt, pyqtProperty
from PyQt5.QtGui import QPainter, QPen, QColor

class AnalogGauge(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.value = 0
        self.min_value = 0
        self.max_value = 8000
        self.title = "RPM"
        self.redline = 6500

    def setRange(self, min_val, max_val):
        self.min_value = min_val
        self.max_value = max_val

    def setTitle(self, title):
        self.title = title

    def setRedline(self, redline):
        self.redline = redline

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        width, height = self.width(), self.height()
        side = min(width, height)

        # Draw background
        painter.setBrush(QColor(20, 20, 20))
        painter.drawRect(0, 0, width, height)

        # Draw gauge
        painter.setPen(QPen(Qt.white, 2))
        painter.drawEllipse(5, 5, side - 10, side - 10)

        # Draw needle
        angle = 180 + (self.value / self.max_value) * 180
        painter.setPen(QPen(Qt.red, 3))
        painter.drawLine(width // 2, height // 2, 
                         width // 2 + (side // 2 - 20) * math.cos(math.radians(angle)),
                         height // 2 + (side // 2 - 20) * math.sin(math.radians(angle)))

    def getValue(self):
        return self.value

    def setValue(self, value):
        self.value = max(self.min_value, min(value, self.max_value))
        self.update()

    def resizeEvent(self, event):
        self.setMinimumSize(self.width(), self.height())
        self.update()

    value = pyqtProperty(int, getValue, setValue)

class TorqueInterface(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Araç Gösterge Paneli")
        self.setGeometry(100, 100, 800, 600)

        # Load fault codes
        file_path = os.path.join(os.path.dirname(__file__), "DTC_codes.txt")
        self.fault_codes = self.load_fault_codes_from_file(file_path)

        # Main layout
        main_layout = QVBoxLayout()
        self.rpm_gauge = AnalogGauge()
        self.rpm_gauge.setTitle("RPM")
        self.rpm_gauge.setRange(0, 8000)
        self.rpm_gauge.setRedline(6500)

        self.torque_gauge = AnalogGauge()
        self.torque_gauge.setTitle("Torque")
        self.torque_gauge.setRange(0, 500)

        # Add gauges to layout
        gauges_layout = QHBoxLayout()
        gauges_layout.addWidget(self.rpm_gauge)
        gauges_layout.addWidget(self.torque_gauge)
        main_layout.addLayout(gauges_layout)

        # Add buttons
        check_button = QPushButton("Arıza Kodunu Kontrol Et")
        check_button.clicked.connect(self.get_and_check_fault_code)
        main_layout.addWidget(check_button)

        widget = QWidget()
        widget.setLayout(main_layout)
        self.setCentralWidget(widget)

    def load_fault_codes_from_file(self, file_path):
        fault_codes = {}
        try:
            with open(file_path, "r", encoding="utf-8") as file:
                for line in file:
                    if line.strip():
                        parts = line.split(" ", 1)
                        if len(parts) == 2:
                            code, description = parts
                            fault_codes[code.strip()] = description.strip()
        except FileNotFoundError:
            QMessageBox.critical(self, "Hata", f"{file_path} dosyası bulunamadı! Lütfen dosyanın mevcut olduğundan emin olun.")
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Beklenmeyen bir hata oluştu: {e}")
        return fault_codes

    def get_and_check_fault_code(self):
        code, ok = QInputDialog.getText(self, "Arıza Kodu Kontrolü", "Arıza Kodunu Girin:")
        if ok and code:
            self.check_fault_code(code.strip())

    def check_fault_code(self, incoming_code):
        if incoming_code in self.fault_codes:
            description = self.fault_codes[incoming_code]
            QMessageBox.information(self, "Arıza Kodu Bulundu", f"{incoming_code}: {description}")
        else:
            QMessageBox.warning(self, "Arıza Kodu Bulunamadı", f"{incoming_code} kodu DTC_codes.txt dosyasında bulunamadı.")

if __name__ == '__main__':
    app = QApplication(sys.argv)
    main_window = TorqueInterface()
    main_window.show()
    sys.exit(app.exec())

P0300 Rastgele/Çoklu Silindir Ateşleme Arızası
P0420 Katalitik Konvertör Verimliliği (Bank 1)
P0171 Yakıt Sistemi Çok Fakir (Bank 1)