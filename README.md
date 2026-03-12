# ChimeraX-SpaceMouse

A ChimeraX plugin that enables 3DConnexion SpaceMouse 6DoF input for manipulating the 3D view and models.
Useful in combination with spatial reality displays or while recording movies.

> [!NOTE]
> This is an experimental plugin. There is built-in support for 3D Connexion hardware in ChimeraX via the [command](https://www.cgl.ucsf.edu/chimerax/docs/user/commands/device.html#snav) `device snav on`. ChimeraX-SpaceMouse uses a different backend library that is not delivered with the plugin, but can be installed independently.


## Features

- **6 Degrees of Freedom**: Natural translation (X/Y/Z) and rotation (roll/pitch/yaw) control
- **View manipulation**: Pan, rotate, and zoom the camera using the SpaceMouse
- **Model manipulation**: Translate and rotate selected models
- **Custom button bindings**: Map SpaceMouse buttons to ChimeraX commands
- **Configurable sensitivity** and dead zones for all 6 axes
- **Axis inversion**: Independently invert any of the 6 axes

## Supported Devices

Via the [pyspacemouse](https://github.com/JakubAndrysek/pyspacemouse) library:

- SpaceNavigator
- SpaceMouse Compact
- SpaceMouse Pro / Pro Wireless
- SpaceMouse Wireless
- SpaceMouse Enterprise
- SpaceExplorer
- SpacePilot / SpacePilot Pro
- Universal Receiver

## Requirements

- ChimeraX 1.9 or later
- HIDAPI library (see installation instructions below)
- A 3DConnexion SpaceMouse device

## Installation

### 1. Install HIDAPI

The plugin requires the HIDAPI C library to communicate with SpaceMouse devices.

**macOS (Homebrew):**
```bash
brew install hidapi
```

The plugin will automatically find the library in Homebrew's lib directory.
If you encounter issues, you can manually set the library path:
```bash
# For Apple Silicon (M1/M2/M3)
export DYLD_LIBRARY_PATH=/opt/homebrew/lib:$DYLD_LIBRARY_PATH

# For Intel Macs
export DYLD_LIBRARY_PATH=/usr/local/lib:$DYLD_LIBRARY_PATH
```

**Linux (Debian/Ubuntu):**
```bash
sudo apt install libhidapi-dev
```

You'll also need udev rules for device access (see Troubleshooting section).

**Windows:**
1. Download from [HIDAPI releases](https://github.com/libusb/hidapi/releases)
2. Extract and copy `hidapi.dll` to a folder
3. Add that folder to your system PATH

### 2. Install the Plugin

**From wheel (recommended):**

Download the latest `.whl` file from the [releases page](https://github.com/uermel/chimerax-spacemouse/releases), then in ChimeraX:
```
toolshed install /Users/username/Downloads/ChimeraX_SpaceMouse-0.1.0-py3-none-any.whl
```

**From source (development):**
```bash
cd /path/to/chimerax-spacemouse
.launch/prelaunch.sh .
```

Or manually in ChimeraX:
```
devel build /path/to/chimerax-spacemouse
devel install /path/to/chimerax-spacemouse
```

## Usage

### Starting the SpaceMouse Tool

In ChimeraX, run:
```
spacemouse
```

This opens the SpaceMouse tool panel and begins listening for device input.

### Control Mapping

The SpaceMouse provides natural 6DoF control:

| SpaceMouse Input | View Mode | Model Mode |
|------------------|-----------|------------|
| Push left/right (X) | Pan horizontally | Translate X |
| Push forward/back (Y) | Pan vertically | Translate Y |
| Push up/down (Z) | Zoom in/out | Translate Z |
| Twist (Roll) | Roll camera | Roll model |
| Tilt cap forward/back (Pitch) | Tilt view up/down | Pitch model |
| Rotate base left/right (Yaw) | Spin view left/right | Yaw model |
| Left Button | Toggle mode | Toggle mode |

### Commands

| Command | Description |
|---------|-------------|
| `spacemouse` | Open the SpaceMouse tool |
| `spacemouse start` | Start SpaceMouse polling |
| `spacemouse stop` | Stop SpaceMouse polling |
| `spacemouse mode view` | Switch to view control mode |
| `spacemouse mode model` | Switch to model control mode |
| `spacemouse sensitivity translation <value>` | Set translation/pan sensitivity (0.1-5.0) |
| `spacemouse sensitivity rotation <value>` | Set rotation sensitivity (0.1-5.0) |
| `spacemouse sensitivity zoom <value>` | Set zoom/Z-translate sensitivity (0.1-5.0) |
| `spacemouse deadzone <value>` | Set dead zone (0.0-0.5) |
| `spacemouse invert <axis> <true\|false>` | Invert an axis (x/y/z/roll/pitch/yaw) |
| `spacemouse bind <button> <command>` | Bind button to ChimeraX command |
| `spacemouse unbind <button>` | Remove button binding |
| `spacemouse settings` | Open settings dialog |

### Button Names for Binding

Common button names (varies by device):

- `LEFT`, `RIGHT` (most devices)
- `TOP`, `BOTTOM`, `FRONT`, `REAR`
- `FIT`, `MENU`, `ALT`, `SPIN`
- `PLUS`, `MINUS`, `ESC`, `CTRL`, `LOCK`

### Example: Bind Buttons to Commands

```
spacemouse bind RIGHT "view initial"
spacemouse bind TOP "surface"
spacemouse bind BOTTOM "hide surfaces"
```

## Configuration

Settings are stored in `~/.chimerax/spacemouse/config.json` and include:

- **Dead zone**: Percentage of input to ignore (default: 5% - SpaceMouse is more precise)
- **Translation sensitivity**: Speed multiplier for pan/translate actions (default: 1.0)
- **Rotation sensitivity**: Speed multiplier for rotation actions (default: 1.0)
- **Zoom sensitivity**: Speed multiplier for zoom/Z-translate actions (default: 1.0)
- **Axis inversion**: Independently flip any of the 6 axes
- **Mode toggle button**: Which button toggles between View and Model modes
- **Button mappings**: Custom button-to-command mappings

Use `spacemouse settings` to open the configuration dialog.

## Troubleshooting

### "HID API is probably not installed" error

This means the hidapi C library cannot be found.

**macOS:**
```bash
# Install hidapi
brew install hidapi

# Verify installation
brew info hidapi
```

The plugin automatically searches common Homebrew locations. If it still fails:
```bash
# Check where hidapi is installed
ls /opt/homebrew/lib/libhidapi.dylib  # Apple Silicon
ls /usr/local/lib/libhidapi.dylib     # Intel
```

**Linux:**
```bash
sudo apt install libhidapi-dev
```

**Windows:**
Download `hidapi.dll` from [HIDAPI releases](https://github.com/libusb/hidapi/releases)
and add its location to your PATH.

### Device not detected

1. Ensure the SpaceMouse is connected before starting ChimeraX
2. Check that HIDAPI is properly installed (see above)
3. **On Linux**, you need udev rules for HID access:
   ```bash
   # Create udev rule
   echo 'KERNEL=="hidraw*", SUBSYSTEM=="hidraw", MODE="0666"' | sudo tee /etc/udev/rules.d/99-hidraw.rules

   # For specific 3Dconnexion devices (more secure):
   echo 'KERNEL=="hidraw*", ATTRS{idVendor}=="256f", MODE="0666"' | sudo tee /etc/udev/rules.d/99-spacemouse.rules
   echo 'KERNEL=="hidraw*", ATTRS{idVendor}=="046d", MODE="0666"' | sudo tee -a /etc/udev/rules.d/99-spacemouse.rules

   # Reload rules
   sudo udevadm control --reload-rules
   sudo udevadm trigger
   ```
4. Try disconnecting and reconnecting the device
5. On macOS, you do NOT need the 3Dconnexion drivers installed

### Movements feel inverted

Invert individual axes as needed:
```
spacemouse invert y true    # Invert Y translation
spacemouse invert pitch true # Invert pitch rotation
```

### Movements are too fast/slow

Adjust sensitivity:
```
spacemouse sensitivity translation 0.5   # Slower panning/translation
spacemouse sensitivity rotation 2.0      # Faster rotation
spacemouse sensitivity zoom 1.5          # Faster zoom/Z-movement
```

### Minor input when device is at rest

Increase the dead zone:
```
spacemouse deadzone 0.1   # 10% dead zone
```

## Development

### Building from Source

```bash
# Clone the repository
git clone https://github.com/uermel/chimerax-spacemouse.git
cd chimerax-spacemouse

# Build and install
.launch/prelaunch.sh .
```

## License

MIT License
