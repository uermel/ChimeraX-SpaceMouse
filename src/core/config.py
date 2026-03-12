# vim: set expandtab shiftwidth=4 softtabstop=4:

import json
import os
from enum import IntEnum


class ControlMode(IntEnum):
    """Control mode enum."""

    VIEW = 1
    MODEL = 2


class SpaceMouseConfig:
    """Manages SpaceMouse configuration settings."""

    DEFAULT_CONFIG = {
        "dead_zone": 0.05,  # 5% dead zone (SpaceMouse is more precise than gamepad)
        "translation_sensitivity": 1.0,  # For X/Y pan
        "rotation_sensitivity": 1.0,  # For roll/pitch/yaw
        "zoom_sensitivity": 1.0,  # For Z-axis zoom
        # Axis inversion flags (6DoF)
        "invert_x": False,
        "invert_y": False,
        "invert_z": False,
        "invert_roll": False,
        "invert_pitch": False,
        "invert_yaw": False,
        # Mode toggle button (button index)
        "mode_toggle_button": 0,  # LEFT button on most SpaceMice
        # Button command mappings
        "button_mappings": {
            # Default button mappings: button_name -> ChimeraX command
            # Button 0 (LEFT) is reserved for mode toggle by default
            # "RIGHT": "view initial",
        },
    }

    # Common button names for SpaceMouse devices
    # These vary by device but cover most common cases
    BUTTON_NAMES = {
        0: "LEFT",
        1: "RIGHT",
        2: "TOP",
        3: "BOTTOM",
        4: "FRONT",
        5: "REAR",
        6: "FIT",
        7: "MENU",
        8: "ALT",
        9: "SPIN",
        10: "PLUS",
        11: "MINUS",
        12: "ESC",
        13: "CTRL",
        14: "LOCK",
    }

    # Axis names for inversion
    AXIS_NAMES = ("x", "y", "z", "roll", "pitch", "yaw")

    def __init__(self):
        """Initialize the configuration."""
        self._config = dict(self.DEFAULT_CONFIG)
        self._config["button_mappings"] = dict(self.DEFAULT_CONFIG["button_mappings"])
        self._config_path = self._get_config_path()
        self.load()

    def _get_config_path(self):
        """Get path to config file in user's ChimeraX config dir.

        Returns
        -------
        str
            The path to the config file.
        """
        config_dir = os.path.expanduser("~/.chimerax/spacemouse")
        os.makedirs(config_dir, exist_ok=True)
        return os.path.join(config_dir, "config.json")

    def load(self):
        """Load configuration from file."""
        if os.path.exists(self._config_path):
            try:
                with open(self._config_path) as f:
                    loaded = json.load(f)
                    self._config.update(loaded)
            except (json.JSONDecodeError, OSError):
                pass  # Use defaults on error

    def save(self):
        """Save configuration to file."""
        try:
            with open(self._config_path, "w") as f:
                json.dump(self._config, f, indent=2)
        except OSError:
            pass  # Silently fail if can't save

    @property
    def dead_zone(self):
        """Get the dead zone value.

        Returns
        -------
        float
            The dead zone (0.0 to 0.5).
        """
        return self._config["dead_zone"]

    @dead_zone.setter
    def dead_zone(self, value):
        """Set the dead zone value.

        Parameters
        ----------
        value : float
            The dead zone value (clamped to 0.0-0.5).
        """
        self._config["dead_zone"] = max(0.0, min(0.5, value))

    @property
    def translation_sensitivity(self):
        """Get the translation sensitivity.

        Returns
        -------
        float
            The translation sensitivity (0.1 to 5.0).
        """
        return self._config.get("translation_sensitivity", 1.0)

    @translation_sensitivity.setter
    def translation_sensitivity(self, value):
        """Set the translation sensitivity.

        Parameters
        ----------
        value : float
            The sensitivity value (clamped to 0.1-5.0).
        """
        self._config["translation_sensitivity"] = max(0.1, min(5.0, value))

    @property
    def rotation_sensitivity(self):
        """Get the rotation sensitivity.

        Returns
        -------
        float
            The rotation sensitivity (0.1 to 5.0).
        """
        return self._config.get("rotation_sensitivity", 1.0)

    @rotation_sensitivity.setter
    def rotation_sensitivity(self, value):
        """Set the rotation sensitivity.

        Parameters
        ----------
        value : float
            The sensitivity value (clamped to 0.1-5.0).
        """
        self._config["rotation_sensitivity"] = max(0.1, min(5.0, value))

    @property
    def zoom_sensitivity(self):
        """Get the zoom sensitivity.

        Returns
        -------
        float
            The zoom sensitivity (0.1 to 5.0).
        """
        return self._config.get("zoom_sensitivity", 1.0)

    @zoom_sensitivity.setter
    def zoom_sensitivity(self, value):
        """Set the zoom sensitivity.

        Parameters
        ----------
        value : float
            The sensitivity value (clamped to 0.1-5.0).
        """
        self._config["zoom_sensitivity"] = max(0.1, min(5.0, value))

    @property
    def mode_toggle_button(self):
        """Get the mode toggle button index.

        Returns
        -------
        int
            The button index used for mode toggle.
        """
        return self._config.get("mode_toggle_button", 0)

    @mode_toggle_button.setter
    def mode_toggle_button(self, value):
        """Set the mode toggle button index.

        Parameters
        ----------
        value : int
            The button index (0 or greater).
        """
        self._config["mode_toggle_button"] = max(0, int(value))

    def get_invert(self, axis):
        """Get whether an axis is inverted.

        Parameters
        ----------
        axis : str
            The axis name ("x", "y", "z", "roll", "pitch", or "yaw").

        Returns
        -------
        bool
            True if the axis is inverted.
        """
        return self._config.get(f"invert_{axis}", False)

    def set_invert(self, axis, value):
        """Set whether an axis is inverted.

        Parameters
        ----------
        axis : str
            The axis name ("x", "y", "z", "roll", "pitch", or "yaw").
        value : bool
            True to invert the axis.
        """
        if axis in self.AXIS_NAMES:
            self._config[f"invert_{axis}"] = bool(value)

    def button_to_name(self, button):
        """Convert button index to string name.

        Parameters
        ----------
        button : int
            The button index.

        Returns
        -------
        str
            The button name.
        """
        return self.BUTTON_NAMES.get(button, f"BUTTON_{button}")

    def name_to_button(self, name):
        """Convert button name to index.

        Parameters
        ----------
        name : str
            The button name.

        Returns
        -------
        int or None
            The button index, or None if not found.
        """
        for idx, btn_name in self.BUTTON_NAMES.items():
            if btn_name == name.upper():
                return idx
        # Try parsing as BUTTON_N format
        if name.upper().startswith("BUTTON_"):
            try:
                return int(name[7:])
            except ValueError:
                pass
        return None

    def get_button_command(self, button):
        """Get command mapped to button, or None.

        Parameters
        ----------
        button : int or str
            The button index or name.

        Returns
        -------
        str or None
            The ChimeraX command mapped to the button.
        """
        if isinstance(button, int):
            button_name = self.button_to_name(button)
        else:
            button_name = button.upper()
        return self._config["button_mappings"].get(button_name)

    def set_button_command(self, button_name, command):
        """Map a button to a ChimeraX command.

        Parameters
        ----------
        button_name : str
            The button name (e.g., "LEFT", "RIGHT").
        command : str or None
            The ChimeraX command to execute, or None to remove mapping.
        """
        if command:
            self._config["button_mappings"][button_name.upper()] = command
        elif button_name.upper() in self._config["button_mappings"]:
            del self._config["button_mappings"][button_name.upper()]

    def to_dict(self):
        """Export config for session saving.

        Returns
        -------
        dict
            The configuration dictionary.
        """
        return dict(self._config)

    def from_dict(self, data):
        """Import config from session restore.

        Parameters
        ----------
        data : dict
            The configuration dictionary.
        """
        self._config.update(data)
