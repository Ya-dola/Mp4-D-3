import os
import subprocess
import sys

import ffmpeg
import qdarktheme
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QApplication, QLabel, QVBoxLayout, QWidget, QFileDialog, QComboBox, QPushButton, \
    QProgressBar, QTextEdit, QLineEdit, QDesktopWidget, QHBoxLayout, QFrame, QCheckBox


class HorizontalLine(QFrame):
    def __init__(self):
        super().__init__()
        self.setFrameShape(QFrame.HLine)
        self.setFrameShadow(QFrame.Plain)


class VerticalLine(QFrame):
    def __init__(self):
        super().__init__()
        self.setFrameShape(QFrame.VLine)
        self.setFrameShadow(QFrame.Plain)


# noinspection PyUnresolvedReferences
class HoverableLabel(QLabel):
    clicked = pyqtSignal()  # Define a custom clicked signal

    def __init__(self, text, parent=None):
        super().__init__(text, parent)
        self.setMouseTracking(True)
        self.normal_color = '#e4e7eb'

    def enterEvent(self, event):
        primary_color = '#db885e'
        self.setStyleSheet(f"color: {primary_color}; text-decoration: underline;")
        self.setCursor(Qt.PointingHandCursor)
        super().enterEvent(event)

    def leaveEvent(self, event):
        self.setStyleSheet(f"color: {self.normal_color};")
        self.setCursor(Qt.ArrowCursor)
        super().leaveEvent(event)

    def mousePressEvent(self, event):
        self.clicked.emit()  # Emit the custom clicked signal
        super().mousePressEvent(event)


# noinspection PyUnresolvedReferences
class LeftAlignedCheckBox(QWidget):
    def __init__(self, text, parent=None):
        super().__init__(parent)
        self.layout = QHBoxLayout()
        self.checkbox = QCheckBox()
        self.label = HoverableLabel(text)
        self.label.clicked.connect(self.checkbox.toggle)
        self.layout.addWidget(self.label)
        self.layout.addWidget(self.checkbox)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(self.layout)

    def set_checked(self, checked):
        self.checkbox.setChecked(checked)

    def is_checked(self):
        return self.checkbox.isChecked()


