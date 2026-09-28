"""
Data Loader
============
Reads CSV/Excel/database transaction records into a raw DataFrame.
Records source metadata (file name, row count, load timestamp).
Architecture §4.1 — src/ingestion/loader.py
"""

import os
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

import pandas as pd


@dataclass
class SourceMetadata:
    """Metadata about the loaded data source."""
    filename: str
    file_path: str
    file_format: str
    row_count: int
    column_count: int
    columns: list
    load_timestamp: datetime
    file_size_bytes: int = 0


@dataclass
class LoadResult:
    """Result of a data load operation."""
    data: pd.DataFrame
    metadata: SourceMetadata
    success: bool
    error_message: Optional[str] = None


def load_csv(file_path: str, **kwargs) -> LoadResult:
    """
    Load a CSV file into a DataFrame with source metadata.

    Parameters
    ----------
    file_path : str
        Path to the CSV file.
    **kwargs
        Additional arguments passed to pd.read_csv.

    Returns
    -------
    LoadResult
        DataFrame with metadata, success status, and optional error message.
    """
    try:
        if not os.path.exists(file_path):
            return LoadResult(
                data=pd.DataFrame(),
                metadata=SourceMetadata(
                    filename="", file_path=file_path, file_format="csv",
                    row_count=0, column_count=0, columns=[],
                    load_timestamp=datetime.now()
                ),
                success=False,
                error_message=f"File not found: {file_path}"
            )

        df = pd.read_csv(file_path, **kwargs)
        file_size = os.path.getsize(file_path)

        metadata = SourceMetadata(
            filename=os.path.basename(file_path),
            file_path=os.path.abspath(file_path),
            file_format="csv",
            row_count=len(df),
            column_count=len(df.columns),
            columns=list(df.columns),
            load_timestamp=datetime.now(),
            file_size_bytes=file_size,
        )

        return LoadResult(data=df, metadata=metadata, success=True)

    except Exception as e:
        return LoadResult(
            data=pd.DataFrame(),
            metadata=SourceMetadata(
                filename=os.path.basename(file_path),
                file_path=file_path, file_format="csv",
                row_count=0, column_count=0, columns=[],
                load_timestamp=datetime.now()
            ),
            success=False,
            error_message=str(e)
        )


def load_excel(file_path: str, sheet_name: str = 0, **kwargs) -> LoadResult:
    """
    Load an Excel file into a DataFrame with source metadata.

    Parameters
    ----------
    file_path : str
        Path to the Excel file.
    sheet_name : str or int
        Sheet name or index to read.
    **kwargs
        Additional arguments passed to pd.read_excel.

    Returns
    -------
    LoadResult
        DataFrame with metadata, success status, and optional error message.
    """
    try:
        if not os.path.exists(file_path):
            return LoadResult(
                data=pd.DataFrame(),
                metadata=SourceMetadata(
                    filename="", file_path=file_path, file_format="excel",
                    row_count=0, column_count=0, columns=[],
                    load_timestamp=datetime.now()
                ),
                success=False,
                error_message=f"File not found: {file_path}"
            )

        df = pd.read_excel(file_path, sheet_name=sheet_name, **kwargs)
        file_size = os.path.getsize(file_path)

        metadata = SourceMetadata(
            filename=os.path.basename(file_path),
            file_path=os.path.abspath(file_path),
            file_format="excel",
            row_count=len(df),
            column_count=len(df.columns),
            columns=list(df.columns),
            load_timestamp=datetime.now(),
            file_size_bytes=file_size,
        )

        return LoadResult(data=df, metadata=metadata, success=True)

    except Exception as e:
        return LoadResult(
            data=pd.DataFrame(),
            metadata=SourceMetadata(
                filename=os.path.basename(file_path),
                file_path=file_path, file_format="excel",
                row_count=0, column_count=0, columns=[],
                load_timestamp=datetime.now()
            ),
            success=False,
            error_message=str(e)
        )


def load_data(file_path: str, **kwargs) -> LoadResult:
    """
    Auto-detect file format and load data.

    Parameters
    ----------
    file_path : str
        Path to the data file (CSV or Excel).

    Returns
    -------
    LoadResult
        Loaded data with metadata.
    """
    ext = os.path.splitext(file_path)[1].lower()

    if ext == ".csv":
        return load_csv(file_path, **kwargs)
    elif ext in (".xlsx", ".xls"):
        return load_excel(file_path, **kwargs)
    else:
        return LoadResult(
            data=pd.DataFrame(),
            metadata=SourceMetadata(
                filename=os.path.basename(file_path),
                file_path=file_path, file_format=ext,
                row_count=0, column_count=0, columns=[],
                load_timestamp=datetime.now()
            ),
            success=False,
            error_message=f"Unsupported file format: {ext}. Use CSV or Excel."
        )
