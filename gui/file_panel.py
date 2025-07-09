"""
File Panel Module
Handles file selection and management for MISR processing.
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from pathlib import Path
from typing import List, Callable
import logging

logger = logging.getLogger(__name__)


class FilePanel:
    """Panel for managing input file selection."""

    def __init__(self, parent, callback: Callable[[List[str]], None]):
        """Initialize file panel."""
        self.parent = parent
        self.callback = callback
        self.files: List[str] = []

        self.frame = ttk.LabelFrame(parent, text="Input Files", padding="5")
        self._setup_ui()

    def _setup_ui(self):
        """Create file panel UI components."""
        # File selection buttons
        button_frame = ttk.Frame(self.frame)
        button_frame.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 5))

        ttk.Button(button_frame, text="Add Files", command=self.add_files).grid(
            row=0, column=0, padx=(0, 5)
        )

        ttk.Button(button_frame, text="Add Directory", command=self.add_directory).grid(
            row=0, column=1, padx=(0, 5)
        )

        ttk.Button(
            button_frame, text="Remove Selected", command=self.remove_selected
        ).grid(row=0, column=2, padx=(0, 5))

        ttk.Button(button_frame, text="Clear All", command=self.clear_files).grid(
            row=0, column=3
        )

        # File list with scrollbar
        list_frame = ttk.Frame(self.frame)
        list_frame.grid(row=1, column=0, columnspan=2, sticky="nsew", pady=(5, 0))
        list_frame.columnconfigure(0, weight=1)
        list_frame.rowconfigure(0, weight=1)

        # Configure frame grid weights
        self.frame.columnconfigure(0, weight=1)
        self.frame.rowconfigure(1, weight=1)

        # Listbox with scrollbars
        self.file_listbox = tk.Listbox(
            list_frame, selectmode=tk.EXTENDED, height=6, font=("Consolas", 9)
        )
        self.file_listbox.grid(row=0, column=0, sticky="nsew")

        # Vertical scrollbar
        v_scrollbar = ttk.Scrollbar(
            list_frame, orient="vertical", command=self.file_listbox.yview
        )
        v_scrollbar.grid(row=0, column=1, sticky="ns")
        self.file_listbox.configure(yscrollcommand=v_scrollbar.set)

        # Horizontal scrollbar
        h_scrollbar = ttk.Scrollbar(
            list_frame, orient="horizontal", command=self.file_listbox.xview
        )
        h_scrollbar.grid(row=1, column=0, sticky="ew")
        self.file_listbox.configure(xscrollcommand=h_scrollbar.set)

        # File count label
        self.count_label = ttk.Label(self.frame, text="0 files selected")
        self.count_label.grid(row=2, column=0, sticky="w", pady=(5, 0))

    def add_files(self):
        """Add individual files through file dialog."""
        filetypes = [
            ("NetCDF files", "*.nc"),
            ("HDF files", "*.hdf *.he5"),
            ("All MISR files", "*.nc *.hdf *.he5"),
            ("All files", "*.*"),
        ]

        filenames = filedialog.askopenfilenames(
            title="Select MISR data files", filetypes=filetypes
        )

        if filenames:
            # Filter for valid extensions
            valid_files = []
            for filename in filenames:
                if Path(filename).suffix.lower() in [".nc", ".hdf", ".he5"]:
                    valid_files.append(filename)
                else:
                    logger.warning(f"Skipping unsupported file: {filename}")

            if valid_files:
                self._add_files(valid_files)
            else:
                messagebox.showwarning("No Valid Files", "No supported files selected")

    def add_directory(self):
        """Add all supported files from a directory."""
        directory = filedialog.askdirectory(title="Select directory with MISR data")

        if directory:
            # Find all supported files
            dir_path = Path(directory)
            valid_files = []

            for pattern in ["*.nc", "*.hdf", "*.he5"]:
                valid_files.extend(dir_path.glob(pattern))

            # Include subdirectories
            for pattern in ["**/*.nc", "**/*.hdf", "**/*.he5"]:
                valid_files.extend(dir_path.glob(pattern))

            if valid_files:
                file_paths = [str(f) for f in valid_files]
                self._add_files(file_paths)
                logger.info(f"Added {len(file_paths)} files from {directory}")
            else:
                messagebox.showinfo(
                    "No Files Found", f"No supported files found in {directory}"
                )

    def _add_files(self, new_files: List[str]):
        """Add files to the list, avoiding duplicates."""
        added_count = 0
        for file_path in new_files:
            if file_path not in self.files:
                self.files.append(file_path)
                self.file_listbox.insert(tk.END, file_path)
                added_count += 1

        if added_count > 0:
            self._update_count()
            self.callback(self.files.copy())
            logger.info(f"Added {added_count} new files")
        else:
            messagebox.showinfo(
                "No New Files", "All selected files were already in the list"
            )

    def remove_selected(self):
        """Remove selected files from the list."""
        selected_indices = self.file_listbox.curselection()
        if not selected_indices:
            messagebox.showwarning("No Selection", "Please select files to remove")
            return

        # Remove in reverse order to maintain correct indices
        for index in reversed(selected_indices):
            removed_file = self.files.pop(index)
            self.file_listbox.delete(index)
            logger.debug(f"Removed file: {removed_file}")

        self._update_count()
        self.callback(self.files.copy())

    def clear_files(self):
        """Clear all files from the list."""
        if self.files:
            if messagebox.askyesno(
                "Clear Files", f"Remove all {len(self.files)} files?"
            ):
                self.files.clear()
                self.file_listbox.delete(0, tk.END)
                self._update_count()
                self.callback(self.files.copy())
                logger.info("Cleared all files")

    def get_files(self) -> List[str]:
        """Get current list of files."""
        return self.files.copy()

    def _update_count(self):
        """Update the file count label."""
        count = len(self.files)
        self.count_label.config(
            text=f"{count} file{'s' if count != 1 else ''} selected"
        )

    def validate_files(self) -> List[str]:
        """Validate that all files exist and are accessible."""
        valid_files = []
        invalid_files = []

        for file_path in self.files:
            if Path(file_path).exists():
                try:
                    # Try to open the file to check accessibility
                    with open(file_path, "rb"):
                        pass
                    valid_files.append(file_path)
                except Exception as e:
                    invalid_files.append(f"{file_path}: {e}")
                    logger.warning(f"File not accessible: {file_path} - {e}")
            else:
                invalid_files.append(f"{file_path}: File not found")
                logger.warning(f"File not found: {file_path}")

        if invalid_files:
            invalid_msg = "\n".join(invalid_files[:10])  # Show first 10
            if len(invalid_files) > 10:
                invalid_msg += f"\n... and {len(invalid_files) - 10} more"

            if messagebox.askyesno(
                "Invalid Files Found",
                f"Some files are invalid:\n\n{invalid_msg}\n\nRemove them from the list?",
            ):
                # Remove invalid files
                self.files = valid_files
                self._refresh_listbox()
                self._update_count()
                self.callback(self.files.copy())

        return valid_files

    def _refresh_listbox(self):
        """Refresh the listbox display with current files."""
        self.file_listbox.delete(0, tk.END)
        for file_path in self.files:
            self.file_listbox.insert(tk.END, file_path)

    def get_file_info(self) -> dict:
        """Get information about selected files."""
        if not self.files:
            return {"total_files": 0}

        file_sizes = []
        extensions = {}
        total_size = 0

        for file_path in self.files:
            path = Path(file_path)
            if path.exists():
                size = path.stat().st_size
                file_sizes.append(size)
                total_size += size

                ext = path.suffix.lower()
                extensions[ext] = extensions.get(ext, 0) + 1

        return {
            "total_files": len(self.files),
            "valid_files": len(file_sizes),
            "total_size_mb": total_size / (1024 * 1024),
            "extensions": extensions,
            "average_size_mb": (
                (total_size / len(file_sizes) / (1024 * 1024)) if file_sizes else 0
            ),
        }
