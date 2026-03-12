# vim: set expandtab shiftwidth=4 softtabstop=4:

from chimerax.core.toolshed import BundleAPI


class _SpaceMouseAPI(BundleAPI):
    """ChimeraX bundle API for the SpaceMouse plugin."""

    api_version = 1

    @staticmethod
    def start_tool(session, bi, ti):
        """Start the SpaceMouse tool."""
        if ti.name == "SpaceMouse":
            from .tool import SpaceMouseTool

            return SpaceMouseTool(session, ti.name)

    @staticmethod
    def register_command(bi, ci, logger):
        """Register SpaceMouse commands."""
        if "spacemouse" in ci.name:
            from .cmd.cmd import register_spacemouse_commands

            register_spacemouse_commands(logger)


# Create the ``bundle_api`` object that ChimeraX expects.
bundle_api = _SpaceMouseAPI()
