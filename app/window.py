from datetime import datetime
import logging
import pygame
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QFont, QKeySequence, QShortcut
from PySide6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QSlider, QFrame, QPlainTextEdit, QProgressBar,
    QScrollArea, QBoxLayout, QSizePolicy)
from app.ble_worker import BleWorker
from app.drive import motor_power

STYLE = """
QMainWindow, QWidget { background: #10151f; color: #edf2fc; font-family: 'Segoe UI'; font-size: 14px; }
QFrame#card { background: #1a2230; border: 1px solid #2b3648; border-radius: 16px; }
QFrame#card QLabel { background: transparent; }
QLabel#title { font-size: 32px; font-weight: 700; }
QLabel#footer { color: #8590a2; font-size: 11px; background: transparent; }
QScrollArea { border: none; }
QLabel#muted { color: #99aac2; }
QPushButton { background: #29364c; border: 1px solid #3b4e68; border-radius: 9px; padding: 12px 20px; font-weight: 600; }
QPushButton:hover { background: #354964; }
QPushButton:pressed { background: #17253a; }
QPushButton:disabled { color: #64748b; border-color: #263247; }
QPushButton#connect { background: #3c75eb; border: none; }
QPushButton#stop { background: #d33e52; border: none; font-size: 20px; padding: 20px; }
QPushButton#stop:hover { background: #ea4d63; }
QSlider::groove:horizontal { height: 7px; background: #344157; border-radius: 3px; }
QSlider::sub-page:horizontal { background: #5d92ff; border-radius: 3px; }
QSlider::handle:horizontal { background: #edf2fc; width: 18px; margin: -6px 0; border-radius: 9px; }
QPlainTextEdit { background: #111925; border: 1px solid #2b3648; border-radius: 9px; padding: 10px; color: #adbed5; font-family: Consolas; font-size: 12px; }
QProgressBar { background: #101925; border: none; border-radius: 5px; height: 10px; }
QProgressBar::chunk { background: #5d92ff; border-radius: 5px; }
"""


def label(text, name=None):
    widget = QLabel(text)
    widget.setWordWrap(True)
    widget.setMinimumWidth(0)
    widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
    if name:
        widget.setObjectName(name)
    return widget


