# -*- coding: utf-8 -*-
import sys
import random
import math
import csv
import datetime
import os
from PyQt5.QtWidgets import (QApplication, QMainWindow, QVBoxLayout, 
                            QWidget, QLabel, QHBoxLayout, QSlider, 
                            QPushButton, QComboBox, QInputDialog, QMessageBox)
from PyQt5.QtCore import QTimer, Qt, QPropertyAnimation, pyqtProperty
from PyQt5.QtGui import QPainter, QPen, QColor, QFont, QConicalGradient, QPalette
from PyQt5.QtWidgets import QStackedWidget


class AnalogGauge(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(200, 200)
        self.value = 0
        self.min_value = 0
        self.max_value = 8000
        self.title = "RPM"
        self.redline = 6500
        self.animation_speed = 200
        self.notch_count = 10
        self.wrapping = False
        self.language = "tr"

    def setRange(self, min_val, max_val):
        self.min_value = min_val
        self.max_value = max_val

    def setTitle(self, title):
        self.title = title

    def setRedline(self, redline):
        self.redline = redline

    def setAnimationSpeed(self, speed):
        self.animation_speed = speed

    def setNotchTarget(self, count):
        self.notch_count = count

    def setWrapping(self, wrap):
        self.wrapping = wrap

    def setLanguage(self, lang):
        self.language = lang

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        width = self.width()
        height = self.height()
        side = min(width, height)

        # Arka plan
        painter.setBrush(QColor(20, 20, 20))
        painter.drawRect(0, 0, width, height)

        # Kadran çerçevesi
        painter.setPen(QPen(QColor(100, 100, 100), 2))
        painter.drawEllipse(5, 5, side-10, side-10)

        # Kadran
        gradient = QConicalGradient(width/2, height/2, -90)
        gradient.setColorAt(0.7, Qt.green)
        gradient.setColorAt(0.85, Qt.yellow)
        gradient.setColorAt(1, Qt.red)
        
        painter.setPen(QPen(Qt.white, 2))
        painter.setBrush(Qt.black)
        start_angle = 180 if not self.wrapping else 0
        span_angle = 180 if not self.wrapping else 360
        painter.drawPie(10, 10, side-20, side-20, start_angle*16, span_angle*16)

        # Ölçek ve çentikler
        painter.setPen(QPen(Qt.white, 1))
        step = (self.max_value - self.min_value) / self.notch_count
        for i in range(self.min_value, self.max_value + 1, int(step)):
            angle = start_angle + (i / self.max_value) * span_angle
            rad = (side - 40) / 2
            x = width/2 + rad * math.cos(math.radians(angle))
            y = height/2 + rad * math.sin(math.radians(angle))
            painter.drawLine(width/2, height/2, int(x), int(y))
            painter.drawText(int(x)-15, int(y)-15, 30, 30, 
                           Qt.AlignCenter, str(i//1000 if self.max_value > 1000 else i))

        # Kırmızı bölge
        if not self.wrapping and self.redline < self.max_value:
            painter.setPen(QPen(Qt.red, 3))
            start_angle = 180 + (self.redline / self.max_value) * 180
            span_angle = ((self.max_value - self.redline) / self.max_value) * 180
            painter.drawArc(10, 10, side-20, side-20, int(start_angle*16), int(span_angle*16))

        # İbre
        angle = start_angle + (self.value / self.max_value) * span_angle
        painter.setPen(QPen(Qt.cyan, 3))
        painter.drawLine(width/2, height/2, 
                        width/2 + (side/2-20) * math.cos(math.radians(angle)),
                        height/2 + (side/2-20) * math.sin(math.radians(angle)))

        # Değer gösterimi
        painter.setFont(QFont("Arial", 14, QFont.Bold))
        painter.setPen(QPen(Qt.white))
        display_text = {
            "tr": f"{self.title}: {self.value}",
            "en": f"{self.title}: {self.value}"
        }
        painter.drawText(0, height-40, width, 40, 
                        Qt.AlignCenter, display_text.get(self.language, f"{self.title}: {self.value}"))

    def getValue(self):
        return self.value

    def setValue(self, value):
        self.value = max(0, min(value, self.max_value))
        self.update()

    value = pyqtProperty(int, getValue, setValue)


class TorqueInterface(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Advanced Vehicle Dashboard")
        self.setGeometry(100, 100, 900, 600)
        
        self.animation_speed = 200
        self.night_mode = False
        self.logging_active = True
        self.language = "tr"
        self.simulation_profiles = {
            "Economy": {"max_rpm": 5000, "torque_factor": 0.12, "color": Qt.green},
            "Sport": {"max_rpm": 8000, "torque_factor": 0.18, "color": Qt.red},
            "Diesel": {"max_rpm": 4500, "torque_factor": 0.25, "color": Qt.blue}
        }
        self.current_profile = "Economy"  # Varsayılan profil
        
        self.initUI()
        self.initData()
        self.statusBar().showMessage("İrfanDelil tarafından yapılmıştır. Tüm hakları saklıdır. | Sistem hazır | V1.0 | © 2023")

    def initUI(self):
        self.stacked_widget = QStackedWidget()
        self.setCentralWidget(self.stacked_widget)

        # Profile Selection Screen
        self.profile_screen = QWidget()
        profile_layout = QVBoxLayout()
        profile_label = QLabel("Araç Profilinizi Seçin" if self.language == "tr" else "Select Your Vehicle Profile")
        profile_label.setFont(QFont("Arial", 18, QFont.Bold))
        profile_label.setAlignment(Qt.AlignCenter)
        
        self.profile_combo = QComboBox()
        self.profile_combo.addItems(self.simulation_profiles.keys())
        self.profile_combo.setFont(QFont("Arial", 14))
        self.profile_combo.currentTextChanged.connect(self.change_profile)
        
        create_profile_button = QPushButton("Yeni Profil Oluştur" if self.language == "tr" else "Create New Profile")
        create_profile_button.setFont(QFont("Arial", 14))
        create_profile_button.clicked.connect(self.create_new_profile)
        
        start_button = QPushButton("Başla" if self.language == "tr" else "Start")
        start_button.setFont(QFont("Arial", 14))
        start_button.clicked.connect(self.start_with_selected_profile)
        
        profile_layout.addWidget(profile_label)
        profile_layout.addWidget(self.profile_combo)
        profile_layout.addWidget(create_profile_button)
        profile_layout.addWidget(start_button)
        self.profile_screen.setLayout(profile_layout)

        # Main Screen
        self.main_screen = QWidget()
        main_layout = QVBoxLayout()
        
        # Gauges
        gauges_layout = QHBoxLayout()
        self.rpm_gauge = AnalogGauge()
        self.rpm_gauge.setTitle("RPM")
        self.rpm_gauge.setRange(0, self.simulation_profiles[self.current_profile]["max_rpm"])
        self.rpm_gauge.setRedline(self.simulation_profiles[self.current_profile]["max_rpm"] * 0.8)
        self.rpm_gauge.setNotchTarget(10)
        self.rpm_gauge.setWrapping(False)
        self.rpm_gauge.setLanguage(self.language)
        
        self.torque_gauge = AnalogGauge()
        self.torque_gauge.setTitle("TORQUE (Nm)")
        self.torque_gauge.setRange(0, 500)
        self.torque_gauge.setNotchTarget(10)
        self.torque_gauge.setLanguage(self.language)
        
        gauges_layout.addWidget(self.rpm_gauge)
        gauges_layout.addWidget(self.torque_gauge)
        gauges_layout.setStretch(0, 1)
        gauges_layout.setStretch(1, 1)
        
        # Control Panel
        control_panel = QWidget()
        control_layout = QHBoxLayout()
        
        control_layout.addWidget(QLabel("Animasyon Hızı:" if self.language == "tr" else "Animation Speed:"))
        self.speed_slider = QSlider(Qt.Horizontal)
        self.speed_slider.setRange(50, 1000)
        self.speed_slider.setValue(self.animation_speed)
        self.speed_slider.valueChanged.connect(self.setAnimationSpeed)
        control_layout.addWidget(self.speed_slider)
        
        self.night_mode_btn = QPushButton("Gece Modu" if self.language == "tr" else "Night Mode")
        self.night_mode_btn.setCheckable(True)
        self.night_mode_btn.clicked.connect(self.toggle_night_mode)
        control_layout.addWidget(self.night_mode_btn)
        
        self.profile_combo_main = QComboBox()
        self.profile_combo_main.addItems(self.simulation_profiles.keys())
        self.profile_combo_main.setCurrentText(self.current_profile)
        self.profile_combo_main.currentTextChanged.connect(self.change_profile)
        control_layout.addWidget(QLabel("Sürüş Profili:" if self.language == "tr" else "Drive Profile:"))
        control_layout.addWidget(self.profile_combo_main)
        
        self.language_combo = QComboBox()
        self.language_combo.addItems(["tr", "en"])
        self.language_combo.setCurrentText(self.language)
        self.language_combo.currentTextChanged.connect(self.change_language)
        control_layout.addWidget(QLabel("Dil:" if self.language == "tr" else "Language:"))
        control_layout.addWidget(self.language_combo)
        
        manage_profiles_button = QPushButton("Profil Yönetimi" if self.language == "tr" else "Manage Profiles")
        manage_profiles_button.clicked.connect(self.manage_profiles)
        control_layout.addWidget(manage_profiles_button)

        about_button = QPushButton("Hakkında" if self.language == "tr" else "About")
        about_button.clicked.connect(self.show_about_message)
        control_layout.addWidget(about_button)
        
        control_panel.setLayout(control_layout)
        
        main_layout.addLayout(gauges_layout)
        main_layout.addWidget(control_panel)
        self.main_screen.setLayout(main_layout)

        # Farewell Screen
        self.farewell_screen = QWidget()
        farewell_layout = QVBoxLayout()
        farewell_label = QLabel("Güle Güle!" if self.language == "tr" else "Goodbye!")
        farewell_label.setFont(QFont("Arial", 24, QFont.Bold))
        farewell_label.setAlignment(Qt.AlignCenter)
        powered_label_farewell = QLabel("Powered by IrfanDelil")
        powered_label_farewell.setFont(QFont("Arial", 12, QFont.Italic))
        powered_label_farewell.setAlignment(Qt.AlignCenter)
        farewell_layout.addWidget(farewell_label)
        farewell_layout.addWidget(powered_label_farewell)
        self.farewell_screen.setLayout(farewell_layout)

        # Add screens to stacked widget
        self.stacked_widget.addWidget(self.profile_screen)
        self.stacked_widget.addWidget(self.main_screen)
        self.stacked_widget.addWidget(self.farewell_screen)

        # Show profile selection screen initially
        self.stacked_widget.setCurrentWidget(self.profile_screen)

    def create_new_profile(self):
        # Yeni profil oluşturma ekranı
        profile_name, ok = QInputDialog.getText(self, "Yeni Profil", "Profil Adı:")
        if ok and profile_name:
            # Maksimum devir bilgisi al
            max_rpm, ok = QInputDialog.getInt(self, "Maksimum RPM", "Maksimum RPM Değeri:", 5000, 1000, 10000, 500)
            if ok:
                # Yakıt tipi seçimi
                fuel_types = ["Benzin", "Dizel", "Elektrik", "Hibrit"]
                fuel_type, ok = QInputDialog.getItem(self, "Yakıt Tipi", "Yakıt Tipini Seçin:", fuel_types, 0, False)
                if ok:
                    # Tork faktörü hesaplama (yakıt tipine göre)
                    torque_factor = {
                        "Benzin": 0.15,
                        "Dizel": 0.25,
                        "Elektrik": 0.35,
                        "Hibrit": 0.20
                    }.get(fuel_type, 0.15)

                    # Yeni profil oluştur ve listeye ekle
                    self.simulation_profiles[profile_name] = {
                        "max_rpm": max_rpm,
                        "torque_factor": torque_factor,
                        "fuel_type": fuel_type,
                        "color": Qt.yellow  # Varsayılan renk
                    }
                    self.profile_combo.addItem(profile_name)
                    self.profile_combo_main.addItem(profile_name)
                    QMessageBox.information(self, "Başarılı", f"Yeni profil oluşturuldu!\nYakıt Tipi: {fuel_type}")

    def start_with_selected_profile(self):
        selected_profile = self.profile_combo.currentText()
        if selected_profile:
            self.current_profile = selected_profile
            self.stacked_widget.setCurrentWidget(self.main_screen)
            self.statusBar().showMessage(f"{selected_profile} profili seçildi" if self.language == "tr" else f"{selected_profile} profile selected")
        else:
            QMessageBox.warning(self, "Uyarı", "Lütfen bir profil seçin!" if self.language == "tr" else "Please select a profile!")

    def show_main_screen(self):
        self.stacked_widget.setCurrentWidget(self.main_screen)

    def closeEvent(self, event):
        reply = QMessageBox.question(self, "Çıkış", "Uygulamayı kapatmak istediğinize emin misiniz?",
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            self.stacked_widget.setCurrentWidget(self.farewell_screen)
            QTimer.singleShot(2000, self.close)  # 2 saniye sonra kapat
        else:
            event.ignore()

    def initData(self):
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_data)
        self.timer.start(50)
        
        self.log_timer = QTimer(self)
        self.log_timer.timeout.connect(self.log_data)
        self.log_timer.start(1000)
        
        # Log klasörü oluştur
        if not os.path.exists('logs'):
            os.makedirs('logs')

    def setAnimationSpeed(self, speed):
        self.animation_speed = speed

    def toggle_night_mode(self, checked):
        self.night_mode = checked
        palette = self.palette()
        if checked:
            palette.setColor(QPalette.Window, QColor(25, 25, 25))
            palette.setColor(QPalette.WindowText, Qt.white)
            palette.setColor(QPalette.ButtonText, Qt.white)
            palette.setColor(QPalette.Text, Qt.white)
        else:
            palette.setColor(QPalette.Window, Qt.white)
            palette.setColor(QPalette.WindowText, Qt.black)
            palette.setColor(QPalette.ButtonText, Qt.black)
            palette.setColor(QPalette.Text, Qt.black)
        self.setPalette(palette)
        self.night_mode_btn.setText(("Gece Modu" if self.language == "tr" else "Night Mode") + (" (Açık)" if checked else " (Kapalı)"))

    def change_profile(self, profile):
        # Profil değiştirildiğinde göstergeleri güncelle
        self.current_profile = profile
        max_rpm = self.simulation_profiles[profile]["max_rpm"]
        self.rpm_gauge.setRange(0, max_rpm)
        self.rpm_gauge.setRedline(max_rpm * 0.8)
        self.statusBar().showMessage(f"{profile} profili aktif" if self.language == "tr" else f"{profile} profile active")

    def change_language(self, lang):
        self.language = lang
        self.rpm_gauge.setLanguage(lang)
        self.torque_gauge.setLanguage(lang)
        self.update_ui_texts()

    def update_ui_texts(self):
        self.night_mode_btn.setText("Gece Modu" if self.language == "tr" else "Night Mode")
        self.language_combo.setItemText(0, "Türkçe" if self.language == "tr" else "Turkish")
        self.language_combo.setItemText(1, "İngilizce" if self.language == "tr" else "English")
        # Diğer metinler de burada güncellenebilir.

    def update_data(self):
        current_rpm = self.rpm_gauge.value
        target_rpm = self.calculate_rpm(current_rpm)
        torque = self.calculate_torque(target_rpm)
        
        self.animate_gauge(self.rpm_gauge, target_rpm)
        self.animate_gauge(self.torque_gauge, torque)

    def calculate_rpm(self, current_rpm):
        max_rpm = self.simulation_profiles[self.current_profile]["max_rpm"]
        change = random.randint(-300, 500)
        new_rpm = current_rpm + change
        
        if new_rpm < 800:
            return 800 + random.randint(0, 200)
        elif new_rpm > max_rpm * 0.95:
            return max_rpm * 0.95 - random.randint(0, 500)
        return new_rpm

    def calculate_torque(self, rpm):
        max_rpm = self.simulation_profiles[self.current_profile]["max_rpm"]
        torque_factor = self.simulation_profiles[self.current_profile]["torque_factor"]
        
        # Parabolik tork eğrisi
        if rpm < max_rpm * 0.3:
            return int(50 + (rpm**2) * 0.0005)
        elif rpm < max_rpm * 0.7:
            return int(200 + rpm * 0.2)
        else:
            return int(350 - (rpm - max_rpm*0.7) * 0.3)

    def animate_gauge(self, gauge, target_value):
        animation = QPropertyAnimation(gauge, b"value")
        animation.setDuration(abs(target_value - gauge.value) * 2)
        animation.setStartValue(gauge.value)
        animation.setEndValue(target_value)
        animation.start()

    def log_data(self):
        if not self.logging_active:
            return
            
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        data = [timestamp, self.rpm_gauge.value, self.torque_gauge.value, self.current_profile]
        
        try:
            log_file = 'logs/vehicle_log.csv'
            # Log dosyası boyut kontrolü (10MB)
            if os.path.exists(log_file) and os.path.getsize(log_file) > 10*1024*1024:
                self.rotate_logs()
                
            with open(log_file, 'a', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                if f.tell() == 0:  # Dosya boşsa başlık yaz
                    headers = ["Timestamp", "RPM", "Torque", "Profile"]
                    writer.writerow(headers)
                writer.writerow(data)
        except Exception as e:
            print(f"Loglama hatası: {e}")

    def rotate_logs(self):
        try:
            log_file = 'logs/vehicle_log.csv'
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_file = f'logs/vehicle_log_{timestamp}.csv'
            os.rename(log_file, backup_file)
        except Exception as e:
            print(f"Log rotasyon hatası: {e}")

    def manage_profiles(self):
        # Profil yönetim ekranı
        dialog = QInputDialog(self)
        dialog.setWindowTitle("Profil Yönetimi")
        dialog.setLabelText("Bir işlem seçin:")
        dialog.setComboBoxItems(["Profil Adını Değiştir", "Profil Sil", "Yeni Profil Ekle"])
        dialog.setComboBoxEditable(False)
        ok = dialog.exec_()

        if ok:
            action = dialog.textValue()
            if action == "Profil Adını Değiştir":
                self.rename_profile()
            elif action == "Profil Sil":
                self.delete_profile()
            elif action == "Yeni Profil Ekle":
                self.create_new_profile()

    def rename_profile(self):
        # Profil adını değiştirme
        current_profile, ok = QInputDialog.getItem(self, "Profil Adını Değiştir", "Değiştirmek istediğiniz profili seçin:", 
                                                   self.simulation_profiles.keys(), 0, False)
        if ok and current_profile:
            new_name, ok = QInputDialog.getText(self, "Yeni Profil Adı", "Yeni profil adını girin:")
            if ok and new_name:
                self.simulation_profiles[new_name] = self.simulation_profiles.pop(current_profile)
                self.update_profile_combos()
                QMessageBox.information(self, "Başarılı", f"Profil adı '{current_profile}' -> '{new_name}' olarak değiştirildi!")

    def delete_profile(self):
        # Profil silme
        profile_to_delete, ok = QInputDialog.getItem(self, "Profil Sil", "Silmek istediğiniz profili seçin:", 
                                                     self.simulation_profiles.keys(), 0, False)
        if ok and profile_to_delete:
            if profile_to_delete == self.current_profile:
                QMessageBox.warning(self, "Hata", "Aktif profili silemezsiniz!")
                return
            del self.simulation_profiles[profile_to_delete]
            self.update_profile_combos()
            QMessageBox.information(self, "Başarılı", f"'{profile_to_delete}' profili silindi!")

    def update_profile_combos(self):
        # Profil listelerini güncelle
        self.profile_combo.clear()
        self.profile_combo.addItems(self.simulation_profiles.keys())
        self.profile_combo_main.clear()
        self.profile_combo_main.addItems(self.simulation_profiles.keys())

    def show_about_message(self):
        QMessageBox.information(
            self,
            "Hakkında",
            "Bu uygulama İrfanDelil tarafından yapılmıştır.\n"
            "Tüm hakları saklıdır. © 2023\n\n"
            "İletişim: irfandelil@example.com"
        )

    def get_profile_selection(self, title, label):
        profile, ok = QInputDialog.getItem(self, title, label, self.simulation_profiles.keys(), 0, False)
        return profile if ok else None


if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    main_window = TorqueInterface()
    main_window.show()
    sys.exit(app.exec_())