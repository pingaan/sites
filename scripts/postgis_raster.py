import os

import psycopg2
from psycopg2 import sql

from qgis.core import (
    QgsCoordinateReferenceSystem,
    QgsCoordinateTransform,
    QgsProject,
    QgsRasterLayer,
    QgsRectangle,
)


def download_dem_from_postgis(
    site_extent,
    dem_config,
    temp_path,
    output_filename="postgis_dem.tif",
    raster_label="DEM",
):
    """
    Select PostGIS DEM tiles intersecting the site extent,
    merge them in PostGIS and save one local GeoTIFF.
    """

    required_config = {
        "schema",
        "table",
        "raster_column",
        "srid",
    }

    missing_config = (
        required_config - set(dem_config)
    )

    if missing_config:
        raise ValueError(
            "DEM configuration is missing: "
            + ", ".join(sorted(missing_config))
        )

    password = os.environ.get(
        "SITES_DB_PASSWORD"
    )

    if not password:
        raise RuntimeError(
            "SITES_DB_PASSWORD has not been set."
        )

    raster_crs = (
        QgsCoordinateReferenceSystem.fromEpsgId(
            int(dem_config["srid"])
        )
    )

    if not raster_crs.isValid():
        raise ValueError(
            "Invalid PostGIS DEM CRS: "
            f"EPSG:{dem_config['srid']}"
        )

    source_crs = site_extent["crs"]

    if not source_crs.isValid():
        raise ValueError(
            "The site extent has no valid CRS."
        )

    search_extent = QgsRectangle(
        site_extent["x_min"],
        site_extent["y_min"],
        site_extent["x_max"],
        site_extent["y_max"],
    )

    if source_crs != raster_crs:
        transform = QgsCoordinateTransform(
            source_crs,
            raster_crs,
            QgsProject.instance().transformContext(),
        )

        search_extent = (
            transform.transformBoundingBox(
                search_extent
            )
        )

    os.makedirs(
        temp_path,
        exist_ok=True,
    )

    output_path = os.path.join(
        temp_path,
        output_filename,
    )

    temporary_path = (
        output_path + ".part"
    )

    query = sql.SQL(
        """
        WITH search_area AS (
            SELECT ST_MakeEnvelope(
                %s,
                %s,
                %s,
                %s,
                %s
            ) AS geom
        ),
        selected AS MATERIALIZED (
            SELECT source.{raster_column} AS rast
            FROM {schema}.{table} AS source
            CROSS JOIN search_area
            WHERE ST_Intersects(
                source.{raster_column},
                search_area.geom
            )
        )
        SELECT
            count(*)::integer AS tile_count,
            ST_AsGDALRaster(
                ST_Union(rast),
                'GTiff',
                ARRAY[
                    'COMPRESS=DEFLATE',
                    'PREDICTOR=3',
                    'TILED=YES'
                ]
            ) AS geotiff
        FROM selected;
        """
    ).format(
        schema=sql.Identifier(
            dem_config["schema"]
        ),
        table=sql.Identifier(
            dem_config["table"]
        ),
        raster_column=sql.Identifier(
            dem_config["raster_column"]
        ),
    )

    print(
        f"Requesting indexed {raster_label} tiles from "
        f"PostGIS ({dem_config['schema']}."
        f"{dem_config['table']})..."
    )

    connection = psycopg2.connect(
        host=os.environ.get(
            "SITES_DB_HOST",
            "127.0.0.1",
        ),
        port=int(
            os.environ.get(
                "SITES_DB_PORT",
                "5433",
            )
        ),
        dbname=os.environ.get(
            "SITES_DB_NAME",
            "sites",
        ),
        user=os.environ.get(
            "SITES_DB_USER",
            "sites_app",
        ),
        password=password,
        connect_timeout=15,
        application_name=(
            f"Sites {raster_label} download"
        ),
    )

    try:
        with connection.cursor() as cursor:
            cursor.execute(
                "SET statement_timeout = 0"
            )

            cursor.execute(
                query,
                (
                    search_extent.xMinimum(),
                    search_extent.yMinimum(),
                    search_extent.xMaximum(),
                    search_extent.yMaximum(),
                    int(dem_config["srid"]),
                ),
            )

            result = cursor.fetchone()

    finally:
        connection.close()

    if not result:
        raise RuntimeError(
            "PostGIS returned no DEM result."
        )

    tile_count, geotiff = result

    if tile_count == 0 or geotiff is None:
        raise ValueError(
            "No PostGIS DEM tiles overlap "
            "the analysis site."
        )

    with open(
        temporary_path,
        "wb",
    ) as output:
        output.write(bytes(geotiff))

    os.replace(
        temporary_path,
        output_path,
    )

    raster = QgsRasterLayer(
        output_path,
        f"PostGIS {raster_label}",
        "gdal",
    )

    if not raster.isValid():
        raise RuntimeError(
            "The GeoTIFF returned by PostGIS "
            "could not be loaded."
        )

    if raster.crs() != raster_crs:
        raise RuntimeError(
            "The downloaded DEM has an "
            "unexpected CRS: "
            f"{raster.crs().authid()}"
        )

    size_mib = (
        os.path.getsize(output_path)
        / 1024
        / 1024
    )

    print(
        f"PostGIS {raster_label} downloaded: "
        f"{tile_count} tile(s), "
        f"{size_mib:.1f} MiB"
    )

    print(
        f"Local {raster_label}: {output_path}"
    )

    return output_path

