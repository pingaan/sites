from importlib import import_module


COUNTRY_MODULES = {
    "SE": "scripts.countries.se",
}


def load_country_config(country_code):
    """
    Load the configuration for a supported country.

    Register additional countries once their configurations
    are ready.
    """

    code = country_code.strip().upper()

    module_path = COUNTRY_MODULES.get(code)

    if module_path is None:
        supported = ", ".join(sorted(COUNTRY_MODULES))

        raise ValueError(
            f"Unsupported country: {country_code!r}. "
            f"Available countries: {supported}"
        )

    config = import_module(module_path)

    if config.COUNTRY_CODE != code:
        raise ValueError(
            f"Country configuration mismatch in {module_path}."
        )

    print(
        f"Country configuration loaded: "
        f"{config.COUNTRY_NAME} ({config.COUNTRY_CODE})"
    )

    return config