"""
Main Window Module
Primary Tkinter interface for MISR processing application.
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import threading
import queue
import logging
from pathlib import Path
from typing import List, Optional

import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))
from processing_core import BatchProcessor, ProcessingConfig, ProcessingResult
from .file_panel import FilePanel
from .config_panel import ConfigPanel
from .progress_panel import ProgressPanel

logger = logging.getLogger(__name__)


class MainWindow:
    """Main application window for MISR processing."""

    def __init__(self):
        """Initialize main window and components."""
        self.root = tk.Tk()
        self.root.title("MISR Data Processing Tool")
        self.root.geometry("800x600")
        self.root.minsize(700, 500)

        # Processing components
        self.batch_processor: Optional[BatchProcessor] = None
        self.processing_thread: Optional[threading.Thread] = None
        self.progress_queue = queue.Queue()
        self.is_processing = False

        # Setup UI
        self._setup_ui()
        self._setup_logging()
        self._start_progress_monitor()

        logger.info("MISR GUI application initialized")

    def _setup_ui(self):
        """Create and layout UI components."""
        # Main container with padding
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky="nsew")

        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(1, weight=1)

        # Create panels
        self.file_panel = FilePanel(main_frame, self._on_files_changed)
        self.config_panel = ConfigPanel(main_frame, self._on_config_changed)
        self.progress_panel = ProgressPanel(main_frame)

        # Layout panels
        self.file_panel.frame.grid(
            row=0, column=0, columnspan=2, sticky="ew", pady=(0, 10)
        )
        self.config_panel.frame.grid(row=1, column=0, sticky="nsew", padx=(0, 5))
        self.progress_panel.frame.grid(row=1, column=1, sticky="nsew", padx=(5, 0))

        # Control buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=2, column=0, columnspan=2, sticky="ew", pady=(10, 0))
        button_frame.columnconfigure(0, weight=1)

        self.process_button = ttk.Button(
            button_frame,
            text="Start Processing",
            command=self._start_processing,
            state="disabled",
        )
        self.process_button.grid(row=0, column=0, sticky="w")

        self.stop_button = ttk.Button(
            button_frame, text="Stop", command=self._stop_processing, state="disabled"
        )
        self.stop_button.grid(row=0, column=1, padx=(10, 0))

        self.clear_button = ttk.Button(
            button_frame, text="Clear Results", command=self._clear_results
        )
        self.clear_button.grid(row=0, column=2, padx=(10, 0))

        # Status bar
        self.status_var = tk.StringVar(value="Ready")
        status_bar = ttk.Label(
            main_frame, textvariable=self.status_var, relief="sunken"
        )
        status_bar.grid(row=3, column=0, columnspan=2, sticky="ew", pady=(10, 0))

        # Menu bar
        self._create_menu()

    def _create_menu(self):
        """Create application menu bar."""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)

        # File menu
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Add Files...", command=self.file_panel.add_files)
        file_menu.add_command(label="Clear Files", command=self.file_panel.clear_files)
        file_menu.add_separator()
        file_menu.add_command(label="Save Configuration...", command=self._save_config)
        file_menu.add_command(label="Load Configuration...", command=self._load_config)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.root.quit)

        # Tools menu
        tools_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Tools", menu=tools_menu)
        tools_menu.add_command(label="Validate Files", command=self._validate_files)
        tools_menu.add_command(label="Test Configuration", command=self._test_config)

        # Help menu
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Help", menu=help_menu)
        help_menu.add_command(label="About", command=self._show_about)

    def _setup_logging(self):
        """Setup logging to display in progress panel."""
        log_handler = ProgressLogHandler(self.progress_panel.add_log_message)
        log_handler.setLevel(logging.INFO)
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        log_handler.setFormatter(formatter)

        # Add to processing core loggers
        for logger_name in [
            "processing_core.batch_processor",
            "processing_core.data_loader",
            "processing_core.reprojector",
            "processing_core.exporter",
        ]:
            logging.getLogger(logger_name).addHandler(log_handler)

    def _start_progress_monitor(self):
        """Start monitoring progress updates from processing thread."""

        def check_progress():
            try:
                while True:
                    message, progress, current, total = self.progress_queue.get_nowait()
                    self.progress_panel.update_progress(progress, message)
                    self.status_var.set(f"Processing {current}/{total}: {message}")
            except queue.Empty:
                pass

            # Schedule next check
            self.root.after(100, check_progress)

        check_progress()

    def _on_files_changed(self, files: List[str]):
        """Handle file selection changes."""
        self._update_process_button()
        self.status_var.set(f"{len(files)} files selected")

    def _on_config_changed(self, config):
        """Handle configuration changes."""
        # Create appropriate processor based on config type
        if isinstance(config, dict) and config.get("processing_mode") == "hdf":
            # Import HDF adapter
            from processing_hdf import MISRProcessingAdapter

            self.batch_processor = MISRProcessingAdapter(config)
        else:
            # NetCDF processing with original BatchProcessor
            self.batch_processor = BatchProcessor(config)

        self._update_process_button()
        logger.info(
            f"Configuration updated for {config.get('processing_mode', 'netcdf') if isinstance(config, dict) else 'netcdf'} mode"
        )

    def _update_process_button(self):
        """Update process button state based on files and config."""
        if not hasattr(self, "process_button"):
            return  # UI not fully initialized yet

        files = self.file_panel.get_files()
        has_config = self.batch_processor is not None
        can_process = len(files) > 0 and has_config and not self.is_processing

        self.process_button.config(state="normal" if can_process else "disabled")

    def _start_processing(self):
        """Start processing in background thread."""
        if self.is_processing:
            return

        files = self.file_panel.get_files()
        if not files:
            messagebox.showwarning("No Files", "Please select files to process")
            return

        if not self.batch_processor:
            messagebox.showerror(
                "No Configuration", "Please configure processing settings"
            )
            return

        # Validate inputs
        try:
            validation = self.batch_processor.validate_inputs(files)
            if validation["invalid_files"]:
                invalid_msg = "\n".join(validation["invalid_files"])
                if not messagebox.askyesno(
                    "Invalid Files Found",
                    f"Some files are invalid:\n{invalid_msg}\n\nContinue with valid files?",
                ):
                    return
                files = validation["valid_files"]

            if validation["warnings"]:
                warning_msg = "\n".join(validation["warnings"])
                if not messagebox.askyesno(
                    "Configuration Warnings",
                    f"Configuration warnings:\n{warning_msg}\n\nContinue anyway?",
                ):
                    return

        except Exception as e:
            messagebox.showerror("Validation Error", f"Failed to validate inputs: {e}")
            return

        # Start processing
        self.is_processing = True
        self.process_button.config(state="disabled")
        self.stop_button.config(state="normal")
        self.progress_panel.reset()

        def progress_callback(message: str, progress: float, current: int, total: int):
            self.progress_queue.put((message, progress, current, total))

        self.processing_thread = threading.Thread(
            target=self._process_files, args=(files, progress_callback), daemon=True
        )
        self.processing_thread.start()

    def _process_files(self, files: List[str], progress_callback):
        """Process files in background thread."""
        try:
            logger.info(f"Starting batch processing of {len(files)} files")
            results = self.batch_processor.process_batch(files, progress_callback)

            # Show results
            self.root.after(0, lambda: self._show_results(results))

        except Exception as e:
            logger.error(f"Processing failed: {e}")
            error_message = str(e)
            self.root.after(
                0, lambda: messagebox.showerror("Processing Error", error_message)
            )

        finally:
            self.root.after(0, self._processing_complete)

    def _stop_processing(self):
        """Stop current processing."""
        # Note: This is a simple implementation. For proper cancellation,
        # you'd need to implement thread-safe cancellation in BatchProcessor
        if self.processing_thread and self.processing_thread.is_alive():
            logger.warning("Processing stop requested (note: may not stop immediately)")
            self.status_var.set("Stopping processing...")

    def _processing_complete(self):
        """Handle processing completion."""
        self.is_processing = False
        self.process_button.config(state="normal")
        self.stop_button.config(state="disabled")
        self._update_process_button()
        self.status_var.set("Processing complete")

    def _show_results(self, results: List[ProcessingResult]):
        """Display processing results."""
        if not self.batch_processor:
            return

        summary = self.batch_processor.get_processing_summary(results)

        # Update progress panel with summary
        self.progress_panel.show_summary(summary)

        # Show summary dialog
        success_count = summary["successful"]
        total_count = summary["total_files"]
        success_rate = summary["success_rate"]

        message = (
            f"Processing Complete!\n\n"
            f"Successful: {success_count}/{total_count} ({success_rate:.1f}%)\n"
            f"Total time: {summary['total_processing_time']:.1f}s\n"
            f"Average time: {summary['average_processing_time']:.1f}s per file"
        )

        if success_count > 0:
            messagebox.showinfo("Processing Complete", message)
        else:
            messagebox.showerror("Processing Failed", "No files processed successfully")

    def _clear_results(self):
        """Clear processing results and logs."""
        self.progress_panel.clear()
        self.status_var.set("Ready")

    def _validate_files(self):
        """Validate selected files."""
        files = self.file_panel.get_files()
        if not files:
            messagebox.showwarning("No Files", "Please select files to validate")
            return

        if not self.batch_processor:
            messagebox.showwarning(
                "No Configuration", "Please configure settings first"
            )
            return

        try:
            validation = self.batch_processor.validate_inputs(files)

            valid_count = len(validation["valid_files"])
            invalid_count = len(validation["invalid_files"])
            warning_count = len(validation["warnings"])

            message = f"Validation Results:\n\nValid files: {valid_count}\nInvalid files: {invalid_count}\nWarnings: {warning_count}"

            if invalid_count > 0:
                message += f"\n\nInvalid files:\n" + "\n".join(
                    validation["invalid_files"][:5]
                )
                if invalid_count > 5:
                    message += f"\n... and {invalid_count - 5} more"

            if warning_count > 0:
                message += f"\n\nWarnings:\n" + "\n".join(validation["warnings"])

            messagebox.showinfo("Validation Results", message)

        except Exception as e:
            messagebox.showerror("Validation Error", f"Failed to validate files: {e}")

    def _test_config(self):
        """Test current configuration."""
        if not self.batch_processor:
            messagebox.showwarning(
                "No Configuration", "Please configure settings first"
            )
            return

        config = self.batch_processor.config

        # Test output directory
        if not self.batch_processor.exporter.validate_output_directory():
            messagebox.showerror(
                "Configuration Error", "Output directory is not writable"
            )
            return

        # Test shapefile if enabled
        if config.enable_clipping and config.shapefile_path:
            if not self.batch_processor.clipper.validate_shapefile(
                config.shapefile_path
            ):
                messagebox.showerror("Configuration Error", "Invalid shapefile")
                return

        messagebox.showinfo("Configuration Test", "Configuration is valid")

    def _save_config(self):
        """Save current configuration to file."""
        if not self.batch_processor:
            messagebox.showwarning("No Configuration", "No configuration to save")
            return

        filename = filedialog.asksaveasfilename(
            title="Save Configuration",
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
        )

        if filename:
            try:
                self.config_panel.save_config(filename)
                messagebox.showinfo(
                    "Save Configuration", f"Configuration saved to {filename}"
                )
            except Exception as e:
                messagebox.showerror("Save Error", f"Failed to save configuration: {e}")

    def _load_config(self):
        """Load configuration from file."""
        filename = filedialog.askopenfilename(
            title="Load Configuration",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
        )

        if filename:
            try:
                self.config_panel.load_config(filename)
                messagebox.showinfo(
                    "Load Configuration", f"Configuration loaded from {filename}"
                )
            except Exception as e:
                messagebox.showerror("Load Error", f"Failed to load configuration: {e}")

    def _show_about(self):
        """Show about dialog."""
        about_text = (
            "MISR Data Processing Tool\n\n"
            "A graphical application for processing MISR satellite data.\n\n"
            "Features:\n"
            "• Reproject MISR data to WGS84\n"
            "• Quality assurance filtering\n"
            "• Shapefile-based clipping\n"
            "• Batch processing\n"
            "• Export to NetCDF and GeoTIFF\n\n"
            "Built with Python and Tkinter"
        )
        messagebox.showinfo("About", about_text)

    def run(self):
        """Start the GUI application."""
        self.root.mainloop()

    def quit(self):
        """Quit the application."""
        if self.is_processing:
            if messagebox.askyesno("Quit", "Processing is active. Quit anyway?"):
                self.root.quit()
        else:
            self.root.quit()


class ProgressLogHandler(logging.Handler):
    """Custom log handler that sends messages to progress panel."""

    def __init__(self, callback):
        super().__init__()
        self.callback = callback

    def emit(self, record):
        try:
            msg = self.format(record)
            self.callback(msg)
        except Exception:
            self.handleError(record)
