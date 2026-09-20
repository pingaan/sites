from pathlib import Path

from osgeo import gdal, osr


sgis_path = Path(
    r"H:\gis_data\anna2.0\sgis"
)


for raster_path in sorted(
    sgis_path.glob("*.tif")
):
    dataset = gdal.Open(
        str(raster_path)
    )

    if dataset is None:
        print(
            f"\n{raster_path.name}: FAILED TO OPEN"
        )
        continue

    band = dataset.GetRasterBand(1)

    spatial_reference = osr.SpatialReference(
        wkt=dataset.GetProjection()
    )

    authority_name = (
        spatial_reference.GetAuthorityName(
            None
        )
    )

    authority_code = (
        spatial_reference.GetAuthorityCode(
            None
        )
    )

    print(
        f"\n--- {raster_path.name} ---"
    )

    print(
        f"CRS: {authority_name}:"
        f"{authority_code}"
    )

    print(
        f"Size: "
        f"{dataset.RasterXSize} × "
        f"{dataset.RasterYSize}"
    )

    print(
        f"GeoTransform: "
        f"{dataset.GetGeoTransform()}"
    )

    print(
        f"Data type: "
        f"{gdal.GetDataTypeName(band.DataType)}"
    )

    print(
        f"NoData: {band.GetNoDataValue()}"
    )

    print(
        f"Scale: {band.GetScale()}"
    )

    print(
        f"Offset: {band.GetOffset()}"
    )

    print(
        f"Unit: {band.GetUnitType() or 'not embedded'}"
    )

    dataset = None