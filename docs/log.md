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

## 2026-05-04: Phase 4 — ライティング・レンダリング全部入り

**目標**: ライト4種比較、Sky Texture 環境光、Cycles vs Eevee、被写界深度の4課題を一気に消化

**実行した手順**:
1. **ライト4種比較**: Suzanne+球+床のシンプルシーンを `replace_light()` ヘルパーで Point→Sun→Spot→Area と切り替えて4枚レンダー。
2. **Sky Texture 環境光**: `setup_sky_world()` で World ノードに `ShaderNodeTexSky` を組み込み。`NISHITA` が無い Blender なので `HOSEK_WILKIE` で代替。空のグラデーションが背景に出るまで確認。
3. **Cycles vs Eevee**: 椅子v3 を両エンジンで同じカメラ設定でレンダー。Cycles=samples=96、Eevee=瞬時。差は金属脚の反射と影の繊細さで顕著。
4. **被写界深度**: 5色球を Y方向に並べて `lens=50, aperture_fstop=2.0, focus_object=spheres[0]` で手前にピント。手前=シャープ、奥=ボケのDoF効果。最初は椅子複製でやろうとしたが構図が崩れたので、シンプルな球並びに変更。

**結果**: 全部成功。Phase 4 完全制覇、画作りの主要要素が揃った。

**学んだこと**:
- Light タイプ別パラメータ: Point=`shadow_soft_size`、Sun=`angle`（太陽の見かけ角）、Spot=`spot_size`/`spot_blend`、Area=`size`/`shape`/`size_y`
- World ノードも `world.use_nodes = True` を立てる必要あり（マテリアルと同じ）
- `ShaderNodeTexSky.sky_type` の選択肢は Blender バージョンで変わる。`NISHITA` が無いときは利用可能なものに自動フォールバックするのが安全
- Cycles の `samples` 96 + `use_denoising=True` が学習用の良いバランス
- Eevee の利用可能 ID は バージョン依存（`BLENDER_EEVEE_NEXT` か `BLENDER_EEVEE`）。実行時に enum_items から判定するのが正解
- DoF の `focus_object` 指定はオブジェクトに追従するので、被写体が動くシーンで便利
- f値（aperture_fstop）は小さいほどボケる。1.4=大ボケ、8=ほぼ全焦点

**つまずいた点**:
- `sky_type='NISHITA'` を指定したらエラー。利用可能な値を表示してくれるエラーメッセージから `HOSEK_WILKIE` に切替。バージョン依存の機能は実行時判定すべき。
- 椅子3つ並べる構図は複製ロジックが複雑になり画も整わなかった。**DoFのデモは複雑な被写体より単純な並びのほうが効果が伝わる**、という構図設計の教訓。

**再利用可能な成果物**:
- `snippets/light_comparison.py` — `replace_light()` ヘルパー＋4種レシピ
- `snippets/sky_environment.py` — Hosek/Wilkie 空モデル
- `snippets/cycles_vs_eevee.py` — エンジン切替＋実行時判定
- `snippets/camera_dof.py` — DoF 設定の最小例
- `docs/memory/lighting.md` 新設（Phase 4 ノウハウ）
- 画像: `light_point.png` `light_sun.png` `light_spot.png` `light_area.png` `env_skytex.png` `engine_cycles.png` `engine_eevee.png` `dof_spheres.png` の8枚

---

## 2026-05-04: Phase 3 — プロシージャル木目 + ノードグラフ + UV

**目標**: PBRテクスチャ・コードでノードグラフを組む・UVアンラップの3課題を一気に消化。Polyhaven が無効なら **プロシージャル質感で代替**（むしろ学習効果は高い）。

**実行した手順**:
1. **Polyhaven 状態確認**: `get_polyhaven_status` → 無効。BlenderMCP パネルのチェックを ON にすれば有効化できる。今回は手続き的に進める。
2. **プロシージャル木目マテリアル**: `make_procedural_wood()` で「TexCoord → Noise → Wave → ColorRamp → BSDF.BaseColor」+「Wave → Bump → BSDF.Normal」の7ノード/7リンクのグラフを Python で構築。
3. **UV アンラップ**: `add_rounded_box()` ヘルパーに `bpy.ops.uv.smart_project(angle_limit=66, island_margin=0.02)` を組み込んで、椅子の各パーツが自動 UV 展開されるように。
4. **椅子 v3 レンダー**: 座面・背もたれにプロシージャル木目、脚は鏡面金属、床はクリーム。Cycles `samples=96` + denoising で `chair_v3_procedural_wood.png` 出力。

