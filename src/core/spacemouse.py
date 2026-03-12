# vim: set expandtab shiftwidth=4 softtabstop=4:

import contextlib
import os
import sys
from pathlib import Path

from .config import ControlMode, SpaceMouseConfig


def _setup_hidapi_library_path():
    """Configure the hidapi library path for the current platform.

    This must be called before importing pyspacemouse/easyhid.
    Returns a tuple of (success, error_message).
    """
    if sys.platform == "darwin":
        # macOS: hidapi installed via Homebrew
        # Check common Homebrew locations
        homebrew_paths = [
            Path("/opt/homebrew/lib"),  # Apple Silicon
            Path("/usr/local/lib"),  # Intel
        ]

        # Also check Cellar for specific versions
        cellar_paths = [
            Path("/opt/homebrew/Cellar/hidapi"),
            Path("/usr/local/Cellar/hidapi"),
        ]

        found_lib = None

        # First check direct lib paths
        for lib_path in homebrew_paths:
            hidapi_dylib = lib_path / "libhidapi.dylib"
            if hidapi_dylib.exists():
                found_lib = lib_path
                break

        # If not found, check Cellar versions
        if found_lib is None:
            for cellar_path in cellar_paths:
                if cellar_path.exists():
                    # Find the latest version
                    versions = sorted(cellar_path.iterdir(), reverse=True)
                    for version_dir in versions:
                        lib_dir = version_dir / "lib"
                        if (lib_dir / "libhidapi.dylib").exists():
                            found_lib = lib_dir
                            break
                    if found_lib:
                        break

        if found_lib:
            current_path = os.environ.get("DYLD_LIBRARY_PATH", "")
            if str(found_lib) not in current_path:
                os.environ["DYLD_LIBRARY_PATH"] = f"{found_lib}:{current_path}" if current_path else str(found_lib)
            return True, None
        else:
            return False, (
                "hidapi library not found. Please install it:\n"
                "  brew install hidapi\n\n"
                "If already installed, you may need to set DYLD_LIBRARY_PATH:\n"
                "  export DYLD_LIBRARY_PATH=/opt/homebrew/lib:$DYLD_LIBRARY_PATH"
            )

    elif sys.platform.startswith("linux"):
        # Linux: hidapi installed via package manager
        lib_paths = [
            Path("/usr/lib/x86_64-linux-gnu"),
            Path("/usr/lib/aarch64-linux-gnu"),
            Path("/usr/lib"),
            Path("/usr/local/lib"),
        ]

        found_lib = None
        for lib_path in lib_paths:
            # Check for libhidapi-hidraw.so or libhidapi-libusb.so
            if (lib_path / "libhidapi-hidraw.so").exists() or (lib_path / "libhidapi-libusb.so").exists():
                found_lib = lib_path
                break

        if found_lib:
            current_path = os.environ.get("LD_LIBRARY_PATH", "")
            if str(found_lib) not in current_path:
                os.environ["LD_LIBRARY_PATH"] = f"{found_lib}:{current_path}" if current_path else str(found_lib)
            return True, None
        else:
            return False, (
                "hidapi library not found. Please install it:\n"
                "  sudo apt-get install libhidapi-dev  # Debian/Ubuntu\n"
                "  sudo dnf install hidapi-devel       # Fedora\n\n"
                "You may also need udev rules for device access:\n"
                "  See README for details."
            )

    elif sys.platform == "win32":
        # Windows: hidapi.dll needs to be in PATH
        # Check if it's already loadable
        import ctypes.util

        if ctypes.util.find_library("hidapi"):
            return True, None
        else:
            return False, (
                "hidapi.dll not found. Please download from:\n"
                "  https://github.com/libusb/hidapi/releases\n\n"
                "Extract and add the folder containing hidapi.dll to your PATH."
            )

    # Unknown platform
    return True, None


