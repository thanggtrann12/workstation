from PyQt5.QtWidgets import QApplication, QMainWindow, QTextEdit, QVBoxLayout, QWidget, QLineEdit, QSystemTrayIcon, QMenu, QAction, qApp, QStyle
from PyQt5.QtCore import Qt, QEvent
import socketio
import json


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("SocketIO GUI")
        self.channel = "chat"
        self.text_edit = QTextEdit(self)
        self.input_box = QLineEdit(self)
        self.input_box.returnPressed.connect(self.send_message)

        layout = QVBoxLayout()
        layout.addWidget(self.text_edit)
        layout.addWidget(self.input_box)

        widget = QWidget(self)
        widget.setLayout(layout)
        self.setCentralWidget(widget)

        self.socket = socketio.Client()
        self.socket.connect("http://127.0.0.1:5000")

        @self.socket.on("chat")
        def handle_message(message):
            self.text_edit.append(str(message))
            if self.isHidden():
                self.show()
                self.setWindowState(Qt.WindowActive)

        # Create system tray icon
        self.tray_icon = QSystemTrayIcon(self)
        self.tray_icon.setIcon(
            self.style().standardIcon(QStyle.SP_ComputerIcon))

        # Create tray menu
        tray_menu = QMenu(self)
        show_action = QAction("Show", self)
        exit_action = QAction("Exit", self)
        tray_menu.addAction(show_action)
        tray_menu.addAction(exit_action)

        # Set the tray menu
        self.tray_icon.setContextMenu(tray_menu)

        # Show the main window when the tray icon is clicked
        show_action.triggered.connect(self.show)

        # Exit the application when the "Exit" action is triggered
        exit_action.triggered.connect(qApp.quit)

        self.tray_icon.show()

    def send_message(self):
        message = "ADMIN:   "+self.input_box.text()
        self.socket.emit(self.channel, message)
        self.input_box.clear()

    def changeEvent(self, event):
        if event.type() == QEvent.WindowStateChange:
            if self.isMinimized():
                event.ignore()
                self.hide()
                self.tray_icon.showMessage(
                    "SocketIO GUI", "Application minimized to tray.")
        super().changeEvent(event)

    def closeEvent(self, event):
        self.socket.disconnect()


if __name__ == "__main__":
    app = QApplication([])
    window = MainWindow()
    window.show()
    app.exec()
