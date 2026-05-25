# РљР»Р°СЃС‚РµСЂРёР·Р°С†РёСЏ

## РќР°Р·РЅР°С‡РµРЅРёРµ
РџРѕРґСЃРёСЃС‚РµРјР° РєР»Р°СЃС‚РµСЂРёР·Р°С†РёРё РІС‹РґРµР»СЏРµС‚ РѕР±СЉРµРєС‚РЅС‹Рµ РіСЂСѓРїРїС‹ РІ РіРѕСЂРѕРґСЃРєРёС… LiDAR-РѕР±Р»Р°РєР°С… С‚РѕС‡РµРє РґР»СЏ Р·Р°РґР°С‡ РёРЅС‚РµСЂРїСЂРµС‚Р°С†РёРё С‚СЂР°С„РёРєР°, РїРѕСЃР»РµРґСѓСЋС‰РµРіРѕ С‚СЂРµРєРёРЅРіР° Рё СЃРµРјР°РЅС‚РёС‡РµСЃРєРѕР№ РїРѕСЃС‚РѕР±СЂР°Р±РѕС‚РєРё.

## РџРѕРґРґРµСЂР¶РёРІР°РµРјС‹Рµ РјРµС‚РѕРґС‹
- `dbscan`: РїР»РѕС‚РЅРѕСЃС‚РЅР°СЏ РєР»Р°СЃС‚РµСЂРёР·Р°С†РёСЏ Open3D.
- `euclidean`: СЂР°РґРёСѓСЃРЅР°СЏ РєР»Р°СЃС‚РµСЂРёР·Р°С†РёСЏ РјРµС‚РѕРґРѕРј region-growing РЅР° РѕСЃРЅРѕРІРµ Р±Р»РёР¶Р°Р№С€РёС… СЃРѕСЃРµРґРµР№.

## РћСЃРЅРѕРІРЅС‹Рµ РїР°СЂР°РјРµС‚СЂС‹
- `eps`: СЂР°РґРёСѓСЃ РѕРєСЂРµСЃС‚РЅРѕСЃС‚Рё DBSCAN.
- `min_points`: РјРёРЅРёРјР°Р»СЊРЅРѕРµ С‡РёСЃР»Рѕ С‚РѕС‡РµРє РґР»СЏ core-С‚РѕС‡РєРё DBSCAN.
- `euclidean_tolerance`: СЂР°РґРёСѓСЃ СЃРѕСЃРµРґСЃС‚РІР° РґР»СЏ Euclidean-РјРµС‚РѕРґР°.
- `min_cluster_size`, `max_cluster_size`: С„РёР»СЊС‚СЂР°С†РёСЏ РєР»Р°СЃС‚РµСЂРѕРІ РїРѕ СЂР°Р·РјРµСЂСѓ.
- `remove_noise`: РёСЃРєР»СЋС‡РµРЅРёРµ РјРµС‚РєРё `-1` РёР· РІР°Р»РёРґРЅРѕР№ СЃС‚Р°С‚РёСЃС‚РёРєРё.

## РџСЂРёРјРµСЂ DBSCAN
```bash
uv run src/clustering/dbscan_clustering.py \
  --input outputs/pointclouds/preprocessed/sample_preprocessed.ply \
  --output-dir outputs/clusters \
  --config configs/clustering.yaml \
  --method dbscan \
  --eps 0.8 \
  --min-points 20
```

## РџСЂРёРјРµСЂ Euclidean
```bash
uv run src/clustering/dbscan_clustering.py \
  --input outputs/pointclouds/preprocessed/sample_preprocessed.ply \
  --output-dir outputs/clusters \
  --method euclidean \
  --euclidean-tolerance 0.6 \
  --min-cluster-size 30
```

## РРЅС‚РµРіСЂР°С†РёСЏ РІ РѕР±С‰РёР№ CLI
```bash
uv run src/cli.py cluster \
  --input outputs/pointclouds/preprocessed/sample_preprocessed.ply \
  --output-dir outputs/clusters \
  --method dbscan \
  --eps 0.8 \
  --min-points 20
```

## Р’С‹С…РѕРґРЅС‹Рµ С„Р°Р№Р»С‹
- `outputs/clusters/<name>_clusters.ply`
- `outputs/clusters/<name>_cluster_stats.csv`
- `outputs/clusters/<name>_cluster_labels.csv`
- `outputs/reports/clustering/<name>_cluster_report.md`
- `outputs/clusters/<name>_clusters.png` (РѕРїС†РёРѕРЅР°Р»СЊРЅРѕ)

## РРЅС‚РµСЂРїСЂРµС‚Р°С†РёСЏ СЃС‚Р°С‚РёСЃС‚РёРєРё
- `point_count`, `centroid`: СЂР°Р·РјРµСЂ Рё РїРѕР»РѕР¶РµРЅРёРµ РѕР±СЉРµРєС‚Р°.
- `bbox_min/max`, `extent`, `bbox_volume`: РїСЂРѕСЃС‚СЂР°РЅСЃС‚РІРµРЅРЅС‹Рµ РіР°Р±Р°СЂРёС‚С‹ РєР»Р°СЃС‚РµСЂР°.
- `density`: РїСЂРёР±Р»РёР¶РµРЅРЅР°СЏ РєРѕРјРїР°РєС‚РЅРѕСЃС‚СЊ (`points / bbox_volume`).
- `is_noise`: РїСЂРёР·РЅР°Рє С€СѓРјРѕРІС‹С… С‚РѕС‡РµРє.

## РўРёРїРѕРІС‹Рµ СЃС‚Р°СЂС‚РѕРІС‹Рµ Р·РЅР°С‡РµРЅРёСЏ
- Р”Р»СЏ РіРѕСЂРѕРґСЃРєРёС… СЃС†РµРЅ СЃСЂРµРґРЅРµР№ РїР»РѕС‚РЅРѕСЃС‚Рё:
  - DBSCAN: `eps=0.6..1.0`, `min_points=15..30`
  - Euclidean: `euclidean_tolerance=0.4..0.8`, `min_cluster_size=20..50`

