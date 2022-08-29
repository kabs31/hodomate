import re


def _is_depth_column(col_name, pattern) -> bool:
    return bool(re.search(pattern, col_name))