class SpaceMouseManager:
    """Manages SpaceMouse device initialization and input polling."""

    def __init__(self, session):
        """Initialize the SpaceMouse manager.

        Parameters
        ----------
        session : chimerax.core.session.Session
            The ChimeraX session.
        """
        self.session = session
        self.device = None  # SpaceMouseDevice instance
        self.config = SpaceMouseConfig()
        self._running = False

        # Device info
        self.device_name = None

        # Current control mode
        self.mode = ControlMode.VIEW

        # Action handlers (lazy import to avoid circular imports)
        self._view_action = None
        self._model_action = None

        # Callback for status changes (device connect/disconnect)
        self.on_status_change = None

        # Previous button state for edge detection
        self._prev_buttons = {}

        # Frame throttling for model mode (reduces expensive model updates)
        self._model_frame_counter = 0
        self._model_update_interval = 3  # Apply model transforms every N frames

    @property
    def view_action(self):
        """Get the view action handler (lazy initialization).

        Returns
        -------
        ViewAction
            The view action handler.
        """
        if self._view_action is None:
            from .actions import ViewAction

            self._view_action = ViewAction(self.session, self.config)
        return self._view_action

    @property
    def model_action(self):
        """Get the model action handler (lazy initialization).

        Returns
        -------
        ModelAction
            The model action handler.
        """
        if self._model_action is None:
            from .actions import ModelAction

            self._model_action = ModelAction(self.session, self.config)
        return self._model_action

    def start(self):
        """Initialize and open SpaceMouse device."""
        if self._running and self.device is not None:
            return

        # Setup hidapi library path before importing pyspacemouse
        success, error_msg = _setup_hidapi_library_path()
        if not success:
            self.session.logger.warning(f"SpaceMouse: {error_msg}")
            self.device = None
            self.device_name = None
            self._running = False
            self._notify_status_change()
            return

        try:
            import pyspacemouse

            # Try to open a SpaceMouse device (auto-detect, non-blocking)
            self.device = pyspacemouse.open(nonblocking=True)
            self.device_name = self.device.name if hasattr(self.device, "name") else "SpaceMouse"
            self._running = True

            self.session.logger.info(f"SpaceMouse: Connected - {self.device_name}")
            self._notify_status_change()

        except RuntimeError as e:
            error_str = str(e)
            if "HID API" in error_str or "hidapi" in error_str.lower():
                # Provide platform-specific help
                _, help_msg = _setup_hidapi_library_path()
                if help_msg:
                    self.session.logger.warning(f"SpaceMouse: HID library error.\n{help_msg}")
                else:
                    self.session.logger.warning(f"SpaceMouse: {e}")
            elif "No connected" in error_str or "not found" in error_str.lower():
                self.session.logger.warning("SpaceMouse: No device found. Please ensure your SpaceMouse is connected.")
            else:
                self.session.logger.warning(f"SpaceMouse: {e}")
            self.device = None
            self.device_name = None
            self._running = False
            self._notify_status_change()

        except AttributeError as e:
            # This often happens when hidapi library isn't found
            _, help_msg = _setup_hidapi_library_path()
            if help_msg:
                self.session.logger.warning(f"SpaceMouse: HID library not properly loaded.\n{help_msg}")
            else:
                self.session.logger.warning(f"SpaceMouse: Library error - {e}")
            self.device = None
            self.device_name = None
            self._running = False
            self._notify_status_change()

        except Exception as e:
            self.session.logger.warning(f"SpaceMouse: Failed to initialize - {e}")
            self.device = None
            self.device_name = None
            self._running = False
            self._notify_status_change()

    def stop(self):
        """Cleanup and close SpaceMouse device."""
        self._running = False

        if self.device is not None:
            with contextlib.suppress(Exception):
                self.device.close()
            self.device = None
            self.device_name = None

        self.session.logger.info("SpaceMouse: Disconnected")
        self._notify_status_change()

    def update(self):
        """Poll SpaceMouse and process input. Called each frame."""
        if not self._running or self.device is None:
            return

        try:
            # Read device state (non-blocking)
            state = self.device.read()

            # Check if we got valid data (t >= 0 indicates valid reading)
            if state.t >= 0:
                # Handle button presses (always process for responsiveness)
                self._handle_buttons(state)

                # Process 6DoF input
                if self.mode == ControlMode.VIEW:
                    # View mode: apply every frame (camera updates are lightweight)
                    self._process_input(state)
                else:
                    # Model mode: throttle to reduce expensive model updates
                    self._model_frame_counter += 1
                    if self._model_frame_counter >= self._model_update_interval:
                        self._model_frame_counter = 0
                        self._process_input(state)

        except Exception as e:
            # Device may have been disconnected
            self.session.logger.warning(f"SpaceMouse: Read error - {e}")
            self._handle_disconnect()

    def _process_input(self, state):
        """Process 6DoF input and route to appropriate action handler.

        Parameters
        ----------
        state : SpaceMouseState
            The current device state.
        """
        # Extract axis values
        x = state.x
        y = state.y
        z = state.z
        roll = state.roll
        pitch = state.pitch
        yaw = state.yaw

        # Apply dead zone
        x = self._apply_dead_zone(x)
        y = self._apply_dead_zone(y)
        z = self._apply_dead_zone(z)
        roll = self._apply_dead_zone(roll)
        pitch = self._apply_dead_zone(pitch)
        yaw = self._apply_dead_zone(yaw)

        # Apply axis inversions from config
        if self.config.get_invert("x"):
            x = -x
        if self.config.get_invert("y"):
            y = -y
        if self.config.get_invert("z"):
            z = -z
        if self.config.get_invert("roll"):
            roll = -roll
        if self.config.get_invert("pitch"):
            pitch = -pitch
        if self.config.get_invert("yaw"):
            yaw = -yaw

        # Route to appropriate action
        if self.mode == ControlMode.VIEW:
            self.view_action.apply(x, y, z, roll, pitch, yaw)
        else:  # MODEL mode
            self.model_action.apply(x, y, z, roll, pitch, yaw)

    def _apply_dead_zone(self, value):
        """Apply dead zone to an axis value.

        Parameters
        ----------
        value : float
            The raw axis value (-1 to 1).

        Returns
        -------
        float
            The processed value with dead zone applied.
        """
        dead_zone = self.config.dead_zone
        if abs(value) < dead_zone:
            return 0.0

        # Scale the remaining range to maintain 0-1 response
        sign = 1 if value > 0 else -1
        return sign * (abs(value) - dead_zone) / (1.0 - dead_zone)

    def _handle_buttons(self, state):
        """Handle button state changes for mode toggle and custom commands.

        Parameters
        ----------
        state : SpaceMouseState
            The current device state.
        """
        buttons = state.buttons

        for idx, pressed in enumerate(buttons):
            prev_pressed = self._prev_buttons.get(idx, 0)

            # Detect button press (edge detection)
            if pressed and not prev_pressed:
                # Check for mode toggle button
                if idx == self.config.mode_toggle_button:
                    self.toggle_mode()
                else:
                    # Check for custom command mapping
                    command = self.config.get_button_command(idx)
                    if command:
                        self._run_command(command)

        # Store current state for next frame
        self._prev_buttons = dict(enumerate(buttons))

    def _run_command(self, command):
        """Execute a ChimeraX command.

        Parameters
        ----------
        command : str
            The ChimeraX command to execute.
        """
        from chimerax.core.commands import run

        try:
            run(self.session, command)
        except Exception as e:
            self.session.logger.warning(f"SpaceMouse: Command failed - {e}")

    def toggle_mode(self):
        """Toggle between VIEW and MODEL control modes."""
        if self.mode == ControlMode.VIEW:
            self.mode = ControlMode.MODEL
            self.session.logger.info("SpaceMouse: Mode set to MODEL")
        else:
            self.mode = ControlMode.VIEW
            self.session.logger.info("SpaceMouse: Mode set to VIEW")
        self._notify_status_change()

    def _handle_disconnect(self):
        """Handle device disconnection."""
        self._running = False
        if self.device is not None:
            with contextlib.suppress(Exception):
                self.device.close()
            self.device = None
            self.device_name = None
        self._notify_status_change()

    def _notify_status_change(self):
        """Notify listener of device status change."""
        if self.on_status_change is not None:
            import contextlib

            with contextlib.suppress(Exception):
                self.on_status_change()

    def get_button_name(self, index):
        """Get the name of a button by index.

        Parameters
        ----------
        index : int
            The button index.

        Returns
        -------
        str
            The button name.
        """
        # Try to get name from device info if available
        if self.device is not None and hasattr(self.device, "get_button_name"):
            try:
                return self.device.get_button_name(index)
            except Exception:
                pass
        # Fall back to config mapping
        return self.config.button_to_name(index)