**結果**: 大成功。**「マテリアルをコードで組み立てる」というPhase 3 の核心が掴めた**。木目は粒状で味のある質感に。

**学んだこと**:
- ノードグラフは `nt.nodes.new('ShaderNodeXXX')` で生成、`nt.links.new(out, in)` で接続。UI で組むのと完全に同じ構造を Python で書ける。
- ノードタイプ名は **`ShaderNodeBsdfPrincipled` / `ShaderNodeTexNoise` / `ShaderNodeValToRGB` (=ColorRamp)** など先頭大文字
- ソケット名は **UI ラベルそのまま、大小区別あり**: `'Base Color'`, `'Fac'`, `'Vector'`
- `Bump` ノードは Height 入力 → Normal 出力で凹凸感を出す。`Strength` で強度調整。
- `bpy.ops.uv.smart_project` は **編集モード + 全選択** が前提。`angle_limit` 66 が家具の汎用解。
- プロシージャル質感は UV 不要でも動くが、画像テクスチャに移行できるよう UV は貼っておくのが推奨。

**つまずいた点**:
- Polyhaven が無効化されていた（Blender 側のチェックが OFF）。**有効化すれば本物の PBR テクスチャで椅子をリアル木材化できる**。今後ユーザーに ON を依頼する。

**再利用可能な成果物**:
- `snippets/procedural_wood_node_graph.py` — 完全プロシージャル木目（樹種パラメータ調整可）
- `snippets/uv_unwrap_smart.py` — Smart UV Project の最小例
- `docs/memory/materials.md` に「ノードグラフ構築」「樹種レシピ」「UVアンラップ」「Polyhaven連携メモ」追記
- `docs/images/chair_v3_procedural_wood.png` — 進化形3作目

---

## 2026-05-04: Phase 2 完了（ブーリアン）+ Phase 3 着手（着色済み椅子）

**目標**: Phase 2 の最後「ブーリアン」を消化し、その勢いで Phase 3 マテリアル編に入って椅子に色を付ける

**実行した手順**:
1. **ブーリアン**: Cube + Cylinder（X軸貫通）→ Boolean DIFFERENCE で穴あけブロック生成。`solver='EXACT'`、適用後のカッター削除、仕上げベベルまでのフルパターン確認。
2. **Principled BSDF**: `make_material()` / `assign_material()` の2ヘルパー関数で、木・金属・床の3マテリアルを定義。
3. **着色済み椅子**: 座面と背もたれに木マテリアル、4本の脚に金属マテリアル、床にクリーム色を割り当て。
4. **Cycles レンダリング**: `samples=64` + denoising で `chair_v2_material.png` 出力。木の温かさと金属の反射、影のリアルさを確認。

**結果**: Phase 2 完全制覇、Phase 3 入口クリア。**「単色だった椅子に質感が宿った」** 瞬間が一番達成感が大きかった。

**学んだこと**:
- Boolean は **カッターをベースより大きく** が鉄則（同サイズで破綻するパターンを回避）
- `solver='EXACT'` のほうが綺麗、`FAST` は速さ優先のとき
- `mat.use_nodes = True` を忘れると BSDF が触れない（よくあるハマりポイント）
- `bsdf.inputs["Base Color"].default_value` は **RGBA の4要素**、アルファ忘れに注意
- Cycles は `scene.cycles.samples` と `use_denoising` で品質と速度をコントロール
- 「Metallic=0/1, Roughness=0.2〜0.8」の組み合わせだけで木・金属・プラスチック・ゴムが作り分けられる

**つまずいた点**:
- 特になし。Phase 1〜2 で基礎が固まったので、マテリアル追加はスムーズに進んだ。

**再利用可能な成果物**:
- `snippets/boolean_hole.py` — ブーリアンの完全パターン
- `snippets/material_basics.py` — マテリアル作成・割り当てヘルパー
- `docs/memory/modeling.md` に「ブーリアン」セクション追記
- `docs/memory/materials.md` 新設（Phase 3 ノウハウファイル）
- `docs/images/chair_v2_material.png` — 着色済み椅子の Cycles レンダー

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