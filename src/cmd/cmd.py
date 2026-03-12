# vim: set expandtab shiftwidth=4 softtabstop=4:

"""SpaceMouse command implementations and registration."""


def spacemouse(session):
    """Open the SpaceMouse tool.

    Parameters
    ----------
    session : chimerax.core.session.Session
        The ChimeraX session.
    """
    from chimerax.core.commands import run

    run(session, "ui tool show SpaceMouse")


def spacemouse_start(session):
    """Start SpaceMouse control.

    Parameters
    ----------
    session : chimerax.core.session.Session
        The ChimeraX session.
    """
    tool = _get_or_create_tool(session)
    if tool and tool.spacemouse_manager:
        tool.spacemouse_manager.start()
        session.logger.info("SpaceMouse control started")


def spacemouse_stop(session):
    """Stop SpaceMouse control.

    Parameters
    ----------
    session : chimerax.core.session.Session
        The ChimeraX session.
    """
    if hasattr(session, "spacemouse") and session.spacemouse:
        session.spacemouse.spacemouse_manager.stop()
        session.logger.info("SpaceMouse control stopped")
    else:
        session.logger.warning("SpaceMouse tool not running")


def spacemouse_mode(session, mode):
    """Set SpaceMouse control mode.

    Parameters
    ----------
    session : chimerax.core.session.Session
        The ChimeraX session.
    mode : str
        The mode to set ("view" or "model").
    """
    tool = _get_tool(session)
    if not tool:
        return

    from ..core.config import ControlMode

    if mode == "view":
        tool.spacemouse_manager.mode = ControlMode.VIEW
        session.logger.info("SpaceMouse mode set to: view")
    elif mode == "model":
        tool.spacemouse_manager.mode = ControlMode.MODEL
        session.logger.info("SpaceMouse mode set to: model")
    else:
        session.logger.warning(f"Unknown mode: {mode}")

    # Update UI if available
    if hasattr(tool, "_update_status"):
        tool._update_status()


def spacemouse_sensitivity(session, target, value):
    """Set SpaceMouse sensitivity.

    Parameters
    ----------
    session : chimerax.core.session.Session
        The ChimeraX session.
    target : str
        The target to set ("translation", "rotation", or "zoom").
    value : float
        The sensitivity value (0.1 to 5.0).
    """
    tool = _get_tool(session)
    if not tool:
        return

    config = tool.spacemouse_manager.config

    if target == "translation":
        config.translation_sensitivity = value
        session.logger.info(f"Translation sensitivity set to: {config.translation_sensitivity}")
    elif target == "rotation":
        config.rotation_sensitivity = value
        session.logger.info(f"Rotation sensitivity set to: {config.rotation_sensitivity}")
    elif target == "zoom":
        config.zoom_sensitivity = value
        session.logger.info(f"Zoom sensitivity set to: {config.zoom_sensitivity}")
    else:
        session.logger.warning(f"Unknown target: {target}")
        return

    config.save()


def spacemouse_deadzone(session, value):
    """Set SpaceMouse dead zone.

    Parameters
    ----------
    session : chimerax.core.session.Session
        The ChimeraX session.
    value : float
        The dead zone value (0.0 to 0.5).
    """
    tool = _get_tool(session)
    if not tool:
        return

    config = tool.spacemouse_manager.config
    config.dead_zone = value
    config.save()
    session.logger.info(f"Dead zone set to: {config.dead_zone}")


def spacemouse_invert(session, axis, value):
    """Invert a SpaceMouse axis.

    Parameters
    ----------
    session : chimerax.core.session.Session
        The ChimeraX session.
    axis : str
        The axis to invert ("x", "y", "z", "roll", "pitch", or "yaw").
    value : bool
        True to invert, False to not invert.
    """
    tool = _get_tool(session)
    if not tool:
        return

    config = tool.spacemouse_manager.config

    axis = axis.lower()
    if axis not in config.AXIS_NAMES:
        session.logger.warning(f"Unknown axis: {axis}. Valid axes: {', '.join(config.AXIS_NAMES)}")
        return

    config.set_invert(axis, value)
    config.save()
    session.logger.info(f"Axis '{axis}' invert set to: {value}")


def spacemouse_bind(session, button, command):
    """Bind a SpaceMouse button to a ChimeraX command.

    Parameters
    ----------
    session : chimerax.core.session.Session
        The ChimeraX session.
    button : str
        The button name (e.g., "LEFT", "RIGHT").
    command : str
        The ChimeraX command to execute.
    """
    tool = _get_tool(session)
    if not tool:
        return

    config = tool.spacemouse_manager.config
    config.set_button_command(button.upper(), command)
    config.save()
    session.logger.info(f"Bound {button.upper()} to: {command}")


