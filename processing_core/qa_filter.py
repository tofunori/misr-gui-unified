"""
QA Filter Module
Handles MISR Quality Assurance flag processing and filtering.
"""

import numpy as np
import xarray as xr
from typing import Dict, List, Optional, Tuple
import logging

logger = logging.getLogger(__name__)


class QAFilter:
    """Processes MISR QA flags for data quality filtering."""

    # Common MISR QA flag definitions (bit positions and meanings)
    QA_FLAGS = {
        "cloud_detected": {"bit": 0, "valid_values": [0]},
        "clear_sky": {"bit": 1, "valid_values": [1]},
        "high_quality": {"bit": 2, "valid_values": [1]},
        "shadow_detected": {"bit": 3, "valid_values": [0]},
        "snow_ice": {"bit": 4, "valid_values": [0, 1]},  # Both valid depending on use
        "water_detected": {"bit": 5, "valid_values": [0, 1]},  # Both valid
        "retrieval_quality": {"bit_range": (6, 7), "valid_values": [0, 1, 2]},
    }

    def __init__(self, qa_dataset: Optional[xr.Dataset] = None):
        """Initialize QA filter with optional QA dataset."""
        self.qa_dataset = qa_dataset
        self.enabled_filters = []
        self.custom_flags = {}

    def set_qa_dataset(self, qa_dataset: xr.Dataset):
        """Set the QA dataset for processing."""
        self.qa_dataset = qa_dataset
        logger.info("QA dataset loaded for filtering")

    def add_filter(self, flag_name: str, enabled: bool = True):
        """Add or remove a QA filter."""
        if enabled and flag_name not in self.enabled_filters:
            if flag_name in self.QA_FLAGS or flag_name in self.custom_flags:
                self.enabled_filters.append(flag_name)
                logger.info(f"Enabled QA filter: {flag_name}")
            else:
                logger.warning(f"Unknown QA flag: {flag_name}")
        elif not enabled and flag_name in self.enabled_filters:
            self.enabled_filters.remove(flag_name)
            logger.info(f"Disabled QA filter: {flag_name}")

    def add_custom_flag(
        self,
        flag_name: str,
        bit_position: int,
        valid_values: List[int],
        description: str = "",
    ):
        """Add custom QA flag definition."""
        self.custom_flags[flag_name] = {
            "bit": bit_position,
            "valid_values": valid_values,
            "description": description,
        }
        logger.info(f"Added custom QA flag: {flag_name}")

    def extract_bit_values(self, qa_data: np.ndarray, bit_position: int) -> np.ndarray:
        """Extract specific bit from QA integer values."""
        return (qa_data >> bit_position) & 1

    def extract_bit_range(
        self, qa_data: np.ndarray, bit_range: Tuple[int, int]
    ) -> np.ndarray:
        """Extract bit range from QA integer values."""
        start_bit, end_bit = bit_range
        num_bits = end_bit - start_bit + 1
        mask = (1 << num_bits) - 1
        return (qa_data >> start_bit) & mask

    def create_quality_mask(self, qa_data: np.ndarray) -> np.ndarray:
        """Create combined quality mask from enabled filters."""
        if not self.enabled_filters:
            logger.warning("No QA filters enabled, returning all-valid mask")
            return np.ones_like(qa_data, dtype=bool)

        combined_mask = np.ones_like(qa_data, dtype=bool)

        for flag_name in self.enabled_filters:
            # Get flag definition
            if flag_name in self.QA_FLAGS:
                flag_def = self.QA_FLAGS[flag_name]
            elif flag_name in self.custom_flags:
                flag_def = self.custom_flags[flag_name]
            else:
                logger.warning(f"Skipping unknown flag: {flag_name}")
                continue

            # Extract bit values
            if "bit" in flag_def:
                bit_values = self.extract_bit_values(qa_data, flag_def["bit"])
            elif "bit_range" in flag_def:
                bit_values = self.extract_bit_range(qa_data, flag_def["bit_range"])
            else:
                logger.warning(f"Invalid flag definition for {flag_name}")
                continue

            # Create mask for valid values
            valid_values = flag_def["valid_values"]
            flag_mask = np.isin(bit_values, valid_values)

            # Combine with overall mask
            combined_mask &= flag_mask

            logger.debug(
                f"Flag {flag_name}: {np.sum(flag_mask)} valid pixels "
                f"({np.sum(flag_mask)/flag_mask.size*100:.1f}%)"
            )

        valid_pixels = np.sum(combined_mask)
        total_pixels = combined_mask.size
        logger.info(
            f"Combined QA mask: {valid_pixels}/{total_pixels} valid pixels "
            f"({valid_pixels/total_pixels*100:.1f}%)"
        )

        return combined_mask

    def apply_qa_filter(self, data: np.ndarray, qa_data: np.ndarray) -> np.ndarray:
        """Apply QA filtering to data array."""
        if qa_data.shape != data.shape:
            logger.warning(
                f"QA shape {qa_data.shape} doesn't match data shape {data.shape}"
            )
            # Try to handle different resolutions
            if qa_data.size == data.size:
                qa_data = qa_data.reshape(data.shape)
            else:
                logger.error("Cannot align QA data with input data")
                return data

        quality_mask = self.create_quality_mask(qa_data)
        filtered_data = data.copy()
        filtered_data[~quality_mask] = np.nan

        masked_pixels = np.sum(~quality_mask)
        logger.info(f"QA filtering masked {masked_pixels} pixels")

        return filtered_data

    def get_qa_statistics(self, qa_data: np.ndarray) -> Dict[str, any]:
        """Get statistics for all QA flags."""
        stats = {"total_pixels": qa_data.size}

        # Analyze each flag
        for flag_name, flag_def in {**self.QA_FLAGS, **self.custom_flags}.items():
            try:
                if "bit" in flag_def:
                    bit_values = self.extract_bit_values(qa_data, flag_def["bit"])
                elif "bit_range" in flag_def:
                    bit_values = self.extract_bit_range(qa_data, flag_def["bit_range"])
                else:
                    continue

                # Count each value
                unique_values, counts = np.unique(bit_values, return_counts=True)
                value_stats = dict(zip(unique_values.astype(int), counts.astype(int)))

                # Calculate valid percentage
                valid_count = sum(
                    counts[unique_values == val] for val in flag_def["valid_values"]
                )
                valid_percent = (valid_count / qa_data.size) * 100

                stats[flag_name] = {
                    "values": value_stats,
                    "valid_count": int(valid_count),
                    "valid_percent": float(valid_percent),
                }

            except Exception as e:
                logger.warning(f"Failed to analyze flag {flag_name}: {e}")

        return stats

    def get_enabled_filters(self) -> List[str]:
        """Get list of currently enabled filters."""
        return self.enabled_filters.copy()

    def clear_filters(self):
        """Clear all enabled filters."""
        self.enabled_filters.clear()
        logger.info("Cleared all QA filters")

    def get_available_flags(self) -> Dict[str, Dict]:
        """Get all available QA flag definitions."""
        return {**self.QA_FLAGS, **self.custom_flags}
