"""
Main window of the application (View).

This module is responsible for the application's user interface.
It should contain minimal business logic. Its primary roles are:
- Displaying data to the user.
- Capturing user input (e.g., button clicks, file selections).
- Forwarding user actions to the Controller.
- Updating the UI based on signals received from the Controller.
"""
import sys
import os
from pathlib import Path

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLineEdit, QTextEdit, QProgressBar, QFileDialog,
    QMessageBox, QTabWidget, QGroupBox
)
from PyQt6.QtCore import Qt

from src.utils.package_manager import check_and_install_dependencies
from src.controllers.media_controller import MediaController
from src.utils import helpers
from src.config import settings

class MainWindow(QMainWindow):
    """Main window of the application (View)."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Media Mixer")

        # Centralized controller for all business logic
        self.controller = MediaController()

        # Basic checks before initializing UI
        if not helpers.check_ffmpeg(settings.FFMPEG_PATH):
            QMessageBox.critical(self, "Error", "FFmpeg is required but not found.")
            sys.exit(1)

        self.init_ui()
        self.connect_signals()
        self.load_last_used_paths()

    def init_ui(self):
        """Initialize the user interface components."""
        self.setMinimumSize(700, 600)
        self.center_window()

        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QVBoxLayout(main_widget)

        # --- Tabs ---
        self.tabs = QTabWidget()
        self.tab_directory = QWidget()
        self.tab_single = QWidget()
        self.tabs.addTab(self.tab_directory, "Process Directory")
        self.tabs.addTab(self.tab_single, "Process Single File")
        main_layout.addWidget(self.tabs)

        self._setup_directory_tab()
        self._setup_single_file_tab()

        # --- Common UI Elements ---
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setFormat("%p%")
        main_layout.addWidget(self.progress_bar)

        self.output_text = QTextEdit()
        self.output_text.setReadOnly(True)
        main_layout.addWidget(self.output_text)

        exit_btn = QPushButton("Exit")
        exit_btn.clicked.connect(self.close)
        main_layout.addWidget(exit_btn, alignment=Qt.AlignmentFlag.AlignRight)

    def _setup_directory_tab(self):
        """Set up the UI for the directory processing tab."""
        layout = QVBoxLayout(self.tab_directory)
        dir_layout = QHBoxLayout()
        
        self.dir_input = QLineEdit()
        self.dir_input.setPlaceholderText("Select input directory...")
        self.dir_input.setReadOnly(True)
        
        browse_btn = QPushButton("Browse")
        browse_btn.clicked.connect(self.browse_directory)
        
        dir_layout.addWidget(self.dir_input)
        dir_layout.addWidget(browse_btn)
        layout.addLayout(dir_layout)

        self.start_dir_btn = QPushButton("Start Processing Directory")
        self.start_dir_btn.clicked.connect(self.start_directory_processing)
        self.start_dir_btn.setEnabled(False)
        layout.addWidget(self.start_dir_btn)
        layout.addStretch()

    def _setup_single_file_tab(self):
        """Set up the UI for the single file processing tab."""
        layout = QVBoxLayout(self.tab_single)

        # MP3 selection
        mp3_group = QGroupBox("Select MP3 File")
        mp3_layout = QHBoxLayout(mp3_group)
        self.mp3_input = QLineEdit()
        self.mp3_input.setPlaceholderText("Select an MP3 file...")
        self.mp3_input.setReadOnly(True)
        browse_mp3_btn = QPushButton("Browse")
        browse_mp3_btn.clicked.connect(self.browse_mp3_file)
        mp3_layout.addWidget(self.mp3_input)
        mp3_layout.addWidget(browse_mp3_btn)
        layout.addWidget(mp3_group)

        # Media source selection
        media_group = QGroupBox("Select Media Source (Image/Video)")
        media_layout = QHBoxLayout(media_group)
        self.media_input = QLineEdit()
        self.media_input.setPlaceholderText("Select a JPG, WEBP, or MP4 file...")
        self.media_input.setReadOnly(True)
        browse_media_btn = QPushButton("Browse")
        browse_media_btn.clicked.connect(self.browse_media_file)
        media_layout.addWidget(self.media_input)
        media_layout.addWidget(browse_media_btn)
        layout.addWidget(media_group)

        # Output directory selection
        output_dir_group = QGroupBox("Select Output Directory")
        output_dir_layout = QHBoxLayout(output_dir_group)
        self.output_dir_input = QLineEdit()
        self.output_dir_input.setPlaceholderText("Select a directory to save the result...")
        self.output_dir_input.setReadOnly(True)
        browse_output_dir_btn = QPushButton("Browse")
        browse_output_dir_btn.clicked.connect(self.browse_output_directory)
        output_dir_layout.addWidget(self.output_dir_input)
        output_dir_layout.addWidget(browse_output_dir_btn)
        layout.addWidget(output_dir_group)

        self.start_single_btn = QPushButton("Start Processing Single File")
        self.start_single_btn.clicked.connect(self.start_single_file_processing)
        self.start_single_btn.setEnabled(False)
        layout.addWidget(self.start_single_btn)
        layout.addStretch()

    def connect_signals(self):
        """Connect signals from the controller to UI slots."""
        self.controller.progress_update.connect(self.update_output)
        self.controller.progress_value.connect(self.progress_bar.setValue)
        self.controller.processing_finished.connect(self.on_processing_complete)

    # --- Action Handlers / Slots --- 

    def start_directory_processing(self):
        """Action to start directory processing. Forwards call to controller."""
        input_dir = self.dir_input.text()
        if not input_dir:
            QMessageBox.warning(self, "Warning", "Please select an input directory.")
            return

        self.output_text.clear()
        self.progress_bar.setValue(0)
        self.set_ui_enabled(False)
        self.controller.process_directory(input_dir)

    def start_single_file_processing(self):
        """Action to start single file processing. Forwards call to controller."""
        mp3_path = self.mp3_input.text()
        media_path = self.media_input.text()
        output_dir = self.output_dir_input.text()

        if not all([mp3_path, media_path, output_dir]):
            QMessageBox.warning(self, "Warning", "Please select an MP3, a media file, and an output directory.")
            return

        self.output_text.clear()
        self.progress_bar.setValue(0)
        self.set_ui_enabled(False)
        self.controller.process_single_pair(mp3_path, media_path, output_dir)

    def on_processing_complete(self, success: bool):
        """Slot to handle completion of a processing task."""
        self.set_ui_enabled(True)
        if success:
            QMessageBox.information(self, "Done", "Processing completed successfully!")
        else:
            QMessageBox.warning(self, "Done", "Processing failed. Check logs for details.")

    def update_output(self, text: str):
        """Slot to append text to the output log."""
        self.output_text.append(text)
        self.output_text.verticalScrollBar().setValue(self.output_text.verticalScrollBar().maximum())

    # --- UI Helper Methods ---

    def set_ui_enabled(self, enabled: bool):
        """Enable or disable UI elements during processing."""
        self.tabs.setEnabled(enabled)
        self.start_dir_btn.setEnabled(enabled and bool(self.dir_input.text()))
        self.start_single_btn.setEnabled(enabled and self._are_single_inputs_valid())

    def browse_directory(self):
        """Open directory selection dialog for the directory tab."""
        dir_path = QFileDialog.getExistingDirectory(self, "Select Input Directory")
        if dir_path:
            self.dir_input.setText(dir_path)
            self.start_dir_btn.setEnabled(True)
            helpers.save_last_input_dir(dir_path) # This could also be moved to controller

    def browse_mp3_file(self):
        """Open file dialog for MP3 selection."""
        path, _ = QFileDialog.getOpenFileName(self, "Select MP3 File", "", "MP3 files (*.mp3)")
        if path:
            self.mp3_input.setText(path)
            self._check_single_file_inputs()

    def browse_media_file(self):
        """Open file dialog for media source selection."""
        path, _ = QFileDialog.getOpenFileName(self, "Select Media File", "", "Media files (*.jpg *.jpeg *.webp *.mp4)")
        if path:
            self.media_input.setText(path)
            self._check_single_file_inputs()

    def browse_output_directory(self):
        """Open directory dialog for single file output."""
        path = QFileDialog.getExistingDirectory(self, "Select Output Directory")
        if path:
            self.output_dir_input.setText(path)
            self._check_single_file_inputs()

    def _are_single_inputs_valid(self) -> bool:
        """Check if all inputs in the single file tab are filled."""
        return all([self.mp3_input.text(), self.media_input.text(), self.output_dir_input.text()])

    def _check_single_file_inputs(self):
        """Enable the start button if all single file inputs are valid."""
        self.start_single_btn.setEnabled(self._are_single_inputs_valid())

    def center_window(self):
        """Center the window on the primary screen."""
        screen = QApplication.primaryScreen().geometry()
        size = self.geometry()
        self.move(
            (screen.width() - size.width()) // 2,
            (screen.height() - size.height()) // 2
        )

    def load_last_used_paths(self):
        """Load the last used directory path from settings."""
        try:
            last_dir = helpers.load_last_input_dir()
            if last_dir and Path(last_dir).exists():
                self.dir_input.setText(last_dir)
                self.start_dir_btn.setEnabled(True)
        except Exception:
            pass # Ignore errors


def run_gui():
    """Initialize and run the GUI application."""
    if not check_and_install_dependencies():
        print("Error: Failed to install dependencies.", file=sys.stderr)
        sys.exit(1)
        
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec())
