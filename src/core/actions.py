# vim: set expandtab shiftwidth=4 softtabstop=4:


class ViewAction:
    """Applies SpaceMouse 6DoF input to camera/view manipulation."""

    def __init__(self, session, config):
        """Initialize the view action handler.

        Parameters
        ----------
        session : chimerax.core.session.Session
            The ChimeraX session.
        config : SpaceMouseConfig
            The SpaceMouse configuration.
        """
        self.session = session
        self.config = config

    @property
    def view(self):
        """Get the main view.

        Returns
        -------
        chimerax.graphics.View
            The main view.
        """
        return self.session.main_view

    def apply(self, x, y, z, roll, pitch, yaw):
        """Apply view transformations based on 6DoF SpaceMouse input.

        Natural 6DoF mapping:
        - x (left/right translation) -> camera pan horizontal
        - y (forward/back translation) -> camera pan vertical
        - z (up/down translation) -> zoom (push up = zoom in)
        - roll (twist) -> camera roll rotation
        - pitch (tilt cap forward/back) -> camera tilt (up/down rotation)
        - yaw (rotate base left/right) -> camera spin (left/right rotation)

        Parameters
        ----------
        x : float
            X-axis translation (-1 to 1) for horizontal panning.
        y : float
            Y-axis translation (-1 to 1) for vertical panning.
        z : float
            Z-axis translation (-1 to 1) for zooming.
        roll : float
            Roll rotation (-1 to 1) for camera roll.
        pitch : float
            Pitch rotation (-1 to 1) for camera tilt.
        yaw : float
            Yaw rotation (-1 to 1) for camera spin.
        """
        # Skip if all inputs are near zero
        if all(abs(v) < 0.001 for v in [x, y, z, roll, pitch, yaw]):
            return

        # Pan (X/Y translation)
        if abs(x) > 0.001 or abs(y) > 0.001:
            self._apply_pan(x, y, self.config.translation_sensitivity)

        # Zoom (Z translation)
        if abs(z) > 0.001:
            self._apply_zoom(z, self.config.zoom_sensitivity)

        # Rotation (roll/pitch/yaw)
        if any(abs(v) > 0.001 for v in [roll, pitch, yaw]):
            self._apply_rotation(roll, pitch, yaw, self.config.rotation_sensitivity)

    def _apply_pan(self, pan_x, pan_y, sensitivity):
        """Apply panning to the view.

        Parameters
        ----------
        pan_x : float
            Horizontal pan amount.
        pan_y : float
            Vertical pan amount.
        sensitivity : float
            Sensitivity multiplier.
        """
        # Get pixel size for scaling
        psize = self.view.pixel_size()
        if psize is None:
            psize = 1.0

        # Pan speed in scene units per frame
        pan_speed = sensitivity * 20.0 * psize

        # Calculate shift in camera coordinates
        # X moves right, Y moves up (negate for natural feel)
        shift_cam = (pan_x * pan_speed, -pan_y * pan_speed, 0)

        # Convert to scene coordinates
        camera_pos = self.view.camera.position
        shift_scene = camera_pos.transform_vector(shift_cam)

        self.view.translate(shift_scene)

    def _apply_rotation(self, roll, pitch, yaw, sensitivity):
        """Apply 3-axis rotation to the view.

        Parameters
        ----------
        roll : float
            Roll rotation amount (twist around view axis).
        pitch : float
            Pitch rotation amount (tilt up/down).
        yaw : float
            Yaw rotation amount (spin left/right).
        sensitivity : float
            Sensitivity multiplier.
        """
        # Get camera position for coordinate conversion
        camera_pos = self.view.camera.position

        # Rotation speed in degrees per frame
        angle_speed = sensitivity * 2.0

        # Yaw - spin left/right (around camera Y axis)
        if abs(yaw) > 0.001:
            axis = camera_pos.transform_vector((0, 1, 0))
            angle = yaw * angle_speed
            self.view.rotate(axis, angle)

        # Pitch - tilt up/down (around camera X axis)
        if abs(pitch) > 0.001:
            axis = camera_pos.transform_vector((1, 0, 0))
            angle = pitch * angle_speed
            self.view.rotate(axis, angle)

        # Roll - twist (around camera Z axis)
        if abs(roll) > 0.001:
            axis = camera_pos.transform_vector((0, 0, 1))
            angle = roll * angle_speed
            self.view.rotate(axis, angle)

    def _apply_zoom(self, zoom, sensitivity):
        """Apply zoom to the view.

        Parameters
        ----------
        zoom : float
            Zoom amount (-1 to 1, positive zooms in).
        sensitivity : float
            Sensitivity multiplier.
        """
        v = self.view
        c = v.camera

        # Get pixel size for scaling
        psize = v.pixel_size()
        if psize is None:
            psize = 1.0

        if c.name == "orthographic":
            # For orthographic camera, adjust field width
            zoom_speed = sensitivity * 15.0
            delta_z = zoom * zoom_speed * psize
            c.field_width = max(c.field_width - delta_z, psize)
            c.redraw_needed = True

        elif c.name == "vr":
            # For VR/XR cameras (including Sony Spatial Reality), use scale transformation
            # Scale factor: >1 zooms in, <1 zooms out
            zoom_speed = sensitivity * 0.02  # Smaller value for scale-based zoom
            scale_factor = 1.0 + (zoom * zoom_speed)

            # Clamp scale factor per frame
            scale_factor = max(0.9, min(1.1, scale_factor))

            # Get zoom center (scene center)
            bounds = v.drawing_bounds()
            if bounds is not None:
                center = c.room_to_scene.inverse() * bounds.center()
            elif hasattr(c, "room_position"):
                center = c.room_position.origin()
            else:
                center = (0, 0, 0)

            # Apply scale transformation
            from chimerax.geometry import scale, translation

            scale_transform = translation(center) * scale(scale_factor) * translation(-center)
            c.move_scene(scale_transform)

        elif c.name == "lookingglass":
            # For LookingGlass displays, adjust depth_offset
            zoom_speed = sensitivity * 15.0
            delta_z = zoom * zoom_speed * psize
            c.depth_offset -= delta_z

        else:
            # For standard perspective cameras, translate along camera Z axis
            zoom_speed = sensitivity * 15.0
            delta_z = zoom * zoom_speed * psize
            shift = c.position.transform_vector((0, 0, delta_z))
            v.translate(shift)


