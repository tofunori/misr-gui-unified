"""
Progress Panel Module
Displays processing progress, logs, and results.
"""

import tkinter as tk
from tkinter import ttk, scrolledtext
from typing import Dict, Any, Optional
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class ProgressPanel:
    """Panel for displaying processing progress and logs."""

    def __init__(self, parent):
        """Initialize progress panel."""
        self.parent = parent
        self.frame = ttk.LabelFrame(parent, text="Progress & Results", padding="5")
        self._setup_ui()

    def _setup_ui(self):
        """Create progress panel UI components."""
        # Configure frame grid weights
        self.frame.columnconfigure(0, weight=1)
        self.frame.rowconfigure(1, weight=1)

        # Progress bar and status
        progress_frame = ttk.Frame(self.frame)
        progress_frame.grid(row=0, column=0, sticky="ew", pady=(0, 5))
        progress_frame.columnconfigure(1, weight=1)

        ttk.Label(progress_frame, text="Progress:").grid(row=0, column=0, sticky="w")

        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(
            progress_frame, variable=self.progress_var, maximum=100, mode="determinate"
        )
        self.progress_bar.grid(row=0, column=1, sticky="ew", padx=(5, 5))

        self.progress_label = ttk.Label(progress_frame, text="Ready")
        self.progress_label.grid(row=0, column=2, sticky="e")

        # Current operation status
        self.status_label = ttk.Label(
            progress_frame, text="", font=("TkDefaultFont", 8)
        )
        self.status_label.grid(row=1, column=0, columnspan=3, sticky="w", pady=(2, 0))

        # Notebook for logs and results
        self.notebook = ttk.Notebook(self.frame)
        self.notebook.grid(row=1, column=0, sticky="nsew", pady=(5, 0))

        # Log tab
        self._create_log_tab()

        # Results tab
        self._create_results_tab()

        # Statistics tab
        self._create_stats_tab()

    def _create_log_tab(self):
        """Create logging tab."""
        log_frame = ttk.Frame(self.notebook)
        self.notebook.add(log_frame, text="Log")
        log_frame.columnconfigure(0, weight=1)
        log_frame.rowconfigure(0, weight=1)

        # Log text area with scrollbar
        self.log_text = scrolledtext.ScrolledText(
            log_frame,
            height=15,
            width=50,
            font=("Consolas", 9),
            state="disabled",
            wrap=tk.WORD,
        )
        self.log_text.grid(row=0, column=0, sticky="nsew", pady=(0, 5))

        # Log controls
        log_controls = ttk.Frame(log_frame)
        log_controls.grid(row=1, column=0, sticky="ew")

        ttk.Button(log_controls, text="Clear Log", command=self.clear_log).grid(
            row=0, column=0, sticky="w"
        )

        ttk.Button(log_controls, text="Save Log...", command=self.save_log).grid(
            row=0, column=1, padx=(10, 0)
        )

        # Auto-scroll option
        self.auto_scroll_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(
            log_controls, text="Auto-scroll", variable=self.auto_scroll_var
        ).grid(row=0, column=2, padx=(10, 0))

    def _create_results_tab(self):
        """Create results tab."""
        results_frame = ttk.Frame(self.notebook)
        self.notebook.add(results_frame, text="Results")
        results_frame.columnconfigure(0, weight=1)
        results_frame.rowconfigure(0, weight=1)

        # Results tree view
        columns = ("file", "status", "time", "output")
        self.results_tree = ttk.Treeview(
            results_frame, columns=columns, show="tree headings", height=15
        )
        self.results_tree.grid(row=0, column=0, sticky="nsew", pady=(0, 5))

        # Configure columns
        self.results_tree.heading("#0", text="Index")
        self.results_tree.heading("file", text="Input File")
        self.results_tree.heading("status", text="Status")
        self.results_tree.heading("time", text="Time (s)")
        self.results_tree.heading("output", text="Output Files")

        self.results_tree.column("#0", width=50, minwidth=50)
        self.results_tree.column("file", width=200, minwidth=100)
        self.results_tree.column("status", width=80, minwidth=60)
        self.results_tree.column("time", width=60, minwidth=50)
        self.results_tree.column("output", width=150, minwidth=100)

        # Vertical scrollbar for results
        results_scrollbar = ttk.Scrollbar(
            results_frame, command=self.results_tree.yview
        )
        results_scrollbar.grid(row=0, column=1, sticky="ns")
        self.results_tree.configure(yscrollcommand=results_scrollbar.set)

        # Results controls
        results_controls = ttk.Frame(results_frame)
        results_controls.grid(row=1, column=0, columnspan=2, sticky="ew")

        ttk.Button(
            results_controls, text="Clear Results", command=self.clear_results
        ).grid(row=0, column=0, sticky="w")

        ttk.Button(
            results_controls, text="Export Results...", command=self.export_results
        ).grid(row=0, column=1, padx=(10, 0))

        ttk.Button(
            results_controls, text="Open Output Folder", command=self.open_output_folder
        ).grid(row=0, column=2, padx=(10, 0))

    def _create_stats_tab(self):
        """Create statistics tab."""
        stats_frame = ttk.Frame(self.notebook)
        self.notebook.add(stats_frame, text="Statistics")
        stats_frame.columnconfigure(0, weight=1)
        stats_frame.rowconfigure(0, weight=1)

        # Statistics text area
        self.stats_text = scrolledtext.ScrolledText(
            stats_frame,
            height=15,
            width=50,
            font=("Consolas", 9),
            state="disabled",
            wrap=tk.WORD,
        )
        self.stats_text.grid(row=0, column=0, sticky="nsew")

    def update_progress(self, progress: float, message: str = ""):
        """Update progress bar and message."""
        self.progress_var.set(progress * 100)
        self.progress_label.config(text=f"{progress*100:.1f}%")

        if message:
            self.status_label.config(text=message)

        # Force update
        self.frame.update_idletasks()

    def add_log_message(self, message: str, level: str = "INFO"):
        """Add message to log."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        formatted_message = f"[{timestamp}] {level}: {message}\n"

        self.log_text.configure(state="normal")
        self.log_text.insert(tk.END, formatted_message)
        self.log_text.configure(state="disabled")

        # Auto-scroll if enabled
        if self.auto_scroll_var.get():
            self.log_text.see(tk.END)

    def add_result(
        self,
        filename: str,
        success: bool,
        processing_time: float,
        output_files: Dict[str, str],
        error_message: Optional[str] = None,
    ):
        """Add processing result to results tree."""
        # Determine status
        status = "Success" if success else "Failed"

        # Format output files
        if output_files:
            output_summary = ", ".join(output_files.keys())
        else:
            output_summary = error_message or "No output"

        # Insert into tree
        item_index = len(self.results_tree.get_children()) + 1
        item = self.results_tree.insert(
            "",
            tk.END,
            text=str(item_index),
            values=(filename, status, f"{processing_time:.1f}", output_summary),
        )

        # Color code by status
        if success:
            self.results_tree.set(item, "status", "✓ Success")
        else:
            self.results_tree.set(item, "status", "✗ Failed")

    def show_summary(self, summary: Dict[str, Any]):
        """Display processing summary."""
        # Update statistics tab
        stats_text = self._format_summary(summary)

        self.stats_text.configure(state="normal")
        self.stats_text.delete(1.0, tk.END)
        self.stats_text.insert(1.0, stats_text)
        self.stats_text.configure(state="disabled")

        # Switch to statistics tab
        self.notebook.select(2)

    def _format_summary(self, summary: Dict[str, Any]) -> str:
        """Format summary for display."""
        lines = [
            "PROCESSING SUMMARY",
            "=" * 50,
            "",
            f"Total files: {summary['total_files']}",
            f"Successful: {summary['successful']}",
            f"Failed: {summary['failed']}",
            f"Success rate: {summary['success_rate']:.1f}%",
            "",
            f"Total processing time: {summary['total_processing_time']:.1f} seconds",
            f"Average time per file: {summary['average_processing_time']:.1f} seconds",
            "",
        ]

        # Export summary
        if "export_summary" in summary:
            export_summary = summary["export_summary"]
            lines.extend(
                [
                    "EXPORT SUMMARY",
                    "-" * 30,
                    f"Total output size: {export_summary['total_size_mb']:.1f} MB",
                    "",
                ]
            )

            for format_name, file_info in export_summary["files"].items():
                if file_info["exists"]:
                    lines.append(f"{format_name}: {file_info['size_mb']:.1f} MB")
                else:
                    lines.append(f"{format_name}: Failed")

            lines.append("")

        # Error summary
        if "error_summary" in summary:
            lines.extend(
                [
                    "ERROR SUMMARY",
                    "-" * 30,
                ]
            )

            for error, count in summary["error_summary"].items():
                lines.append(f"{error}: {count} occurrences")

        return "\n".join(lines)

    def reset(self):
        """Reset progress and clear current operation status."""
        self.progress_var.set(0)
        self.progress_label.config(text="0%")
        self.status_label.config(text="")

    def clear(self):
        """Clear all progress, logs, and results."""
        self.reset()
        self.clear_log()
        self.clear_results()
        self.clear_stats()

    def clear_log(self):
        """Clear log messages."""
        self.log_text.configure(state="normal")
        self.log_text.delete(1.0, tk.END)
        self.log_text.configure(state="disabled")

    def clear_results(self):
        """Clear results tree."""
        for item in self.results_tree.get_children():
            self.results_tree.delete(item)

    def clear_stats(self):
        """Clear statistics."""
        self.stats_text.configure(state="normal")
        self.stats_text.delete(1.0, tk.END)
        self.stats_text.configure(state="disabled")

    def save_log(self):
        """Save log to file."""
        from tkinter import filedialog

        filename = filedialog.asksaveasfilename(
            title="Save Log",
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")],
        )

        if filename:
            try:
                log_content = self.log_text.get(1.0, tk.END)
                with open(filename, "w") as f:
                    f.write(log_content)
                self.add_log_message(f"Log saved to {filename}")
            except Exception as e:
                self.add_log_message(f"Failed to save log: {e}", "ERROR")

    def export_results(self):
        """Export results to CSV file."""
        from tkinter import filedialog
        import csv

        filename = filedialog.asksaveasfilename(
            title="Export Results",
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
        )

        if filename:
            try:
                with open(filename, "w", newline="") as f:
                    writer = csv.writer(f)

                    # Write header
                    writer.writerow(
                        [
                            "Index",
                            "Input File",
                            "Status",
                            "Processing Time (s)",
                            "Output Files",
                        ]
                    )

                    # Write data
                    for item in self.results_tree.get_children():
                        values = [self.results_tree.item(item)["text"]] + list(
                            self.results_tree.item(item)["values"]
                        )
                        writer.writerow(values)

                self.add_log_message(f"Results exported to {filename}")
            except Exception as e:
                self.add_log_message(f"Failed to export results: {e}", "ERROR")

    def open_output_folder(self):
        """Open output folder in file manager."""
        import subprocess
        import platform

        # Try to get output directory from results
        output_dir = "."  # Default to current directory

        try:
            if platform.system() == "Windows":
                subprocess.run(["explorer", output_dir])
            elif platform.system() == "Darwin":  # macOS
                subprocess.run(["open", output_dir])
            else:  # Linux
                subprocess.run(["xdg-open", output_dir])

            self.add_log_message(f"Opened output folder: {output_dir}")
        except Exception as e:
            self.add_log_message(f"Failed to open output folder: {e}", "ERROR")

    def set_current_file(self, filename: str, current: int, total: int):
        """Update current file being processed."""
        self.status_label.config(text=f"Processing {current}/{total}: {filename}")

    def get_log_content(self) -> str:
        """Get current log content."""
        return self.log_text.get(1.0, tk.END)

    def get_results_count(self) -> int:
        """Get number of results."""
        return len(self.results_tree.get_children())

    def get_results_summary(self) -> Dict[str, int]:
        """Get summary of results."""
        total = 0
        successful = 0
        failed = 0

        for item in self.results_tree.get_children():
            total += 1
            status = self.results_tree.item(item)["values"][1]
            if "Success" in status:
                successful += 1
            else:
                failed += 1

        return {
            "total": total,
            "successful": successful,
            "failed": failed,
            "success_rate": (successful / total * 100) if total > 0 else 0,
        }
