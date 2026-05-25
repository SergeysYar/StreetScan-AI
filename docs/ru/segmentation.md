# РЎРµРіРјРµРЅС‚Р°С†РёСЏ

## РќР°Р·РЅР°С‡РµРЅРёРµ
РџРѕРґСЃРёСЃС‚РµРјР° СЃРµРјР°РЅС‚РёС‡РµСЃРєРѕР№ СЃРµРіРјРµРЅС‚Р°С†РёРё РІС‹РїРѕР»РЅСЏРµС‚ РїРѕРєРѕРјРїРѕРЅРµРЅС‚РЅСѓСЋ СЂР°Р·РјРµС‚РєСѓ С‚РѕС‡РµРє РіРѕСЂРѕРґСЃРєРѕРіРѕ LiDAR-РѕР±Р»Р°РєР° РґР»СЏ РїРѕСЃР»РµРґСѓСЋС‰РёС… СЌС‚Р°РїРѕРІ РІРѕСЃРїСЂРёСЏС‚РёСЏ Рё Р°РЅР°Р»РёС‚РёРєРё.

## РџРѕРґРґРµСЂР¶РёРІР°РµРјС‹Рµ РєР»Р°СЃСЃС‹
- `0 unlabeled`
- `1 road`
- `2 building`
- `3 vehicle`
- `4 pedestrian`
- `5 vegetation`
- `6 pole`
- `7 traffic_sign`

## Р‘Р°Р·РѕРІС‹Р№ РјРµС‚РѕРґ
Р РµР¶РёРј `baseline` СЂРµР°Р»РёР·РѕРІР°РЅ РєР°Рє РґРµС‚РµСЂРјРёРЅРёСЂРѕРІР°РЅРЅС‹Р№ РЅР°Р±РѕСЂ РїСЂР°РІРёР»:
- РЅРѕСЂРјР°Р»РёР·Р°С†РёСЏ РІС‹СЃРѕС‚С‹ РѕС‚РЅРѕСЃРёС‚РµР»СЊРЅРѕ РјРёРЅРёРјР°Р»СЊРЅРѕРіРѕ `Z`
- РїСЂРёСЃРІРѕРµРЅРёРµ `road` РґР»СЏ РѕРєРѕР»РѕР·РµРјРЅС‹С… С‚РѕС‡РµРє
- РґРёР°РїР°Р·РѕРЅРЅС‹Рµ РїСЂР°РІРёР»Р° РїРѕ РІС‹СЃРѕС‚Рµ РґР»СЏ `vehicle` Рё `pedestrian`
- СЂР°Р·РґРµР»РµРЅРёРµ РІС‹СЃРѕРєРёС… СЃС‚СЂСѓРєС‚СѓСЂ РЅР° `building`/`vegetation` РїРѕ Р»РѕРєР°Р»СЊРЅРѕР№ РїР»РѕС‚РЅРѕСЃС‚Рё
- РІС‹РґРµР»РµРЅРёРµ СѓР·РєРёС… РІРµСЂС‚РёРєР°Р»СЊРЅС‹С… СЃС‚СЂСѓРєС‚СѓСЂ РєР°Рє `pole`/`traffic_sign`

Р­С‚Рѕ РёРЅС‚РµСЂРїСЂРµС‚РёСЂСѓРµРјС‹Р№ Р±Р°Р·РѕРІС‹Р№ РїРѕРґС…РѕРґ, Р° РЅРµ РѕР±СѓС‡РµРЅРЅР°СЏ РЅРµР№СЂРѕСЃРµС‚РµРІР°СЏ РјРѕРґРµР»СЊ.

## Р—Р°РіР»СѓС€РєР° PointNet++
Р РµР¶РёРј `pointnet` СЏРІР»СЏРµС‚СЃСЏ РєРѕРЅС‚СЂР°РєС‚РѕРј РёРЅС‚РµРіСЂР°С†РёРё. РџСЂРё РѕС‚СЃСѓС‚СЃС‚РІРёРё РІРµСЃРѕРІ РІС‹РїРѕР»РЅРµРЅРёРµ Р·Р°РІРµСЂС€Р°РµС‚СЃСЏ СЏРІРЅРѕР№ РѕС€РёР±РєРѕР№.
Р¤РёРєС‚РёРІРЅС‹Рµ РїСЂРµРґСЃРєР°Р·Р°РЅРёСЏ РЅРµ РіРµРЅРµСЂРёСЂСѓСЋС‚СЃСЏ.

## Р’С…РѕРґ / Р’С‹С…РѕРґ
- Р’С…РѕРґ: `.ply`, `.pcd`, `.xyz`
- Р’С‹С…РѕРґ:
  - `outputs/semantic/<name>_semantic.ply`
  - `outputs/semantic/<name>_semantic_labels.csv`
  - `outputs/semantic/<name>_semantic_stats.csv`
  - `outputs/reports/segmentation/<name>_segmentation_report.md`
  - РѕРїС†РёРѕРЅР°Р»СЊРЅРѕ `outputs/semantic/<name>_semantic.png`

## РџСЂРёРјРµСЂ РєРѕРЅС„РёРіСѓСЂР°С†РёРё
```yaml
segmentation:
  method: baseline
  weights_path: null
  device: cpu
  use_cluster_features: false
  cluster_labels_path: null
  cluster_stats_path: null
  z_ground_threshold: 0.25
  z_vehicle_min: 0.3
  z_vehicle_max: 2.2
  z_pedestrian_min: 0.5
  z_pedestrian_max: 2.5
  pole_radius_threshold: 0.25
  min_points_per_object: 20
  save_screenshot: false
  output_format: ply
```

## РџСЂРёРјРµСЂС‹ CLI
```bash
uv run src/segmentation/semantic_segmentation.py \
  --input outputs/pointclouds/preprocessed/sample_preprocessed.ply \
  --output-dir outputs/semantic \
  --method baseline
```

```bash
uv run src/cli.py segment \
  --input outputs/pointclouds/preprocessed/sample_preprocessed.ply \
  --output-dir outputs/semantic \
  --method baseline \
  --config configs/segmentation.yaml
```

## РћРіСЂР°РЅРёС‡РµРЅРёСЏ Рё СЂР°Р·РІРёС‚РёРµ
- РљР°С‡РµСЃС‚РІРѕ baseline-РїСЂР°РІРёР» Р·Р°РІРёСЃРёС‚ РѕС‚ С‚РёРїР° СЃС†РµРЅС‹.
- Р”Р»СЏ СЂРµР¶РёРјР° PointNet++ С‚СЂРµР±СѓРµС‚СЃСЏ СЂРµР°Р»СЊРЅР°СЏ РёРЅС‚РµРіСЂР°С†РёСЏ РѕР±СѓС‡РµРЅРЅРѕР№ РјРѕРґРµР»Рё.