def sample_raster_values_from_postgis(
    raster_configs,
    longitude,
    latitude,
):
    """
    Sample several indexed PostGIS rasters at one WGS 84 point.

    One database connection is reused for every configured raster.
    """

    required_config = {
        "schema",
        "table",
        "raster_column",
        "srid",
    }

    for key, config in raster_configs.items():
        missing_config = (
            required_config - set(config)
        )

        if missing_config:
            raise ValueError(
                f"Raster configuration for {key!r} "
                "is missing: "
                + ", ".join(
                    sorted(missing_config)
                )
            )

    password = os.environ.get(
        "SITES_DB_PASSWORD"
    )

    if not password:
        raise RuntimeError(
            "SITES_DB_PASSWORD has not been set."
        )

    connection = psycopg2.connect(
        host=os.environ.get(
            "SITES_DB_HOST",
            "127.0.0.1",
        ),
        port=int(
            os.environ.get(
                "SITES_DB_PORT",
                "5433",
            )
        ),
        dbname=os.environ.get(
            "SITES_DB_NAME",
            "sites",
        ),
        user=os.environ.get(
            "SITES_DB_USER",
            "sites_app",
        ),
        password=password,
        connect_timeout=15,
        application_name=(
            "Sites SolarGIS sampling"
        ),
    )

    values = {}

    try:
        with connection.cursor() as cursor:
            cursor.execute(
                "SET statement_timeout = '60s'"
            )

            for key, config in (
                raster_configs.items()
            ):
                query = sql.SQL(
                    """
                    WITH sample_point AS (
                        SELECT ST_Transform(
                            ST_SetSRID(
                                ST_MakePoint(%s, %s),
                                4326
                            ),
                            %s
                        ) AS geom
                    )
                    SELECT ST_Value(
                        source.{raster_column},
                        %s,
                        sample_point.geom,
                        true
                    )
                    FROM
                        {schema}.{table}
                            AS source
                    CROSS JOIN sample_point
                    WHERE
                        ST_ConvexHull(
                            source.{raster_column}
                        ) && sample_point.geom
                        AND ST_Intersects(
                            source.{raster_column},
                            sample_point.geom
                        )
                    LIMIT 1
                    """
                ).format(
                    schema=sql.Identifier(
                        config["schema"]
                    ),
                    table=sql.Identifier(
                        config["table"]
                    ),
                    raster_column=sql.Identifier(
                        config["raster_column"]
                    ),
                )

                cursor.execute(
                    query,
                    (
                        float(longitude),
                        float(latitude),
                        int(config["srid"]),
                        int(config.get("band", 1)),
                    ),
                )

                row = cursor.fetchone()

                if (
                    row is None
                    or row[0] is None
                ):
                    values[key] = None
                else:
                    values[key] = float(
                        row[0]
                    )

    except Exception as error:
        raise RuntimeError(
            "Failed to sample the PostGIS "
            "SolarGIS rasters."
        ) from error

    finally:
        connection.close()

    return values