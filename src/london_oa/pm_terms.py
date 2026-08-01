"""UK Prime Minister tenure lookup, for bucketing applications by government."""

# (name, start_date inclusive or None for "since before our data starts")
PM_TERMS = [
    ("David Cameron", None),
    ("Theresa May", "2016-07-13"),
    ("Boris Johnson", "2019-07-24"),
    ("Liz Truss", "2022-09-06"),
    ("Rishi Sunak", "2022-10-25"),
    ("Keir Starmer", "2024-07-05"),
]


def pm_for_date(date_str: str) -> str:
    """Which PM was in office on a given ISO YYYY-MM-DD date."""
    current = PM_TERMS[0][0]
    for name, start in PM_TERMS:
        if start is not None and date_str < start:
            break
        current = name
    return current
