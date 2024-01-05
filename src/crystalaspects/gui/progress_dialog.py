from collections import namedtuple
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QLabel,
    QDialog,
    QDialogButtonBox,
    QHBoxLayout,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)
from crystalaspects.gui.circular_progress import PyCircularProgress

class CircularProgress(QDialog):
    def __init__(self, calc_type="Aspect Ratio"):
        super().__init__()

        # Initialise Window
        self.setWindowTitle(f"{calc_type} Calculation Progress")

        # Create the main layout for all your widgets
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignCenter)

        # Create a widget for the main layout
        self.circular_progress = PyCircularProgress(value=0)
        self.circular_progress.setFixedSize(400, 400)

        # # Create a label for displaying the options
        self.options_label = QLabel("Calculating...\nWith Selected Options: ")
        self.options_label.setAlignment(Qt.AlignCenter)
        # Add widgets to the layout with padding
        layout.addSpacing(50)
        layout.addWidget(self.options_label)
        layout.addSpacing(50)
        layout.addWidget(self.circular_progress)
        layout.addSpacing(50)

    def set_value(self, value):
        self.circular_progress.set_value(value)

    def update_options(self, options:namedtuple):
        # Format the options into a bullet-point style string
        options_text = "Calculating...\n With Selected Options:\n"
        options_text += f"• Aspect Ratios\n"
        options_text += f"  PCA/OBA: {'Enabled' if options.selected_ar else 'Disabled'}\n"
        options_text += f"  CDA:     {'Enabled' if options.selected_cda else 'Disabled'}\n"
        options_text += f"• Checked Directions: {', '.join(options.checked_directions) or 'None'}\n"
        options_text += f"• Selected Directions: {', '.join(options.selected_directions) or 'None'}\n"
        options_text += f"• Plotting: {'Enabled' if options.plotting else 'Disabled'}"

        self.options_label.setText(options_text)