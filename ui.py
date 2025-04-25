import os
import platform
import logging
from threading import Thread

from PyQt5 import QtWidgets, QtCore, QtGui

from .workers import RunEvent


class Ui_Form(object):
    """
    A PyQt5 UI form class for configuring and executing network diagnostics.

    """

    def setup_ui(self, form):
        """
        Set up the layout and UI elements of the diagnostics form.

        Args:
            form (QWidget): The parent widget to apply the layout and components to.
        """
        self.layout = QtWidgets.QVBoxLayout(form)

        # Input section layout
        self.input_layout = QtWidgets.QHBoxLayout()
        self.layout.addLayout(self.input_layout)

        # Source group
        self.source_group = QtWidgets.QGroupBox(form)
        self.source_group.setTitle("Source")
        self.input_layout.addWidget(self.source_group)

        self.source_layout = QtWidgets.QVBoxLayout(self.source_group)
        self.source_layout.setSpacing(10)

        self.source_text_input = QtWidgets.QTextEdit(self.source_group)
        self.source_text_input.setPlaceholderText("Paste text here...")
        self.source_layout.addWidget(self.source_text_input)

        self.source_file_button = QtWidgets.QPushButton(self.source_group)
        self.source_file_button.setText("Browse")
        self.source_file_button.setIcon(self._get_icon("file"))
        self.source_file_button.setIconSize(QtCore.QSize(20, 20))
        self.source_file_button.setFixedSize(150, 30)
        self.source_layout.addWidget(self.source_file_button)

        # Action layout with compare button
        self.actions_layout = QtWidgets.QVBoxLayout()
        self.actions_layout.setSpacing(0)
        self.input_layout.addLayout(self.actions_layout)

        self.actions_layout.addItem(QtWidgets.QSpacerItem(0, 0, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding))

        self.compare_button = QtWidgets.QPushButton(form)
        self.compare_button.setStyleSheet("QPushButton {background: transparent; border-radius: 15px;}")
        self.compare_button.setIcon(self._get_icon("compare"))
        self.compare_button.setMinimumSize(QtCore.QSize(80, 80))
        self.compare_button.setIconSize(QtCore.QSize(50, 50))
        self.actions_layout.addWidget(self.compare_button)

        self.compare_label = QtWidgets.QLabel(form)
        self.compare_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.compare_label.setText("Compare")
        self.actions_layout.addWidget(self.compare_label)

        self.actions_layout.addItem(QtWidgets.QSpacerItem(0, 0, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding))

        # Destination group
        self.dest_group = QtWidgets.QGroupBox(form)
        self.dest_group.setTitle("Destination")
        self.input_layout.addWidget(self.dest_group)

        self.dest_layout = QtWidgets.QVBoxLayout(self.dest_group)
        self.dest_layout.setSpacing(10)

        self.dest_text_input = QtWidgets.QTextEdit(self.dest_group)
        self.dest_text_input.setPlaceholderText("Paste text here...")
        self.dest_layout.addWidget(self.dest_text_input)

        self.dest_file_button = QtWidgets.QPushButton(self.dest_group)
        self.dest_file_button.setText("Browse")
        self.dest_file_button.setIcon(self._get_icon("file"))
        self.dest_file_button.setIconSize(QtCore.QSize(20, 20))
        self.dest_file_button.setFixedSize(150, 30)
        self.dest_layout.addWidget(self.dest_file_button)

        # Output section layout
        self.output_group = QtWidgets.QGroupBox(form)
        self.output_group.setTitle("Output")
        self.layout.addWidget(self.output_group)

        self.output_layout = QtWidgets.QHBoxLayout(self.output_group)

        self.last_report_button = QtWidgets.QPushButton(self.output_group)
        self.last_report_button.setText("Last Report")
        self.last_report_button.setIcon(self._get_icon("xls"))
        self.last_report_button.setIconSize(QtCore.QSize(20, 20))
        self.last_report_button.setFixedSize(150, 30)
        self.output_layout.addWidget(self.last_report_button)

        self.folder_button = QtWidgets.QPushButton(self.output_group)
        self.folder_button.setText("Folder")
        self.folder_button.setIcon(self._get_icon("opened-folder"))
        self.folder_button.setIconSize(QtCore.QSize(20, 20))
        self.folder_button.setFixedSize(150, 30)
        self.output_layout.addWidget(self.folder_button)

        self.output_layout.addItem(QtWidgets.QSpacerItem(0, 0, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum))

    def _get_icon(self, filename: str) -> QtGui.QIcon:
        """
        Load an icon from the assets directory.

        Args:
            filename (str): Name of the icon file (without extension).

        Returns:
            QtGui.QIcon: The QIcon object.
        """
        icon_path = os.path.join(os.path.dirname(__file__), "assets", f"{filename}.ico")
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap(icon_path), QtGui.QIcon.Mode.Normal, QtGui.QIcon.State.Off)
        return icon


