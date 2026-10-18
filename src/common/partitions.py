from collections.abc import Callable
from datetime import date
from pathlib import Path

from helpers.date_ranges import iter_month_ranges


def load_monthly_partitions(
    start_date: date,
    end_date: date,
    *,
    path_for_month: Callable[[int, int], Path],
    load_partition: Callable[[Path], int],
    name: str,
) -> int:
    """Load every monthly partition in an inclusive date range."""
    loaded_rows = 0
    for month_start, _ in iter_month_ranges(start_date, end_date):
        partition_path = path_for_month(month_start.year, month_start.month)
        if not partition_path.is_file():
            raise FileNotFoundError(
                f"Silver {name} partition does not exist: {partition_path}"
            )
        loaded_rows += load_partition(partition_path)
    return loaded_rows
