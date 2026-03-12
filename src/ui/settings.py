# vim: set expandtab shiftwidth=4 softtabstop=4:

"""Settings dialog for SpaceMouse configuration."""

from Qt.QtCore import Qt
from Qt.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QSlider,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
)


class SettingsDialog(QDialog):
    """Configuration dialog for SpaceMouse settings."""

    def __init__(self, session, config, parent=None):
        """Initialize the settings dialog.

        Parameters
        ----------
        session : chimerax.core.session.Session
            The ChimeraX session.
        config : SpaceMouseConfig
            The SpaceMouse configuration.
        parent : QWidget, optional
            The parent widget.
        """
        super().__init__(parent)
        self.session = session
        self.config = config

        self.setWindowTitle("SpaceMouse Settings")
        self.setMinimumWidth(500)

        self._build_ui()
        self._load_values()

    def _build_ui(self):
        """Build the dialog UI."""
        layout = QVBoxLayout(self)

        # Sensitivity Group
        sensitivity_group = QGroupBox("Sensitivity")
        sens_layout = QFormLayout()

        # Dead zone slider
        self.dead_zone_slider = QSlider(Qt.Horizontal)
        self.dead_zone_slider.setRange(0, 50)  # 0-50%
        self.dead_zone_slider.valueChanged.connect(self._on_dead_zone_changed)
        self.dead_zone_label = QLabel("5%")
        self.dead_zone_label.setMinimumWidth(40)
        dz_layout = QHBoxLayout()
        dz_layout.addWidget(self.dead_zone_slider)
        dz_layout.addWidget(self.dead_zone_label)
        sens_layout.addRow("Dead Zone:", dz_layout)

        # Translation sensitivity
        self.trans_sens_slider = QSlider(Qt.Horizontal)
        self.trans_sens_slider.setRange(10, 500)  # 0.1-5.0
        self.trans_sens_slider.valueChanged.connect(self._on_trans_sens_changed)
        self.trans_sens_label = QLabel("1.0")
        self.trans_sens_label.setMinimumWidth(40)
        trans_layout = QHBoxLayout()
        trans_layout.addWidget(self.trans_sens_slider)
        trans_layout.addWidget(self.trans_sens_label)
        sens_layout.addRow("Translation:", trans_layout)

        # Rotation sensitivity
        self.rot_sens_slider = QSlider(Qt.Horizontal)
        self.rot_sens_slider.setRange(10, 500)
        self.rot_sens_slider.valueChanged.connect(self._on_rot_sens_changed)
        self.rot_sens_label = QLabel("1.0")
        self.rot_sens_label.setMinimumWidth(40)
        rot_layout = QHBoxLayout()
        rot_layout.addWidget(self.rot_sens_slider)
        rot_layout.addWidget(self.rot_sens_label)
        sens_layout.addRow("Rotation:", rot_layout)

        # Zoom sensitivity
        self.zoom_sens_slider = QSlider(Qt.Horizontal)
        self.zoom_sens_slider.setRange(10, 500)
        self.zoom_sens_slider.valueChanged.connect(self._on_zoom_sens_changed)
        self.zoom_sens_label = QLabel("1.0")
        self.zoom_sens_label.setMinimumWidth(40)
        zoom_layout = QHBoxLayout()
        zoom_layout.addWidget(self.zoom_sens_slider)
        zoom_layout.addWidget(self.zoom_sens_label)
        sens_layout.addRow("Zoom:", zoom_layout)

        sensitivity_group.setLayout(sens_layout)
        layout.addWidget(sensitivity_group)

        # Axis Inversion Group
        invert_group = QGroupBox("Axis Inversion")
        invert_layout = QHBoxLayout()

        # Translation axes
        trans_invert_layout = QVBoxLayout()
        trans_invert_layout.addWidget(QLabel("Translation:"))
        self.invert_x_check = QCheckBox("Invert X")
        self.invert_y_check = QCheckBox("Invert Y")
        self.invert_z_check = QCheckBox("Invert Z")
        trans_invert_layout.addWidget(self.invert_x_check)
        trans_invert_layout.addWidget(self.invert_y_check)
        trans_invert_layout.addWidget(self.invert_z_check)
        invert_layout.addLayout(trans_invert_layout)

        # Rotation axes
        rot_invert_layout = QVBoxLayout()
        rot_invert_layout.addWidget(QLabel("Rotation:"))
        self.invert_roll_check = QCheckBox("Invert Roll")
        self.invert_pitch_check = QCheckBox("Invert Pitch")
        self.invert_yaw_check = QCheckBox("Invert Yaw")
        rot_invert_layout.addWidget(self.invert_roll_check)
        rot_invert_layout.addWidget(self.invert_pitch_check)
        rot_invert_layout.addWidget(self.invert_yaw_check)
        invert_layout.addLayout(rot_invert_layout)

        invert_group.setLayout(invert_layout)
        layout.addWidget(invert_group)

        # Mode Toggle Button Group
        mode_group = QGroupBox("Mode Toggle")
        mode_layout = QFormLayout()

        self.mode_toggle_combo = QComboBox()
        self.mode_toggle_combo.addItems([
            "LEFT (Button 0)",
            "RIGHT (Button 1)",
            "TOP (Button 2)",
            "BOTTOM (Button 3)",
            "None (Disabled)",
        ])
        mode_layout.addRow("Toggle Button:", self.mode_toggle_combo)

        mode_group.setLayout(mode_layout)
        layout.addWidget(mode_group)

        # Button Mappings Group
        mapping_group = QGroupBox("Button Mappings")
        mapping_layout = QVBoxLayout()

        self.mapping_table = QTableWidget()
        self.mapping_table.setColumnCount(2)
        self.mapping_table.setHorizontalHeaderLabels(["Button", "Command"])
        self.mapping_table.horizontalHeader().setStretchLastSection(True)
        self.mapping_table.setMinimumHeight(120)
        mapping_layout.addWidget(self.mapping_table)

        # Add/Remove buttons
        btn_layout = QHBoxLayout()
        self.add_mapping_btn = QPushButton("Add Mapping")
        self.add_mapping_btn.clicked.connect(self._add_mapping)
        self.remove_mapping_btn = QPushButton("Remove")
        self.remove_mapping_btn.clicked.connect(self._remove_mapping)
        btn_layout.addWidget(self.add_mapping_btn)
        btn_layout.addWidget(self.remove_mapping_btn)
        btn_layout.addStretch()
        mapping_layout.addLayout(btn_layout)

        mapping_group.setLayout(mapping_layout)
        layout.addWidget(mapping_group)

        # Dialog buttons
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel | QDialogButtonBox.Apply)
        buttons.accepted.connect(self._save_and_close)
        buttons.rejected.connect(self.reject)
        apply_btn = buttons.button(QDialogButtonBox.Apply)
        if apply_btn:
            apply_btn.clicked.connect(self._apply)
        layout.addWidget(buttons)

    def _load_values(self):
        """Load current config values into UI."""
        self.dead_zone_slider.setValue(int(self.config.dead_zone * 100))
        self.trans_sens_slider.setValue(int(self.config.translation_sensitivity * 100))
        self.rot_sens_slider.setValue(int(self.config.rotation_sensitivity * 100))
        self.zoom_sens_slider.setValue(int(self.config.zoom_sensitivity * 100))

        # Axis inversion
        self.invert_x_check.setChecked(self.config.get_invert("x"))
        self.invert_y_check.setChecked(self.config.get_invert("y"))
        self.invert_z_check.setChecked(self.config.get_invert("z"))
        self.invert_roll_check.setChecked(self.config.get_invert("roll"))
        self.invert_pitch_check.setChecked(self.config.get_invert("pitch"))
        self.invert_yaw_check.setChecked(self.config.get_invert("yaw"))

        # Mode toggle button
        toggle_btn = self.config.mode_toggle_button
        if toggle_btn >= 0 and toggle_btn < 4:
            self.mode_toggle_combo.setCurrentIndex(toggle_btn)
        else:
            self.mode_toggle_combo.setCurrentIndex(4)  # None/Disabled

        # Load button mappings
        self._refresh_mappings_table()

    def _refresh_mappings_table(self):
        """Refresh the button mappings table."""
        mappings = self.config._config.get("button_mappings", {})
        self.mapping_table.setRowCount(len(mappings))
        for row, (button, command) in enumerate(mappings.items()):
            self.mapping_table.setItem(row, 0, QTableWidgetItem(button))
            self.mapping_table.setItem(row, 1, QTableWidgetItem(command))

    def _on_dead_zone_changed(self, value):
        """Handle dead zone slider change."""
        self.dead_zone_label.setText(f"{value}%")

    def _on_trans_sens_changed(self, value):
        """Handle translation sensitivity slider change."""
        self.trans_sens_label.setText(f"{value / 100:.1f}")

    def _on_rot_sens_changed(self, value):
        """Handle rotation sensitivity slider change."""
        self.rot_sens_label.setText(f"{value / 100:.1f}")

    def _on_zoom_sens_changed(self, value):
        """Handle zoom sensitivity slider change."""
        self.zoom_sens_label.setText(f"{value / 100:.1f}")

    def _add_mapping(self):
        """Add a new button mapping row."""
        row = self.mapping_table.rowCount()
        self.mapping_table.insertRow(row)

        # Button selector combo
        button_combo = QComboBox()
        button_combo.addItems([
            "LEFT",
            "RIGHT",
            "TOP",
            "BOTTOM",
            "FRONT",
            "REAR",
            "FIT",
            "MENU",
            "ALT",
            "SPIN",
            "PLUS",
            "MINUS",
            "ESC",
            "CTRL",
            "LOCK",
        ])
        self.mapping_table.setCellWidget(row, 0, button_combo)

        # Command input
        command_edit = QLineEdit()
        command_edit.setPlaceholderText("ChimeraX command...")
        self.mapping_table.setCellWidget(row, 1, command_edit)

    def _remove_mapping(self):
        """Remove selected mapping row."""
        current_row = self.mapping_table.currentRow()
        if current_row >= 0:
            self.mapping_table.removeRow(current_row)

    def _apply(self):
        """Apply current settings to config."""
        self.config.dead_zone = self.dead_zone_slider.value() / 100
        self.config.translation_sensitivity = self.trans_sens_slider.value() / 100
        self.config.rotation_sensitivity = self.rot_sens_slider.value() / 100
        self.config.zoom_sensitivity = self.zoom_sens_slider.value() / 100

        # Axis inversion
        self.config.set_invert("x", self.invert_x_check.isChecked())
        self.config.set_invert("y", self.invert_y_check.isChecked())
        self.config.set_invert("z", self.invert_z_check.isChecked())
        self.config.set_invert("roll", self.invert_roll_check.isChecked())
        self.config.set_invert("pitch", self.invert_pitch_check.isChecked())
        self.config.set_invert("yaw", self.invert_yaw_check.isChecked())

        # Mode toggle button
        toggle_idx = self.mode_toggle_combo.currentIndex()
        if toggle_idx < 4:
            self.config.mode_toggle_button = toggle_idx
        else:
            self.config.mode_toggle_button = -1  # Disabled

        # Update button mappings
        self.config._config["button_mappings"].clear()
        for row in range(self.mapping_table.rowCount()):
            # Get button name
            button_widget = self.mapping_table.cellWidget(row, 0)
            if button_widget and isinstance(button_widget, QComboBox):
                button = button_widget.currentText()
            else:
                item = self.mapping_table.item(row, 0)
                button = item.text() if item else None

            # Get command
            cmd_widget = self.mapping_table.cellWidget(row, 1)
            if cmd_widget and isinstance(cmd_widget, QLineEdit):
                command = cmd_widget.text()
            else:
                cmd_item = self.mapping_table.item(row, 1)
                command = cmd_item.text() if cmd_item else ""

            if button and command:
                self.config._config["button_mappings"][button] = command

        self.config.save()

    def _save_and_close(self):
        """Apply settings and close dialog."""
        self._apply()
        self.accept()
