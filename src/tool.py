# vim: set expandtab shiftwidth=4 softtabstop=4:

from chimerax.core.tools import ToolInstance
from chimerax.ui import MainToolWindow
from Qt.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)


class SpaceMouseTool(ToolInstance):
    """ChimeraX tool for SpaceMouse 6DoF controller support."""

    # Does this instance persist when session closes
    SESSION_ENDURING = False
    # We do save/restore in sessions
    SESSION_SAVE = True
    # Help page
    help = "help:user/tools/spacemouse.html"

    def __init__(self, session, tool_name):
        """Initialize the SpaceMouse tool.

        Parameters
        ----------
        session : chimerax.core.session.Session
            The ChimeraX session.
        tool_name : str
            The name of the tool.
        """
        super().__init__(session, tool_name)

        self.display_name = "SpaceMouse Controller"

        # Store self in session for access from commands
        session.spacemouse = self

        # Create the SpaceMouse manager
        from .core.spacemouse import SpaceMouseManager

        self.spacemouse_manager = SpaceMouseManager(session)
        self.spacemouse_manager.on_status_change = self._update_status

        # Create tool window
        self.tool_window = MainToolWindow(self, close_destroys=True)
        self._build_ui()

        # Register for frame updates
        self._frame_handler = session.triggers.add_handler("new frame", self._on_frame)

        # Start the SpaceMouse manager
        try:
            self.spacemouse_manager.start()
            self._update_status()
        except Exception as e:
            session.logger.warning(f"Failed to initialize SpaceMouse: {e}")

    def _build_ui(self):
        """Build the minimal status UI."""
        tw = self.tool_window

        layout = QVBoxLayout()

        # Status section
        status_layout = QHBoxLayout()
        self._status_label = QLabel("Status: Not connected")
        status_layout.addWidget(self._status_label)
        layout.addLayout(status_layout)

        # Mode section
        mode_layout = QHBoxLayout()
        mode_layout.addWidget(QLabel("Mode:"))
        self._mode_label = QLabel("View")
        mode_layout.addWidget(self._mode_label)
        mode_layout.addStretch()

        self._toggle_mode_btn = QPushButton("Toggle Mode")
        self._toggle_mode_btn.clicked.connect(self._toggle_mode)
        mode_layout.addWidget(self._toggle_mode_btn)
        layout.addLayout(mode_layout)

        # Settings button
        settings_layout = QHBoxLayout()
        settings_layout.addStretch()
        self._settings_btn = QPushButton("Settings...")
        self._settings_btn.clicked.connect(self._open_settings)
        settings_layout.addWidget(self._settings_btn)
        layout.addLayout(settings_layout)

        layout.addStretch()

        container = QWidget()
        container.setLayout(layout)
        tw.ui_area.setLayout(QVBoxLayout())
        tw.ui_area.layout().addWidget(container)
        tw.manage("right")

    def _on_frame(self, trigger_name, update_loop):
        """Called each frame to poll SpaceMouse and apply actions.

        Parameters
        ----------
        trigger_name : str
            The name of the trigger.
        update_loop : object
            The update loop object.
        """
        if self.spacemouse_manager:
            self.spacemouse_manager.update()

    def _update_status(self):
        """Update the status label with device info."""
        if not self.spacemouse_manager:
            self._status_label.setText("Status: Not initialized")
            return

        if self.spacemouse_manager.device is not None:
            device_name = self.spacemouse_manager.device_name or "SpaceMouse"
            self._status_label.setText(f"Status: {device_name}")
        else:
            self._status_label.setText("Status: No device connected")

        # Update mode label
        from .core.spacemouse import ControlMode

        if self.spacemouse_manager.mode == ControlMode.VIEW:
            self._mode_label.setText("View")
        else:
            self._mode_label.setText("Model")

    def _toggle_mode(self):
        """Toggle between view and model control modes."""
        if self.spacemouse_manager:
            self.spacemouse_manager.toggle_mode()
            self._update_status()

    def _open_settings(self):
        """Open the settings dialog."""
        from .ui.settings import SettingsDialog

        dialog = SettingsDialog(self.session, self.spacemouse_manager.config, self.tool_window.ui_area)
        if dialog.exec():
            self.session.logger.info("SpaceMouse settings saved")

    def delete(self):
        """Cleanup when tool is closed."""
        # Remove frame handler
        if hasattr(self, "_frame_handler") and self._frame_handler:
            self.session.triggers.remove_handler(self._frame_handler)
            self._frame_handler = None

        # Stop SpaceMouse manager
        if hasattr(self, "spacemouse_manager") and self.spacemouse_manager:
            self.spacemouse_manager.stop()
            self.spacemouse_manager = None

        # Remove from session
        if hasattr(self.session, "spacemouse"):
            del self.session.spacemouse

        super().delete()

    def take_snapshot(self, session, flags):
        """Save session state.

        Parameters
        ----------
        session : chimerax.core.session.Session
            The ChimeraX session.
        flags : int
            Snapshot flags.

        Returns
        -------
        dict
            The session state.
        """
        return {
            "version": 1,
            "config": self.spacemouse_manager.config.to_dict() if self.spacemouse_manager else {},
        }

    @classmethod
    def restore_snapshot(cls, session, data):
        """Restore from session.

        Parameters
        ----------
        session : chimerax.core.session.Session
            The ChimeraX session.
        data : dict
            The saved session state.

        Returns
        -------
        SpaceMouseTool
            The restored tool instance.
        """
        inst = cls(session, "SpaceMouse")
        if inst.spacemouse_manager and "config" in data:
            inst.spacemouse_manager.config.from_dict(data["config"])
        return inst
