import pandas as pd


def parse_estate(estate):
    """
    Parse the estate name into BOROUGH, SECTOR and SEGMENT.

    This preserves the same parsing logic used in anna2.0.py.
    """

    parts = estate.upper().split()

    if len(parts) == 4:
        return (
            parts[0],
            parts[1] + " " + parts[2],
            parts[3],
        )

    if len(parts) == 3:
        return tuple(parts)

    raise ValueError("Invalid format of estate entry.")


def search_chunk(chunk, match):
    """
    Search one CSV chunk for the requested estate.
    """

    return chunk[
        (chunk["BOROUGH"] == match[0])
        & (chunk["SECTOR"] == match[1])
        & (chunk["SEGMENT"] == match[2])
    ]


def sequential_search(csv_file, match):
    """
    Search estates.csv in chunks and return matching row indices.
    """

    iterator = pd.read_csv(
        csv_file,
        chunksize=10000,
    )

    results = []

    for chunk in iterator:
        chunk_result = search_chunk(
            chunk,
            match,
        )

        results.append(chunk_result)

    result_df = pd.concat(results)

    if not result_df.empty:
        return result_df.index.values

    return None


def select_site_source(
    estate,
    custom_polygon=None,
):
    """
    Decide whether the site comes from an estate lookup
    or from a custom polygon.

    Returns
    -------
    dict
        Description of the selected source.
    """

    if estate and estate.strip():
        return {
            "type": "estate",
            "estate": estate,
        }

    if custom_polygon is not None:
        return {
            "type": "custom_polygon",
            "polygon": custom_polygon,
        }

    raise ValueError(
        "No estate or custom polygon supplied."
    )