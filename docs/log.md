# 学習ログ

各セッションでの試行錯誤を時系列で記録します。
新しいエントリは **上に追記** してください（最新が一番上）。

---

## テンプレート（コピーして使う）

### YYYY-MM-DD: タイトル

**目標**: 何を作る／学ぼうとしたか

**調べた情報**:
- 参照したサイト・ドキュメント

**実行した手順**:
1. ...
2. ...

**結果**: 成功 / 部分的成功 / 失敗

**学んだこと**:
- ...

**つまずいた点**:
- ...

**再利用可能な成果物**:
- snippets/xxx.py
- memory/xxx.md に追記

---

## 2026-05-04: Phase 2 — 押し出し / ループカット+ベベル / 椅子モデリング

**目標**: Phase 2 の「Extrude」「ループカット+ベベル」を消化し、はじめての家具モデル（椅子）を完成させる

**実行した手順**:
1. **Extrude**: Plane から「上に押し出し → 奥に押し出し」を5回ループして5段の階段を生成（44頂点/42面）
2. **ループカット + ベベル**: Cube → `subdivide(number_cuts=1)` で全エッジに1ループ追加 → `bevel(offset=0.15, segments=4)` で全エッジ丸め（602頂点/600面の滑らかな箱）
3. **椅子モデリング**: 座面（角丸ボックス）+ 脚×4（円柱、符号反転for配置）+ 背もたれ（角丸ボックス）+ 床 + Sun + カメラまでスクリプト1本で構築。`add_rounded_box()` ヘルパー関数で繰り返しを排除。
4. **レンダリング**: Eevee で `docs/images/chair_v1.png` に出力（800x500、影付き）

**結果**: 全部成功。Phase 2 の「立体物を作る基本技」が揃った。椅子はスクリプト1本で再現可能。

**学んだこと**:
- `extrude_region_move` の引数は `TRANSFORM_OT_translate={"value": (dx,dy,dz)}` の2層構造
- ループカットはコードからは `bpy.ops.mesh.subdivide(number_cuts=N)` のほうが安全（loopcut は対話的）
- `bevel` は **先にエッジを増やしてから** 効かせると柔らかい形になる
- 複合モデルは「寸法を定数化 → 繰り返しを関数化 → 対称配置は符号反転for」の3点セットで再利用性が上がる
- `space.region_3d.view_perspective = 'CAMERA'` でビューポートをカメラ視点に切り替えられる

**つまずいた点**:
- ビューポートが俯瞰のままだと椅子が小さく見えて評価しにくかった。カメラ視点切替コードが必要だった。
- 角丸ボックスは bevel offset 0.04 だと遠目では分かりにくい。寄せた構図で確認するのが大事。

**再利用可能な成果物**:
- `snippets/extrude_stairs.py` — 押し出しループで階段生成
- `snippets/loopcut_bevel_box.py` — 角丸ボックスの最小例
- `snippets/simple_chair.py` — パラメトリック椅子（ヘルパー関数つき）
- `docs/memory/modeling.md` に「Extrude」「ループカット+ベベル」「パーツ組み立てのコツ」セクション追記
- `docs/images/chair_v1.png` — 椅子のレンダリング画像（サイトに掲載）

---

## 2026-05-04: Phase 1 仕上げ + Phase 2 着手（bmesh）+ .gitignore強化

**目標**: Phase 1 の最後「シーンクリーンアップのパターン化」を片付けて Phase 2 の入口（bmesh）まで進む

**実行した手順**:
1. `.gitignore` を強化: `*.blend`, `*.fbx`, `*.glb`, `*.exr`, `*.mp4` などの大容量バイナリをどこに置いても除外。`docs/images/` の Web 用 PNG/JPG は引き続き追跡。`git check-ignore` で全ケース確認済み。
2. `snippets/scene_utils.py` 作成: `clear_all` / `clear_meshes_only` / `setup_basic_scene` / `reset_scene` の4関数で使い分け。
3. `reset_scene()` の動作確認（空シーン → Sun + Camera + テストCube → スクショ目視 OK）
4. **Phase 2 着手**: bmesh で Cube の上面を縮めて台形化（条件付き頂点操作）+ Plane を細分化して sin 波で凹凸（484頂点）。両方とも視覚的に確認できた。

**結果**: 成功。Phase 1 完全消化、Phase 2 の bmesh フローを掴んだ。

**学んだこと**:
- `bmesh.from_edit_mesh()` → 操作 → `update_edit_mesh()` の3ステップは絶対に忘れない
- 編集モード内の `bpy.ops.mesh.subdivide(number_cuts=N)` は **「現在の選択頂点」** に対して効く
- `v.co` は `Vector` なので `.x` `.y` `.z` 直接代入できる。条件分岐で「上面だけ」みたいな選択的編集が簡単
- `mode_set(mode='OBJECT')` で必ずオブジェクトモードに戻すクセが大事

**つまずいた点**:
- `mkdocs.yml` を Edit/Write したとき、ファイル末尾が UTF-8 文字の途中で切れて YAML パースエラー（同位置で2回再