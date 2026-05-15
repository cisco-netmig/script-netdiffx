import logging
logger = logging.getLogger(__name__)

import os
import json
from datetime import datetime
from PyQt5 import QtCore

from .helpers import ConfigDiffer


class RunEvent(QtCore.QThread):
    """
    A QThread that compares source and destination configuration texts and
    writes the comparison to an Excel workbook using XLBW.
    """

    def __init__(self, form):
        """
        Initialize the thread with the UI form instance.

        Args:
            form (QWidget): The calling form containing input fields and output directory.
        """
        super().__init__()
        self.form = form
        self.fonts = {}
        self.source_text = ""
        self.dest_text = ""
        self.workbook = None
        self.worksheet = None
        self.differ = None

    def run(self):
        """
        Entry point for the thread. Extracts input text, performs config comparison,
        and writes formatted results to an Excel file.
        """
        try:
            os.makedirs(self.form.output_dir, exist_ok=True)

            self.source_text = self.form.source_text_input.toPlainText()
            self.dest_text = self.form.dest_text_input.toPlainText()

            timestamp = datetime.now().strftime('%Y-%m-%d_%H.%M')
            filename = f"{os.path.basename(os.path.dirname(__file__)).title()}_{timestamp}.xlsx"
            self.form.output_report = os.path.join(self.form.output_dir, filename)

            logger.info("Starting configuration comparison...")

            # First run: write full comparison
            self.differ = ConfigDiffer(self.source_text, self.dest_text)
            from netcore import XLBW  # Imported late to reduce dependency scope

            self.workbook = XLBW(self.form.output_report)
            self.worksheet = self.workbook.add_worksheet("Compare")

            self.load_fonts()
            self.write_input()

            self.differ.write(
                self.worksheet, 'Compare',
                self.fonts['header'], self.fonts['body'],
                self.fonts['bad'], self.fonts['badb'], col_idx=2
            )

            # Second run: write only differences
            self.differ = ConfigDiffer(self.source_text, self.dest_text, diff_only=True)
            self.differ.write(
                self.worksheet, 'Diff',
                self.fonts['header'], self.fonts['body'],
                self.fonts['bad'], self.fonts['badb'], col_idx=3
            )

            if hasattr(logger, 'savings'):
                logger.savings(len(self.differ.diff))

            logger.info("Saving report to Excel.")
            self.workbook.close()
            logger.info("Report generation finished.")

        except Exception as e:
            logger.exception(f"Error during comparison: {e}")

    def write_input(self):
        """
        Writes the original source and destination input lines to the Excel workbook.
        """
        try:
            # Write source input
            source_lines = self.source_text.splitlines()
            source_format = {i: [line, self.fonts['body']] for i, line in enumerate(source_lines)}
            self.differ.write(
                self.worksheet, 'Source',
                self.fonts['header'], self.fonts['body'],
                self.fonts['bad'], self.fonts['badb'],
                format_strings=source_format, col_idx=0
            )

            # Write destination input
            dest_lines = self.dest_text.splitlines()
            dest_format = {i: [line, self.fonts['body']] for i, line in enumerate(dest_lines)}
            self.differ.write(
                self.worksheet, 'Destination',
                self.fonts['header'], self.fonts['body'],
                self.fonts['bad'], self.fonts['badb'],
                format_strings=dest_format, col_idx=1
            )

        except Exception as e:
            logger.exception(f"Error while writing input sections: {e}")

    def load_fonts(self):
        """
        Loads font styles from a JSON file and registers them in the workbook.
        """
        try:
            font_path = os.path.join(os.path.dirname(__file__), 'assets', 'fonts.json')
            with open(font_path, 'r') as f:
                font_styles = json.load(f)

            for style, properties in font_styles.items():
                self.fonts[style] = self.workbook.add_format(properties)

        except Exception as e:
            logger.exception(f"Failed to load fonts: {e}")
