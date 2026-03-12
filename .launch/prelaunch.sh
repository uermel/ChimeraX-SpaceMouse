#!/bin/bash
# Development launch script for ChimeraX SpaceMouse plugin
# Usage: .launch/prelaunch.sh /path/to/chimerax-spacemouse

# Set ChimeraX path (adjust as needed)
CHIMERAX="/Applications/ChimeraX-1.11.1.app/Contents/bin/ChimeraX"

# Plugin directory (passed as argument or use current directory)
PLUGIN_DIR="${1:-$(pwd)}"

# Set HIDAPI library path for macOS (if installed via Homebrew)
if [[ "$OSTYPE" == "darwin"* ]]; then
    if [[ -d "/opt/homebrew/lib" ]]; then
        export DYLD_LIBRARY_PATH="/opt/homebrew/lib:$DYLD_LIBRARY_PATH"
    elif [[ -d "/usr/local/lib" ]]; then
        export DYLD_LIBRARY_PATH="/usr/local/lib:$DYLD_LIBRARY_PATH"
    fi
fi

# On Linux
if [[ "$OSTYPE" == "linux-gnu"* ]]; then
    export LD_LIBRARY_PATH="/usr/lib/x86_64-linux-gnu:/usr/lib:$LD_LIBRARY_PATH"
fi

echo "Building and installing ChimeraX SpaceMouse plugin..."
echo "Plugin directory: $PLUGIN_DIR"

# Clean, build, and install the plugin
$CHIMERAX --nogui --cmd "devel clean $PLUGIN_DIR; exit;"
$CHIMERAX --nogui --cmd "devel build $PLUGIN_DIR; exit;"
$CHIMERAX --nogui --cmd "devel install $PLUGIN_DIR; exit;"

echo "Done! Launch ChimeraX and use 'spacemouse' command to start."