class Form(QtWidgets.QWidget, Ui_Form):
    """
    UI Form class.

    """

    def __init__(self, parent=None, **kwargs):
        """
        Initialize the UI form.

        Args:
            parent (QWidget): Parent widget.
            **kwargs: Additional arguments for customization or metadata.
        """
        super().__init__(parent)
        self.kwargs = kwargs
        self.setup_ui(self)
        self.output_dir = os.path.join(self.kwargs.get("output_dir"), os.path.basename(os.path.dirname(__file__).upper()))
        self.output_report = ""
        self.data = {}

        # Connect UI buttons to methods
        self.source_file_button.clicked.connect(self.select_source_file)
        self.dest_file_button.clicked.connect(self.select_dest_file)
        self.compare_button.clicked.connect(self.run_comparison)
        self.last_report_button.clicked.connect(lambda: self.open_path(self.output_report))
        self.folder_button.clicked.connect(lambda: self.open_path(self.output_dir))

    def select_source_file(self):
        """
        Prompt user to select a source config file and load its content.
        """
        try:
            file_path = QtWidgets.QFileDialog.getOpenFileName(filter="(*.txt *.cfg)")[0]
            if file_path:
                logging.info(f"Source file selected: {file_path}")
                with open(file_path, 'r') as file:
                    self.source_text_input.setText(file.read())
        except Exception as e:
            logging.exception(f"Failed to load source file: {e}")

    def select_dest_file(self):
        """
        Prompt user to select a destination config file and load its content.
        """
        try:
            file_path = QtWidgets.QFileDialog.getOpenFileName(filter="(*.txt *.cfg)")[0]
            if file_path:
                logging.info(f"Destination file selected: {file_path}")
                with open(file_path, 'r') as file:
                    self.dest_text_input.setText(file.read())
        except Exception as e:
            logging.exception(f"Failed to load destination file: {e}")

    def run_comparison(self):
        """
        Disable compare button, start the RunCompare thread, and connect the finish signal.
        """
        try:
            self.compare_button.setEnabled(False)
            self.run_worker = RunEvent(self)
            self.run_worker.start()
            self.run_worker.finished.connect(self.run_comparison_finished)
        except Exception as e:
            logging.exception(f"Failed to start comparison thread: {e}")
            self.compare_button.setEnabled(True)

    def run_comparison_finished(self):
        """
        Re-enable the compare button and notify the user when the comparison is complete.
        """
        self.compare_button.setEnabled(True)
        QtWidgets.QMessageBox.information(self, "Info", "Comparison completed successfully.")

    def open_path(self, path: str):
        """
        Open a file or directory using the system's default handler.

        Args:
            path (str): File or directory path to open.
        """
        try:
            if path and os.path.exists(path):
                logging.info(f"Opening path: {path}")
                QtGui.QDesktopServices.openUrl(QtCore.QUrl.fromLocalFile(path))
            else:
                logging.error(f"Invalid or non-existent path: {path}")
        except Exception as e:
            logging.exception(f"Failed to open path: {e}")