def spacemouse_unbind(session, button):
    """Remove a SpaceMouse button binding.

    Parameters
    ----------
    session : chimerax.core.session.Session
        The ChimeraX session.
    button : str
        The button name to unbind.
    """
    tool = _get_tool(session)
    if not tool:
        return

    config = tool.spacemouse_manager.config
    config.set_button_command(button.upper(), None)
    config.save()
    session.logger.info(f"Unbound {button.upper()}")


def spacemouse_settings(session):
    """Open the SpaceMouse settings dialog.

    Parameters
    ----------
    session : chimerax.core.session.Session
        The ChimeraX session.
    """
    tool = _get_or_create_tool(session)
    if tool:
        tool._open_settings()


# Helper functions


def _get_tool(session):
    """Get the SpaceMouse tool if it exists.

    Parameters
    ----------
    session : chimerax.core.session.Session
        The ChimeraX session.

    Returns
    -------
    SpaceMouseTool or None
        The SpaceMouse tool instance, or None if not running.
    """
    if hasattr(session, "spacemouse") and session.spacemouse:
        return session.spacemouse
    else:
        session.logger.warning("SpaceMouse tool not running. Use 'spacemouse' to start it.")
        return None


def _get_or_create_tool(session):
    """Get or create the SpaceMouse tool.

    Parameters
    ----------
    session : chimerax.core.session.Session
        The ChimeraX session.

    Returns
    -------
    SpaceMouseTool
        The SpaceMouse tool instance.
    """
    if hasattr(session, "spacemouse") and session.spacemouse:
        return session.spacemouse

    # Start the tool
    from ..tool import SpaceMouseTool

    return SpaceMouseTool(session, "SpaceMouse")


# Command registration


def register_spacemouse_commands(logger):
    """Register all SpaceMouse commands with ChimeraX.

    Parameters
    ----------
    logger : chimerax.core.logger.Logger
        The ChimeraX logger.
    """
    from chimerax.core.commands import BoolArg, CmdDesc, EnumOf, FloatArg, StringArg, register

    # spacemouse - open the tool
    register(
        "spacemouse",
        CmdDesc(synopsis="Open the SpaceMouse controller tool"),
        spacemouse,
    )

    # spacemouse start
    register(
        "spacemouse start",
        CmdDesc(synopsis="Start SpaceMouse control"),
        spacemouse_start,
    )

    # spacemouse stop
    register(
        "spacemouse stop",
        CmdDesc(synopsis="Stop SpaceMouse control"),
        spacemouse_stop,
    )

    # spacemouse mode <view|model>
    register(
        "spacemouse mode",
        CmdDesc(
            required=[("mode", EnumOf(["view", "model"]))],
            synopsis="Set SpaceMouse control mode (view or model)",
        ),
        spacemouse_mode,
    )

    # spacemouse sensitivity <translation|rotation|zoom> <value>
    register(
        "spacemouse sensitivity",
        CmdDesc(
            required=[("target", EnumOf(["translation", "rotation", "zoom"])), ("value", FloatArg)],
            synopsis="Set SpaceMouse sensitivity (0.1 to 5.0)",
        ),
        spacemouse_sensitivity,
    )

    # spacemouse deadzone <value>
    register(
        "spacemouse deadzone",
        CmdDesc(
            required=[("value", FloatArg)],
            synopsis="Set SpaceMouse dead zone (0.0 to 0.5)",
        ),
        spacemouse_deadzone,
    )

    # spacemouse invert <axis> <true|false>
    register(
        "spacemouse invert",
        CmdDesc(
            required=[
                ("axis", EnumOf(["x", "y", "z", "roll", "pitch", "yaw"])),
                ("value", BoolArg),
            ],
            synopsis="Invert a SpaceMouse axis",
        ),
        spacemouse_invert,
    )

    # spacemouse bind <button> <command>
    register(
        "spacemouse bind",
        CmdDesc(
            required=[("button", StringArg), ("command", StringArg)],
            synopsis="Bind SpaceMouse button to ChimeraX command",
        ),
        spacemouse_bind,
    )

    # spacemouse unbind <button>
    register(
        "spacemouse unbind",
        CmdDesc(
            required=[("button", StringArg)],
            synopsis="Remove SpaceMouse button binding",
        ),
        spacemouse_unbind,
    )

    # spacemouse settings
    register(
        "spacemouse settings",
        CmdDesc(synopsis="Open SpaceMouse settings dialog"),
        spacemouse_settings,
    )
