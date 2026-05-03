# keyframe_animation.py — キーフレームアニメーション

オブジェクトの位置・回転・スケールを **時間軸に沿って変化** させる最も基本的なアニメ。Phase 5 の入口。

## コード

```python
--8<-- "snippets/keyframe_animation.py"
```

## キーフレーム挿入の最小パターン

```python
obj.location = (x, y, z)
obj.keyframe_insert(data_path="location", frame=N)
```

`data_path` は属性パス。よく使うもの:

| data_path | 内容 |
|---|---|
| `"location"` | 位置 |
| `"rotation_euler"` | 回転（ラジアン）|
| `"scale"` | スケール |
| `"hide_render"` | レンダー非表示の切替 |

## フレーム範囲とFPS

```python
scene.frame_start = 1
scene.frame_end = 60
scene.render.fps = 24
```

24fps で 60 フレーム = 2.5秒。映像作品なら 24 か 30、ゲーム向けなら 60。

## 補間モード

デフォルトは `BEZIER`（滑らかなS字補間）。直線的に変化させたいなら:

```python
for fcurve in obj.animation_data.action.fcurves:
    for kp in fcurve.keyframe_points:
        kp.interpolation = 'LINEAR'   # 'BEZIER', 'LINEAR', 'CONSTANT'
```

## ループアニメーション

開始フレームと終了フレームで **同じ値** にすると、シームレスにループする:

```python
obj.rotation_euler = (0, 0, 0)
obj.keyframe_insert(data_path="rotation_euler", frame=1)
obj.rotation_euler = (0, 0, math.radians(360))   # 360度=0度
obj.keyframe_insert(data_path="rotation_euler", frame=60)
```

## 動画として書き出し

単一フレームのレンダリングと違い、動画は:

```python
scene.render.image_settings.file_format = 'FFMPEG'
scene.render.ffmpeg.format = 'MPEG4'
scene.render.ffmpeg.codec = 'H264'
scene.render.filepath = "/path/to/output.mp4"
bpy.ops.render.render(animation=True)   # animation=True が肝
```

## 落とし穴

- `keyframe_insert` する前に **属性を変更しておく必要がある**（現在値が記録される）
- `data_path` は **小文字**（`"location"` であって `"Location"` ではない）
- 全キーフレームを消すには `obj.animation_data_clear()`