# noinspection PyUnresolvedReferences
class MP4toMP3Converter(QWidget):
    BITRATE_MAPPING = {
        'Variable': 'Variable',
        '128k': '128000',
        '192k': '192000',
        '256k': '256000',
        '320k': '320000'
    }

    def __init__(self):
        super().__init__()
        self.input_entry = None
        self.output_entry = None
        self.bitrate_dropdown = None
        self.file_count_label = None
        self.status_label = None
        self.convert_button = None
        self.progress_bar = None
        self.open_output_checkbox = None
        self.open_output_button = None
        self.conversion_output = None
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        # Sizes
        btn_width = 80
        btn_height = 26
        btn_folder_width = 40
        btn_folder_height = 26

        # Input Folder
        input_layout = QHBoxLayout()
        input_label = QLabel('Input Folder:')
        self.input_entry = QLineEdit()
        input_select_button = QPushButton('📁')
        input_select_button.setFixedSize(btn_folder_width, btn_folder_height)
        input_select_button.clicked.connect(self.select_input_folder)
        input_layout.addWidget(input_label)
        input_layout.addWidget(self.input_entry)
        input_layout.addWidget(input_select_button)
        layout.addLayout(input_layout)
        layout.addWidget(HorizontalLine())

        # Output Folder
        output_layout = QHBoxLayout()
        output_label = QLabel('Output Folder:')
        self.output_entry = QLineEdit()
        output_select_button = QPushButton('📁')
        output_select_button.setFixedSize(btn_folder_width, btn_folder_height)
        output_select_button.clicked.connect(self.select_output_folder)
        output_layout.addWidget(output_label)
        output_layout.addWidget(self.output_entry)
        output_layout.addWidget(output_select_button)
        layout.addLayout(output_layout)
        layout.addWidget(HorizontalLine())

        # Audio Bitrate and File Count
        bitrate_layout = QHBoxLayout()
        bitrate_label = QLabel('Audio Bitrate 🎧:')
        self.bitrate_dropdown = QComboBox()
        self.bitrate_dropdown.addItems(['Variable', '128k', '192k', '256k', '320k'])
        self.bitrate_dropdown.setFixedSize(btn_width, btn_height)
        self.file_count_label = QLabel('MP4 Files: ❌')
        bitrate_layout.addWidget(bitrate_label)
        bitrate_layout.addWidget(self.bitrate_dropdown)
        bitrate_layout.addStretch(1)
        bitrate_layout.addWidget(VerticalLine())
        bitrate_layout.addStretch(2)
        bitrate_layout.addWidget(self.file_count_label)
        bitrate_layout.addStretch(2)
        layout.addLayout(bitrate_layout)
        layout.addWidget(HorizontalLine())

        # Status and Convert Button
        status_layout = QHBoxLayout()
        self.status_label = QLabel('Select Input & Output Folders 🚩')
        self.convert_button = QPushButton('Convert')
        self.convert_button.setFixedSize(btn_width, btn_height)
        self.convert_button.clicked.connect(self.convert_mp4_files_to_mp3)
        self.convert_button.setEnabled(False)
        status_layout.addStretch(1)
        status_layout.addWidget(self.status_label)
        status_layout.addStretch(1)
        status_layout.addWidget(self.convert_button)
        layout.addLayout(status_layout)
        layout.addWidget(HorizontalLine())

        # Progress Bar
        self.progress_bar = QProgressBar()
        layout.addWidget(self.progress_bar)
        layout.addWidget(HorizontalLine())

        # Conversion Output with Heading
        conversion_layout = QHBoxLayout()
        conversion_output_label = QLabel('Conversion Output 📒')
        self.open_output_checkbox = LeftAlignedCheckBox('Open Output 📁 after Converting')
        self.open_output_checkbox.set_checked(False)
        self.open_output_button = QPushButton('Output 📂')
        self.open_output_button.setFixedSize(btn_width, btn_height)
        self.open_output_button.clicked.connect(self.open_output_folder)
        self.open_output_button.setEnabled(False)
        conversion_layout.addWidget(conversion_output_label)
        conversion_layout.addStretch(1)
        conversion_layout.addWidget(self.open_output_checkbox)
        conversion_layout.addStretch(1)
        conversion_layout.addWidget(self.open_output_button)
        layout.addLayout(conversion_layout)
        self.conversion_output = QTextEdit()
        self.conversion_output.setPlaceholderText('Conversion Output will be shown here 📝...')
        self.conversion_output.setReadOnly(True)
        layout.addWidget(self.conversion_output)

        # Window Settings
        self.setLayout(layout)
        self.setWindowTitle('Yadola MP4 to MP3 Converter')
        self.setFixedWidth(760)
        self.setFixedHeight(400)
        # self.setWindowFlags(Qt.WindowStaysOnTopHint)  # Always on top
        self.center_on_screen()  # Center the window on the screen

    def center_on_screen(self):
        rect = self.frameGeometry()
        center_point = QDesktopWidget().availableGeometry().center()
        rect.moveCenter(center_point)
        self.move(rect.topLeft())

    def select_input_folder(self):
        folder_selected = QFileDialog.getExistingDirectory(self, 'Select Input Folder')
        if folder_selected:
            self.input_entry.setText(folder_selected)
        else:
            self.input_entry.setText('')  # Set input entry to blank if Cancel is clicked
        self.update_file_count()
        self.check_converting_state()

    def select_output_folder(self):
        folder_selected = QFileDialog.getExistingDirectory(self, 'Select Output Folder')
        if folder_selected:
            self.output_entry.setText(folder_selected)
        else:
            self.output_entry.setText('')  # Set output entry to blank if Cancel is clicked
        self.check_converting_state()

    def update_file_count(self):
        input_folder = self.input_entry.text()

        if input_folder:
            file_count = len([filename for filename in os.listdir(input_folder) if filename.endswith('.mp4')])
            self.file_count_label.setText(f'MP4 Files: {file_count}')
        else:
            self.file_count_label.setText('MP4 Files: ❌')

    def open_output_folder(self):
        output_folder = self.output_entry.text()

        if output_folder and os.path.exists(output_folder):
            if sys.platform == 'win32':
                os.startfile(output_folder)  # Opens the folder in Windows Explorer
            elif sys.platform == 'darwin':
                subprocess.Popen(['open', output_folder])  # Opens the folder in Finder (MacOS)
            else:
                subprocess.Popen(['xdg-open', output_folder])  # Opens the folder in Linux file manager

    def check_converting_state(self):
        input_folder = self.input_entry.text()
        output_folder = self.output_entry.text()

        if input_folder:
            mp4_files_count = len([filename for filename in os.listdir(input_folder) if filename.endswith('.mp4')])
            if mp4_files_count == 0:
                self.status_label.setText('No MP4 Files in Input Folder ❌')
                self.convert_button.setEnabled(False)
            elif output_folder:
                self.status_label.setText('Ready to Convert 👍')
                self.convert_button.setEnabled(True)
                self.open_output_button.setEnabled(True)
            else:
                self.status_label.setText('Select Output Folder 🚩')
                self.convert_button.setEnabled(False)
                self.open_output_button.setEnabled(False)
        else:
            self.status_label.setText('Select Input Folder 🚩')
            self.convert_button.setEnabled(False)
            self.open_output_button.setEnabled(False)

    def convert_mp4_files_to_mp3(self):
        # Reset Progress Bar and Output
        self.progress_bar.setValue(0)
        self.conversion_output.clear()

        input_folder = self.input_entry.text()
        output_folder = self.output_entry.text()
        selected_bitrate = self.BITRATE_MAPPING[self.bitrate_dropdown.currentText()]

        self.status_label.setText('Converting ♾️')
        QApplication.processEvents()

        try:
            total_files = len([filename for filename in os.listdir(input_folder) if filename.endswith('.mp4')])
            processed_files = 0

            for filename in os.listdir(input_folder):
                if filename.endswith('.mp4'):
                    input_file = os.path.join(input_folder, filename)
                    output_file = os.path.join(output_folder, os.path.splitext(filename)[0] + '.mp3')

                    if selected_bitrate == 'Variable':
                        # Remove args "capture_stdout=True, capture_stderr=True" from .run() to show console output
                        ffmpeg.input(input_file, vsync='2').output(output_file,
                                                                   y='-y', loglevel='quiet', hide_banner='-hide_banner',
                                                                   nostats='-nostats').run(capture_stdout=True,
                                                                                           capture_stderr=True)
                    else:
                        ffmpeg.input(input_file, vsync='2').output(output_file, audio_bitrate=selected_bitrate,
                                                                   y='-y', loglevel='quiet', hide_banner='-hide_banner',
                                                                   nostats='-nostats').run(capture_stdout=True,
                                                                                           capture_stderr=True)

                    self.conversion_output.append(f'--------------\n'
                                                  f'Converted: {filename} -> {os.path.basename(output_file)}'
                                                  f'\n--------------')
                    processed_files += 1
                    progress_value = int((processed_files / total_files) * 100)
                    self.progress_bar.setValue(progress_value)
                    QApplication.processEvents()

            self.status_label.setText('Conversion Done ✅')
            self.progress_bar.setValue(100)

            if self.open_output_checkbox.is_checked():
                self.open_output_folder()
        except Exception as e:
            error_message = f'Error Converting: {e}'
            self.conversion_output.append(error_message)  # Add error message to conversion output
            self.status_label.setText('Error Converting ❌')

        QApplication.processEvents()


if __name__ == '__main__':
    # Set the application icon dynamically
    if hasattr(sys, '_MEIPASS'):
        # If the script is run as a PyInstaller executable
        # noinspection PyProtectedMember
        icon_path = os.path.join(sys._MEIPASS, 'icon.ico')
    else:
        # If the script is run as a Python script
        icon_path = 'icon.ico'

    app = QApplication(sys.argv)
    app.setWindowIcon(QIcon(icon_path))
    qdarktheme.setup_theme(
        custom_colors={"primary": "#db885e",
                       "input.background": "#45332d99",
                       "primary>progressBar.background": "#4fa17e",
                       "primary>button.hoverBackground": "#f59f6633"
                       })
    window = MP4toMP3Converter()
    window.show()
    sys.exit(app.exec_())
