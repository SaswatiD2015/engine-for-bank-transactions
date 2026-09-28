"""
Data Pipeline
==============
Orchestrates the end-to-end batch data pipeline from raw file
to analysis-ready data.
Architecture §5 — Data Pipeline Architecture (Stages 1-10)
"""

import os
import sys
import logging
from dataclasses import dataclass, field
from typing import Optional

import pandas as pd

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.ingestion.loader import load_data, LoadResult
from src.ingestion.schema_validator import validate_schema, coerce_types, ValidationReport
from src.cleaning.dedupe import remove_duplicates, DedupeResult
from src.cleaning.null_handler import handle_null_and_invalid, CleaningResult
from src.cleaning.normalizer import normalize_data, NormalizationResult
from src.analytics.derived_fields import add_derived_fields

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)


@dataclass
class PipelineResult:
    """Complete result of the pipeline run."""
    data: pd.DataFrame
    quarantined: pd.DataFrame
    load_result: Optional[LoadResult] = None
    validation_report: Optional[ValidationReport] = None
    dedupe_result: Optional[DedupeResult] = None
    cleaning_result: Optional[CleaningResult] = None
    normalization_result: Optional[NormalizationResult] = None
    pipeline_summary: dict = field(default_factory=dict)
    success: bool = True
    error_message: Optional[str] = None


def run_pipeline(file_path: str, max_valid_date: str = None) -> PipelineResult:
    """
    Execute the complete data pipeline.

    Stages (Architecture §5.1):
    1. Ingest raw file → raw DataFrame
    2. Validate schema → validated DataFrame + report
    3. Clean (null/invalid handling) → cleaned DataFrame
    4. Normalize categoricals → normalized DataFrame
    5. Deduplicate → deduplicated DataFrame
    6. Derive fields → +date parts, amount_band, absolute_amount

    Each stage records: input row count, output row count, excluded row count.

    Parameters
    ----------
    file_path : str
        Path to the raw data file (CSV or Excel).
    max_valid_date : str, optional
        Maximum valid transaction date.

    Returns
    -------
    PipelineResult
        Complete pipeline result with all intermediate data.
    """
    summary = {}

    # ── Stage 1: Ingest ─────────────────────────────────────────────
    logger.info("Stage 1: Ingesting data from %s", file_path)
    load_result = load_data(file_path)

    if not load_result.success:
        return PipelineResult(
            data=pd.DataFrame(),
            quarantined=pd.DataFrame(),
            load_result=load_result,
            success=False,
            error_message=f"Load failed: {load_result.error_message}",
        )

    df = load_result.data
    summary["stage_1_ingest"] = {"rows": len(df), "columns": len(df.columns)}
    logger.info("  Loaded %d rows, %d columns", len(df), len(df.columns))

    # ── Stage 2: Validate Schema ────────────────────────────────────
    logger.info("Stage 2: Validating schema")
    validation_report = validate_schema(df)
    logger.info("  Validation: %s", "PASSED" if validation_report.is_valid else "FAILED")

    if not validation_report.is_valid:
        return PipelineResult(
            data=pd.DataFrame(),
            quarantined=pd.DataFrame(),
            load_result=load_result,
            validation_report=validation_report,
            success=False,
            error_message=f"Schema validation failed. {validation_report.summary()}",
        )

    # Coerce types
    df = coerce_types(df)
    summary["stage_2_validate"] = {"issues": len(validation_report.issues)}

    # ── Stage 3: Clean (Null/Invalid Handling) ──────────────────────
    logger.info("Stage 3: Cleaning null/invalid values")
    cleaning_result = handle_null_and_invalid(df, max_valid_date=max_valid_date)
    df = cleaning_result.data
    summary["stage_3_clean"] = cleaning_result.cleaning_summary
    logger.info("  Cleaned: %d rows remaining, %d quarantined",
                len(df), len(cleaning_result.quarantined))

    # ── Stage 4: Normalize Categoricals ─────────────────────────────
    logger.info("Stage 4: Normalizing categorical values")
    normalization_result = normalize_data(df)
    df = normalization_result.data
    summary["stage_4_normalize"] = normalization_result.normalization_summary
    logger.info("  Normalized: %s", normalization_result.normalization_summary)

    # ── Stage 5: Deduplicate ────────────────────────────────────────
    logger.info("Stage 5: Removing duplicates")
    dedupe_result = remove_duplicates(df)
    df = dedupe_result.data
    summary["stage_5_dedupe"] = {
        "duplicate_ids": dedupe_result.duplicate_id_count,
        "exact_duplicates": dedupe_result.exact_duplicate_count,
        "total_removed": dedupe_result.total_removed,
    }
    logger.info("  Removed %d duplicates (%d ID dupes, %d exact dupes)",
                dedupe_result.total_removed,
                dedupe_result.duplicate_id_count,
                dedupe_result.exact_duplicate_count)

    # ── Stage 6: Derive Fields ──────────────────────────────────────
    logger.info("Stage 6: Adding derived fields")
    df = add_derived_fields(df)
    summary["stage_6_derive"] = {"output_rows": len(df), "output_columns": len(df.columns)}
    logger.info("  Derived: %d rows, %d columns", len(df), len(df.columns))

    # Combine quarantined records
    all_quarantined = pd.concat(
        [cleaning_result.quarantined, dedupe_result.duplicate_ids],
        ignore_index=True
    )

    summary["final"] = {
        "clean_rows": len(df),
        "quarantined_rows": len(all_quarantined),
        "total_columns": len(df.columns),
    }

    logger.info("Pipeline complete: %d clean rows, %d quarantined",
                len(df), len(all_quarantined))

    return PipelineResult(
        data=df,
        quarantined=all_quarantined,
        load_result=load_result,
        validation_report=validation_report,
        dedupe_result=dedupe_result,
        cleaning_result=cleaning_result,
        normalization_result=normalization_result,
        pipeline_summary=summary,
        success=True,
    )