class ModelAction:
    """Applies SpaceMouse 6DoF input to selected model manipulation."""

    def __init__(self, session, config):
        """Initialize the model action handler.

        Parameters
        ----------
        session : chimerax.core.session.Session
            The ChimeraX session.
        config : SpaceMouseConfig
            The SpaceMouse configuration.
        """
        self.session = session
        self.config = config

    @property
    def view(self):
        """Get the main view.

        Returns
        -------
        chimerax.graphics.View
            The main view.
        """
        return self.session.main_view

    def apply(self, x, y, z, roll, pitch, yaw):
        """Apply model transformations based on 6DoF SpaceMouse input.

        Parameters
        ----------
        x : float
            X-axis translation (-1 to 1) for X translation.
        y : float
            Y-axis translation (-1 to 1) for Y translation.
        z : float
            Z-axis translation (-1 to 1) for Z translation.
        roll : float
            Roll rotation (-1 to 1) for roll rotation.
        pitch : float
            Pitch rotation (-1 to 1) for pitch rotation.
        yaw : float
            Yaw rotation (-1 to 1) for yaw rotation.
        """
        # Get selected models
        models = self._get_selected_models()
        if not models:
            return

        # Skip if all inputs are near zero
        if all(abs(v) < 0.001 for v in [x, y, z, roll, pitch, yaw]):
            return

        # Translation XYZ
        if any(abs(v) > 0.001 for v in [x, y, z]):
            self._apply_translation(models, x, y, z, self.config.translation_sensitivity, self.config.zoom_sensitivity)

        # Rotation (roll/pitch/yaw)
        if any(abs(v) > 0.001 for v in [roll, pitch, yaw]):
            self._apply_rotation(models, roll, pitch, yaw, self.config.rotation_sensitivity)

    def _get_selected_models(self):
        """Get the list of selected models that can be transformed.

        Returns
        -------
        list
            List of selected models with position attribute.
        """
        # Get top-level selected models
        from chimerax.core.models import Model

        selected = []
        for m in self.session.selection.models():
            # Only include top-level models with position attribute
            if (
                isinstance(m, Model)
                and hasattr(m, "position")
                and (m.parent is None or m.parent is self.session.models.scene_root_model)
            ):
                selected.append(m)

        return selected

    def _apply_translation(self, models, translate_x, translate_y, translate_z, xy_sensitivity, z_sensitivity):
        """Apply 3-axis translation to models.

        Parameters
        ----------
        models : list
            List of models to translate.
        translate_x : float
            X translation amount.
        translate_y : float
            Y translation amount.
        translate_z : float
            Z translation amount.
        xy_sensitivity : float
            Sensitivity multiplier for X/Y.
        z_sensitivity : float
            Sensitivity multiplier for Z.
        """
        from chimerax.geometry import translation

        # Get pixel size for scaling
        psize = self.view.pixel_size()
        if psize is None:
            psize = 1.0

        # Translation speed in scene units per frame
        xy_speed = xy_sensitivity * 20.0 * psize
        z_speed = z_sensitivity * 60.0 * psize  # Higher speed for Z

        # Calculate shift in camera coordinates
        shift_cam = (
            translate_x * xy_speed,
            -translate_y * xy_speed,  # Negate for natural feel
            translate_z * z_speed,
        )

        # Convert to scene coordinates
        camera_pos = self.view.camera.position
        shift_scene = camera_pos.transform_vector(shift_cam)

        trans = translation(shift_scene)

        for model in models:
            model.position = trans * model.position

    def _apply_rotation(self, models, roll, pitch, yaw, sensitivity):
        """Apply 3-axis rotation to models.

        Parameters
        ----------
        models : list
            List of models to rotate.
        roll : float
            Roll rotation amount.
        pitch : float
            Pitch rotation amount.
        yaw : float
            Yaw rotation amount.
        sensitivity : float
            Sensitivity multiplier.
        """
        from chimerax.geometry import rotation

        # Get camera position for coordinate conversion
        camera_pos = self.view.camera.position

        # Rotation speed in degrees per frame
        angle_speed = sensitivity * 2.0

        for model in models:
            # Get rotation center (model center)
            center = self._get_model_center(model)

            current_pos = model.position

            # Yaw - spin around camera Y axis
            if abs(yaw) > 0.001:
                axis = camera_pos.transform_vector((0, 1, 0))
                angle = yaw * angle_speed
                rot = rotation(axis, angle, center)
                current_pos = rot * current_pos

            # Pitch - tilt around camera X axis
            if abs(pitch) > 0.001:
                axis = camera_pos.transform_vector((1, 0, 0))
                angle = pitch * angle_speed
                rot = rotation(axis, angle, center)
                current_pos = rot * current_pos

            # Roll - twist around camera Z axis
            if abs(roll) > 0.001:
                axis = camera_pos.transform_vector((0, 0, 1))
                angle = roll * angle_speed
                rot = rotation(axis, angle, center)
                current_pos = rot * current_pos

            model.position = current_pos

    def _get_model_center(self, model):
        """Get the center point of a model for rotation.

        Parameters
        ----------
        model : Model
            The model to get the center of.

        Returns
        -------
        tuple
            (x, y, z) center point in scene coordinates.
        """
        if hasattr(model, "bounds"):
            bounds = model.bounds()
            if bounds is not None:
                return tuple(bounds.center())
        return (0, 0, 0)
