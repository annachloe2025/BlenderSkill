# vrm_to_fbx_for_mixamo.py

VRoid Studio 製の VRMキャラを、**Mixamoの auto-rigger が auto-rig を実行してくれる FBX** に変換するユーティリティ。`character_setup.py` の素材作成段階で使う。

## コード

```python
--8<-- "snippets/vrm_to_fbx_for_mixamo.py"
```

## 処理の流れ

1. シーンを空にする
2. `bpy.ops.import_scene.vrm()` で VRM を読み込み（VRM Add-on for Blender 必須）
3. **メッシュのみ**で FBX 書き出し（テクスチャ埋め込み）
4. ユーザはこの FBX を Mixamo に手動アップロード → auto-rig → DL

## 注意点（最重要）

### `object_types={'MESH'}` を必ず指定

Mixamo の auto-rigger は **メッシュのみのFBXを期待**する。アーマチュアを含めて投げると「これは既にリグ済み」と判定して **auto-rig画面そのものをスキップ**し、元のリグ（VRoid Humanoid命名）のまま FBX を返してくる。

NG:
```python
object_types={'ARMATURE', 'MESH'},   # ← Mixamoがauto-rigを省略する
```

OK:
```python
object_types={'MESH'},               # ← auto-rigger画面が出る
```

メッシュのみ書き出してもバインド形状は T-Pose のまま保存されるので、Mixamoで正しくリグが当たる。

### Mixamoのキャッシュ動作

同じ内容のFBXを2回目アップすると、Mixamo側がコンテンツ一致と判定して前回の結果をそのまま返すケースあり。回避は：
- ファイル名を変える
- 上記 `object_types={'MESH'}` を守っていれば、初回からちゃんとauto-rigが走る

## 前提

- Blender 5.x
- **VRM Add-on for Blender** が有効化済み (`bpy.ops.import_scene.vrm` が使える)
  - <https://github.com/saturday06/VRM-Addon-for-Blender>

## 設定

```python
VRM_PATH = r"...\blender\assets\vroid\<char>\<char>.vrm"
OUT_FBX  = r"...\blender\assets\vroid\<char>\<char>_for_mixamo.fbx"
```

新キャラ追加時はこの2行だけ書き換える。
