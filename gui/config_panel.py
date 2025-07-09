"""
Configuration Panel Module
Handles processing configuration settings for MISR data.
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import json
from pathlib import Path
from typing import Callable, Dict, Any
import logging

import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))
from processing_core import ProcessingConfig
from config.preset_loader import PresetLoader

logger = logging.getLogger(__name__)


class ConfigPanel:
    """Panel for configuring MISR processing settings."""

    def __init__(self, parent, callback: Callable[[ProcessingConfig], None]):
        """Initialize configuration panel."""
        self.parent = parent
        self.callback = callback
        self.config = ProcessingConfig()

        # Initialize preset loader
        self.preset_loader = PresetLoader()

        self.frame = ttk.LabelFrame(
            parent, text="Processing Configuration", padding="5"
        )
        self._setup_ui()
        self._update_config()

    def _setup_ui(self):
        """Create configuration UI components."""
        # Processing mode selector at the top
        mode_frame = ttk.LabelFrame(self.frame, text="Processing Mode", padding="5")
        mode_frame.grid(row=0, column=0, sticky="ew", padx=5, pady=5)
        mode_frame.columnconfigure(0, weight=1)

        self.processing_mode = tk.StringVar(value="netcdf")

        ttk.Radiobutton(
            mode_frame,
            text="NetCDF Processing (Advanced)",
            variable=self.processing_mode,
            value="netcdf",
            command=self._on_mode_change,
        ).grid(row=0, column=0, sticky="w")

        ttk.Radiobutton(
            mode_frame,
            text="HDF Processing (MISR Toolkit)",
            variable=self.processing_mode,
            value="hdf",
            command=self._on_mode_change,
        ).grid(row=1, column=0, sticky="w")

        # Create notebook for organized tabs
        self.notebook = ttk.Notebook(self.frame)
        self.notebook.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)

        # Configure frame grid weights
        self.frame.columnconfigure(0, weight=1)
        self.frame.rowconfigure(1, weight=1)

        # Create tabs
        self._create_region_tab()
        self._create_processing_tab()
        self._create_output_tab()
        self._create_advanced_tab()
        self._create_hdf_tab()

        # Update button
        update_frame = ttk.Frame(self.frame)
        update_frame.grid(row=2, column=0, sticky="ew", pady=(5, 0))

        ttk.Button(
            update_frame, text="Apply Configuration", command=self._update_config
        ).grid(row=0, column=0, sticky="w")

        ttk.Button(
            update_frame, text="Reset to Defaults", command=self._reset_defaults
        ).grid(row=0, column=1, padx=(10, 0))

    def _create_region_tab(self):
        """Create region selection tab."""
        region_frame = ttk.Frame(self.notebook)
        self.notebook.add(region_frame, text="Target Region")

        # Target coordinates
        coords_frame = ttk.LabelFrame(
            region_frame, text="Target Coordinates", padding="5"
        )
        coords_frame.grid(row=0, column=0, sticky="ew", padx=5, pady=5)
        coords_frame.columnconfigure(1, weight=1)

        ttk.Label(coords_frame, text="Latitude:").grid(row=0, column=0, sticky="w")
        self.lat_var = tk.DoubleVar(value=self.config.target_lat)
        self.lat_spinbox = ttk.Spinbox(
            coords_frame,
            from_=-90,
            to=90,
            increment=0.1,
            textvariable=self.lat_var,
            width=15,
        )
        self.lat_spinbox.grid(row=0, column=1, sticky="ew", padx=(5, 0))

        ttk.Label(coords_frame, text="Longitude:").grid(row=1, column=0, sticky="w")
        self.lon_var = tk.DoubleVar(value=self.config.target_lon)
        self.lon_spinbox = ttk.Spinbox(
            coords_frame,
            from_=-180,
            to=180,
            increment=0.1,
            textvariable=self.lon_var,
            width=15,
        )
        self.lon_spinbox.grid(row=1, column=1, sticky="ew", padx=(5, 0))

        ttk.Label(coords_frame, text="Region Margin (°):").grid(
            row=2, column=0, sticky="w"
        )
        self.margin_var = tk.DoubleVar(value=self.config.region_margin)
        self.margin_spinbox = ttk.Spinbox(
            coords_frame,
            from_=0.1,
            to=10.0,
            increment=0.1,
            textvariable=self.margin_var,
            width=15,
        )
        self.margin_spinbox.grid(row=2, column=1, sticky="ew", padx=(5, 0))

        # Resolution settings
        res_frame = ttk.LabelFrame(
            region_frame, text="Resolution Settings", padding="5"
        )
        res_frame.grid(row=1, column=0, sticky="ew", padx=5, pady=5)
        res_frame.columnconfigure(1, weight=1)

        ttk.Label(res_frame, text="Target Resolution (°):").grid(
            row=0, column=0, sticky="w"
        )
        self.resolution_var = tk.DoubleVar(value=self.config.target_resolution)
        self.resolution_spinbox = ttk.Spinbox(
            res_frame,
            from_=0.001,
            to=0.01,
            increment=0.0005,
            textvariable=self.resolution_var,
            width=15,
        )
        self.resolution_spinbox.grid(row=0, column=1, sticky="ew", padx=(5, 0))

        # Quick preset buttons
        preset_frame = ttk.LabelFrame(region_frame, text="Quick Presets", padding="5")
        preset_frame.grid(row=2, column=0, sticky="ew", padx=5, pady=5)

        # Configure preset frame grid
        preset_frame.columnconfigure(0, weight=1)
        preset_frame.columnconfigure(1, weight=1)
        preset_frame.columnconfigure(2, weight=1)
        preset_frame.columnconfigure(3, weight=1)
        preset_frame.columnconfigure(4, weight=1)

        # Load presets dynamically
        self._create_preset_buttons(preset_frame)

    def _create_processing_tab(self):
        """Create processing options tab."""
        proc_frame = ttk.Frame(self.notebook)
        self.notebook.add(proc_frame, text="Processing")

        # QA filtering
        qa_frame = ttk.LabelFrame(
            proc_frame, text="Quality Assurance Filtering", padding="5"
        )
        qa_frame.grid(row=0, column=0, sticky="ew", padx=5, pady=5)
        qa_frame.columnconfigure(0, weight=1)

        self.qa_enabled_var = tk.BooleanVar(value=self.config.enable_qa_filtering)
        ttk.Checkbutton(
            qa_frame,
            text="Enable QA filtering",
            variable=self.qa_enabled_var,
            command=self._toggle_qa_options,
        ).grid(row=0, column=0, sticky="w")

        self.qa_options_frame = ttk.Frame(qa_frame)
        self.qa_options_frame.grid(row=1, column=0, sticky="ew", pady=(5, 0))

        # QA filter checkboxes
        self.qa_filter_vars = {}
        qa_filters = [
            ("cloud_detected", "Filter cloud-detected pixels"),
            ("high_quality", "Require high quality retrievals"),
            ("shadow_detected", "Filter shadow-detected pixels"),
        ]

        for i, (filter_name, description) in enumerate(qa_filters):
            var = tk.BooleanVar(value=filter_name in self.config.qa_filters)
            self.qa_filter_vars[filter_name] = var
            ttk.Checkbutton(self.qa_options_frame, text=description, variable=var).grid(
                row=i, column=0, sticky="w", padx=(20, 0)
            )

        # Shapefile clipping
        clip_frame = ttk.LabelFrame(proc_frame, text="Shapefile Clipping", padding="5")
        clip_frame.grid(row=1, column=0, sticky="ew", padx=5, pady=5)
        clip_frame.columnconfigure(1, weight=1)

        self.clipping_enabled_var = tk.BooleanVar(value=self.config.enable_clipping)
        ttk.Checkbutton(
            clip_frame,
            text="Enable shapefile clipping",
            variable=self.clipping_enabled_var,
            command=self._toggle_clipping_options,
        ).grid(row=0, column=0, columnspan=2, sticky="w")

        self.shapefile_frame = ttk.Frame(clip_frame)
        self.shapefile_frame.grid(
            row=1, column=0, columnspan=2, sticky="ew", pady=(5, 0)
        )
        self.shapefile_frame.columnconfigure(1, weight=1)

        ttk.Label(self.shapefile_frame, text="Shapefile:").grid(
            row=0, column=0, sticky="w"
        )

        self.shapefile_var = tk.StringVar(value=self.config.shapefile_path or "")
        self.shapefile_entry = ttk.Entry(
            self.shapefile_frame, textvariable=self.shapefile_var, state="readonly"
        )
        self.shapefile_entry.grid(row=0, column=1, sticky="ew", padx=(5, 5))

        ttk.Button(
            self.shapefile_frame, text="Browse...", command=self._browse_shapefile
        ).grid(row=0, column=2)

        self._toggle_qa_options()
        self._toggle_clipping_options()

    def _create_hdf_tab(self):
        """Create HDF-specific processing tab."""
        hdf_frame = ttk.Frame(self.notebook)
        self.notebook.add(hdf_frame, text="HDF Settings")

        # Region settings for HDF
        region_frame = ttk.LabelFrame(hdf_frame, text="Region Coordinates", padding="5")
        region_frame.grid(row=0, column=0, sticky="ew", padx=5, pady=5)
        region_frame.columnconfigure(1, weight=1)

        # Upper left corner
        ttk.Label(region_frame, text="Upper Left Latitude:").grid(
            row=0, column=0, sticky="w"
        )
        self.hdf_ulc_lat_var = tk.DoubleVar(value=0.0)
        ttk.Spinbox(
            region_frame,
            from_=-90,
            to=90,
            increment=0.1,
            textvariable=self.hdf_ulc_lat_var,
            width=15,
        ).grid(row=0, column=1, sticky="ew", padx=(5, 0))

        ttk.Label(region_frame, text="Upper Left Longitude:").grid(
            row=1, column=0, sticky="w"
        )
        self.hdf_ulc_lon_var = tk.DoubleVar(value=0.0)
        ttk.Spinbox(
            region_frame,
            from_=-180,
            to=180,
            increment=0.1,
            textvariable=self.hdf_ulc_lon_var,
            width=15,
        ).grid(row=1, column=1, sticky="ew", padx=(5, 0))

        # Lower right corner
        ttk.Label(region_frame, text="Lower Right Latitude:").grid(
            row=2, column=0, sticky="w"
        )
        self.hdf_lrc_lat_var = tk.DoubleVar(value=0.0)
        ttk.Spinbox(
            region_frame,
            from_=-90,
            to=90,
            increment=0.1,
            textvariable=self.hdf_lrc_lat_var,
            width=15,
        ).grid(row=2, column=1, sticky="ew", padx=(5, 0))

        ttk.Label(region_frame, text="Lower Right Longitude:").grid(
            row=3, column=0, sticky="w"
        )
        self.hdf_lrc_lon_var = tk.DoubleVar(value=0.0)
        ttk.Spinbox(
            region_frame,
            from_=-180,
            to=180,
            increment=0.1,
            textvariable=self.hdf_lrc_lon_var,
            width=15,
        ).grid(row=3, column=1, sticky="ew", padx=(5, 0))

        # Field selection
        field_frame = ttk.LabelFrame(hdf_frame, text="Data Field", padding="5")
        field_frame.grid(row=1, column=0, sticky="ew", padx=5, pady=5)
        field_frame.columnconfigure(1, weight=1)

        ttk.Label(field_frame, text="MISR Field:").grid(row=0, column=0, sticky="w")
        self.hdf_field_var = tk.StringVar(value="Red Radiance/RDQI")
        field_combo = ttk.Combobox(
            field_frame,
            textvariable=self.hdf_field_var,
            width=25,
            values=[
                "Red Radiance/RDQI",
                "Red Radiance",
                "Red Brf",
                "Green Radiance/RDQI",
                "Blue Radiance/RDQI",
                "NIR Radiance/RDQI",
            ],
        )
        field_combo.grid(row=0, column=1, sticky="ew", padx=(5, 0))

        # Quality filtering
        quality_frame = ttk.LabelFrame(hdf_frame, text="Quality Filtering", padding="5")
        quality_frame.grid(row=2, column=0, sticky="ew", padx=5, pady=5)

        self.hdf_quality_filter_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(
            quality_frame,
            text="Apply quality filtering",
            variable=self.hdf_quality_filter_var,
        ).grid(row=0, column=0, sticky="w")

        # Initially hide HDF tab (will be shown when HDF mode is selected)
        self.hdf_tab_index = len(self.notebook.tabs()) - 1
        self._on_mode_change()

    def _on_mode_change(self):
        """Handle processing mode change."""
        mode = self.processing_mode.get()

        # Show/hide appropriate tabs
        if mode == "hdf":
            # Hide NetCDF-specific tabs and show HDF tab
            if self.hdf_tab_index < len(self.notebook.tabs()):
                self.notebook.tab(self.hdf_tab_index, state="normal")
            # Hide advanced tab for HDF mode
            self.notebook.tab(3, state="hidden")  # Advanced tab
        else:
            # Hide HDF tab and show NetCDF tabs
            if self.hdf_tab_index < len(self.notebook.tabs()):
                self.notebook.tab(self.hdf_tab_index, state="hidden")
            # Show advanced tab for NetCDF mode
            self.notebook.tab(3, state="normal")  # Advanced tab

        # Update configuration
        self._update_config()

    def _create_output_tab(self):
        """Create output settings tab."""
        output_frame = ttk.Frame(self.notebook)
        self.notebook.add(output_frame, text="Output")

        # Output directory
        dir_frame = ttk.LabelFrame(output_frame, text="Output Directory", padding="5")
        dir_frame.grid(row=0, column=0, sticky="ew", padx=5, pady=5)
        dir_frame.columnconfigure(1, weight=1)

        ttk.Label(dir_frame, text="Directory:").grid(row=0, column=0, sticky="w")

        self.output_dir_var = tk.StringVar(value=self.config.output_directory)
        self.output_dir_entry = ttk.Entry(dir_frame, textvariable=self.output_dir_var)
        self.output_dir_entry.grid(row=0, column=1, sticky="ew", padx=(5, 5))

        ttk.Button(dir_frame, text="Browse...", command=self._browse_output_dir).grid(
            row=0, column=2
        )

        # Export formats
        format_frame = ttk.LabelFrame(output_frame, text="Export Formats", padding="5")
        format_frame.grid(row=1, column=0, sticky="ew", padx=5, pady=5)

        self.export_netcdf_var = tk.BooleanVar(value=self.config.export_netcdf)
        ttk.Checkbutton(
            format_frame, text="Export NetCDF (.nc)", variable=self.export_netcdf_var
        ).grid(row=0, column=0, sticky="w")

        self.export_geotiff_var = tk.BooleanVar(value=self.config.export_geotiff)
        ttk.Checkbutton(
            format_frame, text="Export GeoTIFF (.tif)", variable=self.export_geotiff_var
        ).grid(row=1, column=0, sticky="w")

        # File naming
        naming_frame = ttk.LabelFrame(output_frame, text="File Naming", padding="5")
        naming_frame.grid(row=2, column=0, sticky="ew", padx=5, pady=5)

        self.add_timestamp_var = tk.BooleanVar(value=self.config.add_timestamp)
        ttk.Checkbutton(
            naming_frame,
            text="Add timestamp to filenames",
            variable=self.add_timestamp_var,
        ).grid(row=0, column=0, sticky="w")

        self.overwrite_var = tk.BooleanVar(value=self.config.overwrite_existing)
        ttk.Checkbutton(
            naming_frame, text="Overwrite existing files", variable=self.overwrite_var
        ).grid(row=1, column=0, sticky="w")

    def _create_advanced_tab(self):
        """Create advanced settings tab."""
        advanced_frame = ttk.Frame(self.notebook)
        self.notebook.add(advanced_frame, text="Advanced")

        # Validation options
        validation_frame = ttk.LabelFrame(
            advanced_frame, text="Validation", padding="5"
        )
        validation_frame.grid(row=0, column=0, sticky="ew", padx=5, pady=5)

        self.validate_inputs_var = tk.BooleanVar(value=self.config.validate_inputs)
        ttk.Checkbutton(
            validation_frame,
            text="Validate input files before processing",
            variable=self.validate_inputs_var,
        ).grid(row=0, column=0, sticky="w")

        # Memory and performance
        perf_frame = ttk.LabelFrame(advanced_frame, text="Performance", padding="5")
        perf_frame.grid(row=1, column=0, sticky="ew", padx=5, pady=5)

        ttk.Label(perf_frame, text="Processing optimized for 275m red band data").grid(
            row=0, column=0, sticky="w"
        )

        # Configuration preview
        preview_frame = ttk.LabelFrame(
            advanced_frame, text="Configuration Summary", padding="5"
        )
        preview_frame.grid(row=2, column=0, sticky="ew", padx=5, pady=5)
        preview_frame.columnconfigure(0, weight=1)
        preview_frame.rowconfigure(0, weight=1)

        self.config_text = tk.Text(
            preview_frame, height=8, width=50, font=("Consolas", 9), state="disabled"
        )
        self.config_text.grid(row=0, column=0, sticky="nsew")

        config_scrollbar = ttk.Scrollbar(preview_frame, command=self.config_text.yview)
        config_scrollbar.grid(row=0, column=1, sticky="ns")
        self.config_text.configure(yscrollcommand=config_scrollbar.set)

    def _create_preset_buttons(self, parent_frame):
        """Create preset buttons dynamically from loaded presets."""
        preset_names = self.preset_loader.list_presets()

        # Create buttons for each preset
        for i, preset_name in enumerate(preset_names):
            if i < 4:  # Limit to 4 presets in the first row
                # Use default parameter to capture the preset name correctly
                ttk.Button(
                    parent_frame,
                    text=preset_name,
                    command=lambda name=preset_name: self._load_preset(name),
                ).grid(row=0, column=i, padx=(0, 5), sticky="w")

        # Add Custom Location button
        ttk.Button(
            parent_frame, text="Custom Location", command=self._custom_location
        ).grid(row=0, column=4, padx=(5, 0), sticky="w")

    def _load_preset(self, preset_name: str):
        """Load a preset configuration."""
        try:
            preset_config = self.preset_loader.get_processing_config(preset_name)
            if preset_config:
                # Update NetCDF mode coordinates
                target_lat = preset_config.get("target_lat", 0.0)
                target_lon = preset_config.get("target_lon", 0.0)

                self.lat_var.set(target_lat)
                self.lon_var.set(target_lon)
                self.margin_var.set(preset_config.get("region_margin", 2.0))
                self.resolution_var.set(preset_config.get("target_resolution", 0.0025))

                # Update HDF mode coordinates (calculate region from center point)
                region_margin = preset_config.get("region_margin", 2.0)
                hdf_ulc_lat = target_lat + region_margin
                hdf_ulc_lon = target_lon - region_margin
                hdf_lrc_lat = target_lat - region_margin
                hdf_lrc_lon = target_lon + region_margin

                self.hdf_ulc_lat_var.set(hdf_ulc_lat)
                self.hdf_ulc_lon_var.set(hdf_ulc_lon)
                self.hdf_lrc_lat_var.set(hdf_lrc_lat)
                self.hdf_lrc_lon_var.set(hdf_lrc_lon)

                logger.info(f"Updated HDF coordinates for {preset_name}:")
                logger.info(f"  Upper Left: {hdf_ulc_lat:.4f}°N, {hdf_ulc_lon:.4f}°W")
                logger.info(f"  Lower Right: {hdf_lrc_lat:.4f}°N, {hdf_lrc_lon:.4f}°W")

                # Update QA filtering settings
                self.qa_enabled_var.set(preset_config.get("enable_qa_filtering", False))

                # Update export settings
                self.export_netcdf_var.set(preset_config.get("export_netcdf", True))
                self.export_geotiff_var.set(preset_config.get("export_geotiff", True))
                self.add_timestamp_var.set(preset_config.get("add_timestamp", True))
                self.overwrite_var.set(preset_config.get("overwrite_existing", False))

                # Update advanced settings
                self.validate_inputs_var.set(preset_config.get("validate_inputs", True))

                # Update UI state
                self._toggle_qa_options()
                self._update_config()

                logger.info(
                    f"Loaded preset: {preset_name} (lat: {target_lat}, lon: {target_lon})"
                )
            else:
                logger.error(f"Failed to load preset configuration: {preset_name}")
        except Exception as e:
            logger.error(f"Error loading preset {preset_name}: {e}")

    def _set_preset(self, lat: float, lon: float, name: str):
        """Set coordinate preset."""
        self.lat_var.set(lat)
        self.lon_var.set(lon)
        logger.info(f"Set preset location: {name}")

    def _custom_location(self):
        """Open dialog for custom location input."""
        dialog = CustomLocationDialog(
            self.frame, self.lat_var.get(), self.lon_var.get()
        )
        if dialog.result:
            lat, lon = dialog.result
            self.lat_var.set(lat)
            self.lon_var.set(lon)
            logger.info(f"Set custom location: {lat}, {lon}")

    def _toggle_qa_options(self):
        """Toggle QA filter options based on enabled state."""
        state = "normal" if self.qa_enabled_var.get() else "disabled"
        for widget in self.qa_options_frame.winfo_children():
            widget.configure(state=state)

    def _toggle_clipping_options(self):
        """Toggle clipping options based on enabled state."""
        state = "normal" if self.clipping_enabled_var.get() else "disabled"
        for widget in self.shapefile_frame.winfo_children():
            try:
                widget.configure(state=state)
            except tk.TclError:
                # Some widgets don't support state changes
                pass

    def _browse_shapefile(self):
        """Browse for shapefile."""
        filetypes = [("Shapefiles", "*.shp"), ("All files", "*.*")]

        filename = filedialog.askopenfilename(
            title="Select shapefile for clipping", filetypes=filetypes
        )

        if filename:
            self.shapefile_var.set(filename)

    def _browse_output_dir(self):
        """Browse for output directory."""
        directory = filedialog.askdirectory(title="Select output directory")

        if directory:
            self.output_dir_var.set(directory)

    def _update_config(self):
        """Update configuration from UI values."""
        mode = self.processing_mode.get()

        if mode == "hdf":
            # Create HDF-specific configuration
            ulc_lat = self.hdf_ulc_lat_var.get()
            ulc_lon = self.hdf_ulc_lon_var.get()
            lrc_lat = self.hdf_lrc_lat_var.get()
            lrc_lon = self.hdf_lrc_lon_var.get()

            config_dict = {
                "processing_mode": "hdf",
                "ulc_lat": ulc_lat,
                "ulc_lon": ulc_lon,
                "lrc_lat": lrc_lat,
                "lrc_lon": lrc_lon,
                "field_name": self.hdf_field_var.get(),
                "apply_quality_filter": self.hdf_quality_filter_var.get(),
                "output_directory": getattr(
                    self, "output_dir_var", tk.StringVar()
                ).get()
                or ".",
            }

            # Store as a simple dictionary for HDF mode
            self.config = config_dict

            # Log the HDF configuration coordinates
            logger.info(f"Created HDF configuration with coordinates:")
            logger.info(f"  Upper Left: {ulc_lat:.4f}°N, {ulc_lon:.4f}°W")
            logger.info(f"  Lower Right: {lrc_lat:.4f}°N, {lrc_lon:.4f}°W")

        else:
            # NetCDF mode - use original ProcessingConfig
            qa_filters = []
            for filter_name, var in self.qa_filter_vars.items():
                if var.get():
                    qa_filters.append(filter_name)

            self.config = ProcessingConfig(
                target_lat=self.lat_var.get(),
                target_lon=self.lon_var.get(),
                region_margin=self.margin_var.get(),
                target_resolution=self.resolution_var.get(),
                enable_qa_filtering=self.qa_enabled_var.get(),
                qa_filters=qa_filters,
                enable_clipping=self.clipping_enabled_var.get(),
                shapefile_path=(
                    self.shapefile_var.get() if self.shapefile_var.get() else None
                ),
                output_directory=self.output_dir_var.get(),
                export_netcdf=self.export_netcdf_var.get(),
                export_geotiff=self.export_geotiff_var.get(),
                add_timestamp=self.add_timestamp_var.get(),
                overwrite_existing=self.overwrite_var.get(),
                validate_inputs=self.validate_inputs_var.get(),
            )

        # Update preview
        self._update_config_preview()

        # Notify callback
        self.callback(self.config)
        logger.info(f"Configuration updated for {mode} mode")

    def _update_config_preview(self):
        """Update configuration preview text."""
        # Handle both HDF dictionary config and NetCDF ProcessingConfig object
        if isinstance(self.config, dict):
            # HDF mode - config is a dictionary
            config_dict = {
                "processing_mode": self.config.get("processing_mode", "hdf"),
                "region": {
                    "ulc_lat": self.config.get("ulc_lat"),
                    "ulc_lon": self.config.get("ulc_lon"),
                    "lrc_lat": self.config.get("lrc_lat"),
                    "lrc_lon": self.config.get("lrc_lon"),
                },
                "field_name": self.config.get("field_name"),
                "apply_quality_filter": self.config.get("apply_quality_filter"),
                "output_directory": self.config.get("output_directory"),
            }
        else:
            # NetCDF mode - config is ProcessingConfig object
            config_dict = {
                "processing_mode": "netcdf",
                "region": {
                    "latitude": self.config.target_lat,
                    "longitude": self.config.target_lon,
                    "margin": self.config.region_margin,
                    "resolution": self.config.target_resolution,
                },
                "qa_filtering": {
                    "enabled": self.config.enable_qa_filtering,
                    "filters": self.config.qa_filters,
                },
                "clipping": {
                    "enabled": self.config.enable_clipping,
                    "shapefile": self.config.shapefile_path,
                },
                "output": {
                    "directory": self.config.output_directory,
                    "formats": {
                        "netcdf": self.config.export_netcdf,
                        "geotiff": self.config.export_geotiff,
                    },
                    "add_timestamp": self.config.add_timestamp,
                    "overwrite": self.config.overwrite_existing,
                },
            }

        config_text = json.dumps(config_dict, indent=2)

        self.config_text.configure(state="normal")
        self.config_text.delete(1.0, tk.END)
        self.config_text.insert(1.0, config_text)
        self.config_text.configure(state="disabled")

    def _reset_defaults(self):
        """Reset all settings to defaults."""
        if messagebox.askyesno(
            "Reset Configuration", "Reset all settings to defaults?"
        ):
            default_config = ProcessingConfig()

            self.lat_var.set(default_config.target_lat)
            self.lon_var.set(default_config.target_lon)
            self.margin_var.set(default_config.region_margin)
            self.resolution_var.set(default_config.target_resolution)

            self.qa_enabled_var.set(default_config.enable_qa_filtering)
            for filter_name, var in self.qa_filter_vars.items():
                var.set(filter_name in default_config.qa_filters)

            self.clipping_enabled_var.set(default_config.enable_clipping)
            self.shapefile_var.set(default_config.shapefile_path or "")

            self.output_dir_var.set(default_config.output_directory)
            self.export_netcdf_var.set(default_config.export_netcdf)
            self.export_geotiff_var.set(default_config.export_geotiff)
            self.add_timestamp_var.set(default_config.add_timestamp)
            self.overwrite_var.set(default_config.overwrite_existing)
            self.validate_inputs_var.set(default_config.validate_inputs)

            self._toggle_qa_options()
            self._toggle_clipping_options()
            self._update_config()

    def save_config(self, filename: str):
        """Save configuration to JSON file."""
        config_dict = {
            "target_lat": self.config.target_lat,
            "target_lon": self.config.target_lon,
            "region_margin": self.config.region_margin,
            "target_resolution": self.config.target_resolution,
            "enable_qa_filtering": self.config.enable_qa_filtering,
            "qa_filters": self.config.qa_filters,
            "enable_clipping": self.config.enable_clipping,
            "shapefile_path": self.config.shapefile_path,
            "output_directory": self.config.output_directory,
            "export_netcdf": self.config.export_netcdf,
            "export_geotiff": self.config.export_geotiff,
            "add_timestamp": self.config.add_timestamp,
            "overwrite_existing": self.config.overwrite_existing,
            "validate_inputs": self.config.validate_inputs,
        }

        with open(filename, "w") as f:
            json.dump(config_dict, f, indent=2)

    def load_config(self, filename: str):
        """Load configuration from JSON file."""
        with open(filename, "r") as f:
            config_dict = json.load(f)

        # Update UI variables
        self.lat_var.set(config_dict.get("target_lat", -13.8))
        self.lon_var.set(config_dict.get("target_lon", -70.8))
        self.margin_var.set(config_dict.get("region_margin", 2.0))
        self.resolution_var.set(config_dict.get("target_resolution", 0.0025))

        self.qa_enabled_var.set(config_dict.get("enable_qa_filtering", False))
        qa_filters = config_dict.get("qa_filters", [])
        for filter_name, var in self.qa_filter_vars.items():
            var.set(filter_name in qa_filters)

        self.clipping_enabled_var.set(config_dict.get("enable_clipping", False))
        self.shapefile_var.set(config_dict.get("shapefile_path", "") or "")

        self.output_dir_var.set(config_dict.get("output_directory", "."))
        self.export_netcdf_var.set(config_dict.get("export_netcdf", False))
        self.export_geotiff_var.set(config_dict.get("export_geotiff", True))
        self.add_timestamp_var.set(config_dict.get("add_timestamp", True))
        self.overwrite_var.set(config_dict.get("overwrite_existing", False))
        self.validate_inputs_var.set(config_dict.get("validate_inputs", True))

        self._toggle_qa_options()
        self._toggle_clipping_options()
        self._update_config()


class CustomLocationDialog:
    """Dialog for entering custom location coordinates."""

    def __init__(self, parent, initial_lat: float, initial_lon: float):
        self.result = None

        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Custom Location")
        self.dialog.geometry("300x150")
        self.dialog.resizable(False, False)

        # Make modal
        self.dialog.transient(parent)
        self.dialog.grab_set()

        # Center on parent
        self.dialog.update_idletasks()
        x = (
            parent.winfo_rootx()
            + (parent.winfo_width() // 2)
            - (self.dialog.winfo_width() // 2)
        )
        y = (
            parent.winfo_rooty()
            + (parent.winfo_height() // 2)
            - (self.dialog.winfo_height() // 2)
        )
        self.dialog.geometry(f"+{x}+{y}")

        # Create UI
        main_frame = ttk.Frame(self.dialog, padding="10")
        main_frame.grid(row=0, column=0, sticky="nsew")

        ttk.Label(main_frame, text="Latitude:").grid(row=0, column=0, sticky="w")
        self.lat_var = tk.DoubleVar(value=initial_lat)
        lat_entry = ttk.Entry(main_frame, textvariable=self.lat_var, width=15)
        lat_entry.grid(row=0, column=1, sticky="ew", padx=(5, 0))

        ttk.Label(main_frame, text="Longitude:").grid(row=1, column=0, sticky="w")
        self.lon_var = tk.DoubleVar(value=initial_lon)
        lon_entry = ttk.Entry(main_frame, textvariable=self.lon_var, width=15)
        lon_entry.grid(row=1, column=1, sticky="ew", padx=(5, 0))

        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=2, column=0, columnspan=2, pady=(10, 0))

        ttk.Button(button_frame, text="OK", command=self._ok).grid(
            row=0, column=0, padx=(0, 5)
        )
        ttk.Button(button_frame, text="Cancel", command=self._cancel).grid(
            row=0, column=1
        )

        main_frame.columnconfigure(1, weight=1)

        # Focus on first entry
        lat_entry.focus()
        lat_entry.select_range(0, tk.END)

    def _ok(self):
        try:
            lat = self.lat_var.get()
            lon = self.lon_var.get()

            if not (-90 <= lat <= 90):
                messagebox.showerror(
                    "Invalid Input", "Latitude must be between -90 and 90"
                )
                return

            if not (-180 <= lon <= 180):
                messagebox.showerror(
                    "Invalid Input", "Longitude must be between -180 and 180"
                )
                return

            self.result = (lat, lon)
            self.dialog.destroy()

        except tk.TclError:
            messagebox.showerror(
                "Invalid Input", "Please enter valid numeric coordinates"
            )

    def _cancel(self):
        self.dialog.destroy()