def card():
    frame = QFrame()
    frame.setObjectName("card")
    layout = QVBoxLayout(frame)
    layout.setContentsMargins(22, 20, 22, 20)
    layout.setSpacing(14)
    return frame, layout


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("SPIKE Controller")
        self.setMinimumSize(360, 320)
        available = self.screen().availableGeometry()
        self.resize(min(900, available.width()), min(800, available.height()))
        self.responsive_rows = []
        self.setStyleSheet(STYLE)
        self.worker = None
        self.controller = None
        self.is_ready = False
        self.closing = False
        root = QWidget()
        self.setCentralWidget(root)
        shell = QVBoxLayout(root)
        shell.setContentsMargins(0, 0, 0, 0)
        shell.setSpacing(0)
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        content = QWidget()
        self.scroll.setWidget(content)
        shell.addWidget(self.scroll, 1)
        self.footer = label("Developed by Ahmed Shaaban", "footer")
        self.footer.setAlignment(Qt.AlignCenter)
        self.footer.setContentsMargins(12, 8, 12, 10)
        shell.addWidget(self.footer)
        layout = QVBoxLayout(content)
        self.content_layout = layout
        layout.setContentsMargins(30, 26, 30, 26)
        layout.setSpacing(18)
        layout.addWidget(label("SPIKE Controller", "title"))
        layout.addWidget(label("Your controller. Your robot. Ready to explore.", "muted"))
        connection, box = card()
        row = QHBoxLayout()
        self.hub_status = label("●  Disconnected")
        self.pad_status = label("●  Controller not detected")
        row.addWidget(self.hub_status)
        row.addStretch()
        row.addWidget(self.pad_status)
        self.responsive_rows.append(row)
        box.addLayout(row)
        self.program_status = label("Hub program • awaiting connection", "muted")
        box.addWidget(self.program_status)
        row = QHBoxLayout()
        self.connect_button = QPushButton("Connect to Hub")
        self.connect_button.setObjectName("connect")
        self.disconnect_button = QPushButton("Disconnect")
        self.disconnect_button.setEnabled(False)
        row.addWidget(self.connect_button)
        row.addWidget(self.disconnect_button)
        row.addStretch()
        self.responsive_rows.append(row)
        box.addLayout(row)
        layout.addWidget(connection)
        drive, box = card()
        row = QHBoxLayout()
        row.addWidget(label("DRIVE POWER"))
        row.addStretch()
        self.speed_text = label("100%")
        row.addWidget(self.speed_text)
        box.addLayout(row)
        self.speed = QSlider(Qt.Horizontal)
        self.speed.setRange(10, 100)
        self.speed.setValue(100)
        self.speed.valueChanged.connect(lambda n: self.speed_text.setText(f"{n}%"))
        box.addWidget(self.speed)
        row = QHBoxLayout()
        self.motors = []
        for name in ("Motor A", "Motor B"):
            column = QVBoxLayout()
            text = label(f"{name}   +0")
            bar = QProgressBar()
            bar.setRange(0, 100)
            bar.setValue(0)
            bar.setTextVisible(False)
            column.addWidget(text)
            column.addWidget(bar)
            row.addLayout(column)
            self.motors.append((name, text, bar))
        box.addLayout(row)
        box.addWidget(label("Left stick to drive • D-pad for direction • Space to stop", "muted"))
        layout.addWidget(drive)
        self.stop_button = QPushButton("■   STOP MOTORS")
        self.stop_button.setObjectName("stop")
        self.stop_button.clicked.connect(self.stop)
        layout.addWidget(self.stop_button)
        layout.addWidget(label("After STOP, release the stick and D-pad before driving again.", "muted"))
        layout.addWidget(label("ACTIVITY"))
        self.activity = QPlainTextEdit()
        self.activity.setReadOnly(True)
        self.activity.setMaximumBlockCount(500)
        self.activity.setMinimumHeight(120)
        layout.addWidget(self.activity, 1)
        self.connect_button.clicked.connect(self.connect_hub)
        self.disconnect_button.clicked.connect(self.disconnect_hub)
        self.shortcut = QShortcut(QKeySequence("Space"), self)
        self.shortcut.activated.connect(self.stop)
        pygame.display.init()
        pygame.joystick.init()
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.read_controller)
        self.timer.start(25)
        self.log("Ready. Turn on your Hub, then choose Connect to Hub.")

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if not hasattr(self, "content_layout"):
            return
        compact = self.width() < 620
        margin = 14 if compact else 30
        self.content_layout.setContentsMargins(margin, 20, margin, 20)
        for row in self.responsive_rows:
            row.setDirection(QBoxLayout.TopToBottom if compact else QBoxLayout.LeftToRight)

    def log(self, message):
        logging.info(message)
        self.activity.appendPlainText(f"{datetime.now():%H:%M:%S}  {message}")

    def connect_hub(self):
        if self.worker and self.worker.isRunning():
            return
        self.worker = BleWorker()
        self.worker.state.connect(self.set_state)
        self.worker.log.connect(self.log)
        self.worker.power.connect(self.set_power)
        self.worker.ready.connect(self.set_ready)
        self.worker.finished.connect(self.worker_finished)
        self.connect_button.setEnabled(False)
        self.disconnect_button.setEnabled(True)
        self.worker.start()

    def set_state(self, state):
        self.hub_status.setText(f"●  {state}")
        self.hub_status.setStyleSheet(f"color: {'#62ddb0' if state == 'Connected' else '#f4ba67' if state != 'Disconnected' else '#99aac2'};")

    def set_ready(self, ready):
        self.is_ready = ready
        self.program_status.setText("Hub program • running" if ready else "Hub program • movement disabled")

    def set_power(self, a, b):
        for (name, text, bar), value in zip(self.motors, (a, b)):
            text.setText(f"{name}   {value:+d}")
            bar.setValue(abs(value))

    def stop(self):
        if self.worker:
            self.worker.stop_motors()
        self.log("STOP requested. Release controls to neutral.")

    def disconnect_hub(self):
        if self.worker and self.worker.isRunning():
            self.is_ready = False
            self.disconnect_button.setEnabled(False)
            self.worker.shutdown()
            self.log("Stopping motors and disconnecting…")

    def worker_finished(self):
        self.connect_button.setEnabled(True)
        self.connect_button.setText("Reconnect to Hub")
        self.disconnect_button.setEnabled(False)
        if self.closing:
            self.close()

    def read_controller(self):
        try:
            events = pygame.event.get()
            removed = any(event.type == pygame.JOYDEVICEREMOVED and self.controller
                          and event.instance_id == self.controller.get_instance_id() for event in events)
            if removed:
                self.controller.quit()
                self.controller = None
                if self.worker:
                    self.worker.stop_motors()
                self.pad_status.setText("●  Controller disconnected")
                self.pad_status.setStyleSheet("color: #f07889")
                self.log("Controller disconnected. Stop requested.")
            if self.controller is None:
                for i in range(pygame.joystick.get_count()):
                    candidate = pygame.joystick.Joystick(i)
                    candidate.init()
                    if any(name in candidate.get_name().lower() for name in ("ps4", "dualshock", "wireless controller")):
                        self.controller = candidate
                        self.pad_status.setText(f"●  {candidate.get_name()}")
                        self.pad_status.setStyleSheet("color: #62ddb0")
                        self.log(f"Controller connected: {candidate.get_name()}")
                        break
                    candidate.quit()
            if self.controller and self.is_ready and self.worker:
                x = self.controller.get_axis(0)
                y = -self.controller.get_axis(1)
                hat = self.controller.get_hat(0) if self.controller.get_numhats() else (0, 0)
                self.worker.command(*motor_power(x, y, hat, self.speed.value()))
        except pygame.error as exc:
            if self.worker:
                self.worker.stop_motors()
            self.controller = None
            self.pad_status.setText("●  Controller unavailable")
            self.log(f"Controller: {exc}")

    def closeEvent(self, event):
        if self.worker and self.worker.isRunning():
            event.ignore()
            if not self.closing:
                self.closing = True
                self.timer.stop()
                self.disconnect_hub()
                self.connect_button.setEnabled(False)
            return
        pygame.quit()
        event.accept()
