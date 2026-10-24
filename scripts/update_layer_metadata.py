import sys

from pathlib import Path


if __package__ in {
    None,
    "",
}:
    sys.path.insert(
        0,
        str(
            Path(__file__).resolve().parents[1]
        ),
    )


from scripts.layer_metadata import (
    cache_needs_refresh,
    metadata_cache_path,
    update_layer_metadata_cache,
)


def main():
    force_update = (
        "--force" in sys.argv
    )

    if (
        not force_update
        and not cache_needs_refresh()
    ):
        print(
            "Layer metadata cache is still current: "
            f"{metadata_cache_path()}"
        )

        return 0

    try:
        cache_path = (
            update_layer_metadata_cache()
        )

    except Exception as error:
        print(
            "Layer metadata cache update failed. "
            "The existing cache has been preserved."
        )

        print(
            str(error)
        )

        return 1

    print(
        f"Layer metadata cache updated: "
        f"{cache_path}"
    )

    return 0


if __name__ == "__main__":
    raise SystemExit(
        main()
    )