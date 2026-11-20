"""
GarmentPulse — Preprocessing Module
====================================

Data profiling, validation, and cleaning pipeline for the GarmentPulse
retail fashion analytics platform.

Submodules
----------
data_profiler
    Statistical profiling and audit report generation for transactions,
    articles, and customers tables.
data_validator
    Rule-based data-quality checks including null detection, range
    validation, format verification, and referential-integrity tests.
data_cleaner
    Transparent, documented cleaning operations.  Every transformation
    is logged so the Data Quality dashboard can surface exactly what
    was changed and why.
"""

from . import data_profiler
from . import data_validator
from . import data_cleaner

__all__ = [
    "data_profiler",
    "data_validator",
    "data_cleaner",
]
