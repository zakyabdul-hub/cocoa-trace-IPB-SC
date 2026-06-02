"""
create_shapefile_simulasi.py
Skrip untuk membuat file shapefile kawasan hutan SIMULASI
untuk keperluan pengujian fitur validasi geospasial F2.

Jalankan sekali: python create_shapefile_simulasi.py
"""

import geopandas as gpd
from shapely.geometry import Polygon
import os

def create_simulation_shapefile():
    """
    Membuat shapefile simulasi yang merepresentasikan kawasan hutan.
    Area kawasan hutan yang didefinisikan adalah poligon di koordinat tertentu.
    Koordinat ini adalah simulasi — sesuaikan dengan lokasi riil jika diperlukan.
    """
    # Definisikan beberapa poligon kawasan hutan (koordinat simulasi - Sulawesi Selatan area)
    kawasan_hutan = [
        # Kawasan Hutan 1: Area simulasi (Lat: -3.5 s/d -3.0, Lon: 120.5 s/d 121.0)
        Polygon([
            (120.5, -3.5),
            (121.0, -3.5),
            (121.0, -3.0),
            (120.5, -3.0),
            (120.5, -3.5)
        ]),
        # Kawasan Hutan 2: Area simulasi kedua
        Polygon([
            (119.0, -4.5),
            (119.5, -4.5),
            (119.5, -4.0),
            (119.0, -4.0),
            (119.0, -4.5)
        ]),
        # Kawasan Hutan 3: Area simulasi ketiga (untuk testing deforestasi)
        Polygon([
            (120.0, -5.0),
            (120.3, -5.0),
            (120.3, -4.7),
            (120.0, -4.7),
            (120.0, -5.0)
        ]),
    ]
    
    # Buat GeoDataFrame
    gdf = gpd.GeoDataFrame(
        {
            'nama_kawasan': [
                'Kawasan Hutan Lindung A (Simulasi)',
                'Kawasan Hutan Lindung B (Simulasi)',
                'Kawasan Hutan Produksi C (Simulasi)',
            ],
            'status': ['Hutan Lindung', 'Hutan Lindung', 'Hutan Produksi'],
            'luas_ha': [50000, 35000, 28000],
        },
        geometry=kawasan_hutan,
        crs="EPSG:4326"  # WGS84
    )
    
    # Simpan ke file .shp
    output_path = os.path.join(os.path.dirname(__file__), "peta_kawasan_hutan.shp")
    gdf.to_file(output_path, driver="ESRI Shapefile")
    
    print(f"[OK] Shapefile simulasi berhasil dibuat: {output_path}")
    print(f"     Total {len(gdf)} kawasan hutan simulasi")
    print(f"\n[INFO] Koordinat untuk testing:")
    print(f"   Lahan BEBAS Deforestasi : Lat=-5.5, Lon=119.5 (di luar kawasan hutan)")
    print(f"   Lahan TIDAK BEBAS       : Lat=-3.2, Lon=120.7 (di dalam Kawasan Hutan A)")
    print(f"   Lahan TIDAK BEBAS       : Lat=-4.2, Lon=119.2 (di dalam Kawasan Hutan B)")
    
    return output_path


if __name__ == "__main__":
    create_simulation_shapefile()
