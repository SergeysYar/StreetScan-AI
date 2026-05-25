# РџСЂРµРґРѕР±СЂР°Р±РѕС‚РєР°

## РќР°Р·РЅР°С‡РµРЅРёРµ
РџРѕРґСЃРёСЃС‚РµРјР° РїСЂРµРґРѕР±СЂР°Р±РѕС‚РєРё РїРѕРґРіРѕС‚Р°РІР»РёРІР°РµС‚ СЃС‹СЂС‹Рµ РіРѕСЂРѕРґСЃРєРёРµ LiDAR-РѕР±Р»Р°РєР° С‚РѕС‡РµРє РґР»СЏ РїРѕСЃР»РµРґСѓСЋС‰РёС… СЌС‚Р°РїРѕРІ РєР»Р°СЃС‚РµСЂРёР·Р°С†РёРё, СЃРµРіРјРµРЅС‚Р°С†РёРё, Р°РЅР°Р»РёС‚РёРєРё Рё РІРёР·СѓР°Р»РёР·Р°С†РёРё Р·Р° СЃС‡РµС‚ С„РёР»СЊС‚СЂР°С†РёРё С€СѓРјР° Рё РіРµРѕРјРµС‚СЂРёС‡РµСЃРєРѕР№ РЅРѕСЂРјР°Р»РёР·Р°С†РёРё.

## РџРѕРґРґРµСЂР¶РёРІР°РµРјС‹Рµ С„РѕСЂРјР°С‚С‹
- Р’С…РѕРґ: `.ply`, `.pcd`, `.xyz`
- Р’С‹С…РѕРґ: `.ply` РёР»Рё `.pcd` (РЅР°СЃС‚СЂР°РёРІР°РµС‚СЃСЏ)

## Р”РѕСЃС‚СѓРїРЅС‹Рµ РѕРїРµСЂР°С†РёРё
- Voxel downsampling
- РЎС‚Р°С‚РёСЃС‚РёС‡РµСЃРєР°СЏ С„РёР»СЊС‚СЂР°С†РёСЏ РІС‹Р±СЂРѕСЃРѕРІ
- Р Р°РґРёСѓСЃРЅР°СЏ С„РёР»СЊС‚СЂР°С†РёСЏ РІС‹Р±СЂРѕСЃРѕРІ
- РћС†РµРЅРєР° РїР»РѕСЃРєРѕСЃС‚Рё Р·РµРјР»Рё RANSAC Рё СЂР°Р·РґРµР»РµРЅРёРµ РЅР° ground/non-ground
- РќРѕСЂРјР°Р»РёР·Р°С†РёСЏ РєРѕРѕСЂРґРёРЅР°С‚ (С‚РѕР»СЊРєРѕ РїРµСЂРµРЅРѕСЃ Рє С†РµРЅС‚СЂРѕРёРґСѓ)
- РћС†РµРЅРєР° РїР»РѕС‚РЅРѕСЃС‚Рё С‚РѕС‡РµРє (`points / volume AABB`)

## РџСЂРёРјРµСЂ РєРѕРЅС„РёРіСѓСЂР°С†РёРё
```yaml
preprocessing:
  voxel_size: 0.1
  enable_voxel_downsampling: true
  enable_statistical_outlier_removal: true
  statistical_nb_neighbors: 20
  statistical_std_ratio: 2.0
  enable_radius_outlier_removal: false
  radius_nb_points: 8
  radius: 0.5
  enable_ground_filtering: true
  ground_distance_threshold: 0.2
  ground_ransac_n: 3
  ground_num_iterations: 1000
  normalize_coordinates: false
  estimate_density: true
  output_format: ply
```

## РСЃРїРѕР»СЊР·РѕРІР°РЅРёРµ CLI
```bash
uv run src/preprocessing/preprocess_pointcloud.py \
  --input data/raw/sample.ply \
  --output-dir outputs/pointclouds/preprocessed \
  --config configs/preprocessing.yaml
```

```bash
uv run src/cli.py preprocess \
  --input data/raw/sample.ply \
  --output-dir outputs/pointclouds/preprocessed \
  --ground-filter \
  --estimate-density
```

## Р’С‹С…РѕРґРЅС‹Рµ С„Р°Р№Р»С‹
- `outputs/pointclouds/preprocessed/<name>_preprocessed.(ply|pcd)`
- `outputs/pointclouds/preprocessed/<name>_ground.(ply|pcd)` (РµСЃР»Рё РІРєР»СЋС‡РµРЅРѕ)
- `outputs/pointclouds/preprocessed/<name>_nonground.(ply|pcd)` (РµСЃР»Рё РІРєР»СЋС‡РµРЅРѕ)
- `outputs/reports/preprocessing/<name>_stats.json`
- `outputs/reports/preprocessing/<name>_report.md`

## РРЅС‚РµСЂРїСЂРµС‚Р°С†РёСЏ СЃС‚Р°С‚РёСЃС‚РёРєРё
- `original_points`, `after_downsampling_points`, `after_outlier_removal_points`, `final_points`: РїСЂРѕС„РёР»СЊ СЃРѕРєСЂР°С‰РµРЅРёСЏ С‡РёСЃР»Р° С‚РѕС‡РµРє
- `ground_points` / `nonground_points`: РєР°С‡РµСЃС‚РІРѕ СЂР°Р·РґРµР»РµРЅРёСЏ РїРѕРІРµСЂС…РЅРѕСЃС‚Рё Р·РµРјР»Рё
- `bounding_box_*`, `centroid`: РіРµРѕРјРµС‚СЂРёС‡РµСЃРєРёРµ С…Р°СЂР°РєС‚РµСЂРёСЃС‚РёРєРё РѕР±Р»Р°РєР°
- `average_density`: РїСЂРёР±Р»РёР¶РµРЅРЅР°СЏ РѕР±СЉРµРјРЅР°СЏ РїР»РѕС‚РЅРѕСЃС‚СЊ; `null` РѕР·РЅР°С‡Р°РµС‚ РЅСѓР»РµРІРѕР№/РЅРµРєРѕСЂСЂРµРєС‚РЅС‹Р№ РѕР±СЉРµРј
- `operations_applied` Рё `warnings`: С‚СЂР°СЃСЃРёСЂСѓРµРјРѕСЃС‚СЊ Рё РґРёР°РіРЅРѕСЃС‚РёРєР° РѕС€РёР±РѕРє

