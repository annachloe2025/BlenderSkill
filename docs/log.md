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
- `mkdocs.yml` を Edit/Write したとき、ファイル末尾が UTF-8 文字の途中で切れて YAML パースエラー（同位置で2回再現）。bash の `cat > ...` ヒアドキュメントで書き直したら正常。長い日本語末尾の YAML/MD は bash 直接書き出しが安全という教訓。

**再利用可能な成果物**:
- `snippets/scene_utils.py` — シーン管理4関数
- `snippets/bmesh_basics.py` — bmesh 頂点操作の2例
- `docs/memory/modeling.md` — Phase 2 用ノウハウファイル新設
- `.gitignore` 強化版（大容量バイナリ全種カバー）

---

## 2026-05-04: Phase 1 — トランスフォーム / グリッド配置 / モディファイア

**目標**: Phase 1 の「トランスフォーム」「グリッド配置」「モディファイア入門」を一気に消化

**実行した手順**:
1. **トランスフォーム**: 4つの Cube を「基準・回転のみ・スケールのみ・全部」のパターンで配置。`math.radians()` で度数→ラジアン変換、`Vector` / `Euler` の使い分けも実例化。
2. **グリッド配置**: 5×5=25個の UV Sphere を、中心からの距離で sin 波を高さに反映させて配置。`bpy.ops.object.shade_smooth()` も適用。
3. **モディファイア**: Subdivision Surface / Bevel / Mirror をそれぞれ別 Cube に適用。`obj.modifiers.new(name=..., type=...)` の基本パターンを確認。

**結果**: 3つとも成功。スクリーンショットでも結果を確認済み。

**学んだこと**:
- `obj.location.z += 5` のような **属性アクセス＋複合代入** が便利（Vector のおかげ）
- 中心揃えグリッドの定番計算: `(i - (N - 1) / 2) * spacing`
- モディファイアは `obj.modifiers.new(...)` で生やし、戻り値を変数に受けてプロパティ設定するのが定石
- Mirror は **オブジェクトの原点が対称軸**。ローカル座標で動く

**つまずいた点**:
- Bevel は `width=0.15` だと遠目では効きが分かりにくかった。検証時は近めの構図にするか、初期値を大きめにすると確認しやすい。

**再利用可能な成果物**:
- `snippets/transform_basics.py` — トランスフォーム3パターン
- `snippets/grid_arrangement.py` — NxN グリッド配置（波形高さ）
- `snippets/modifiers_intro.py` — Subsurf / Bevel / Mirror
- `docs/memory/basics.md` に「トランスフォーム応用」「グリッド配置」「モディファイア基本」セクション追記

---

## 2026-05-04: Phase 1 開始 — 接続テスト & 5プリミティブ配置

**目標**: Blender MCP接続確認 → プリミティブを5種類並べて配置

**実行した手順**:
1. `get_scene_info` で接続確認（デフォルトシーン: Cube/Light/Camera）
2. `get_viewport_screenshot` でビューポート目視
3. シーンクリア → cube/sphere/cylinder/cone/torus を X 軸に1.8間隔で配置
4. Sunライト・カメラを追加してアクティブカメラに設定
5. スクリーンショットで結果確認

**結果**: 成功。5プリミティブが綺麗に並び、ライト・カメラも正常に配置された。

**学んだこと**:
- `bpy.ops.object.select_all(action='SELECT')` + `delete()` でシーン全消しが最短
- プリミティブ追加直後の `bpy.context.active_object` ですぐ参照できる
- `bpy.context.scene.camera = obj` でアクティブカメラを切り替えられる

**つまずいた点**: 特になし

**再利用可能な成果物**:
- `snippets/clear_scene.py` — シーン全消し
- `snippets/add_primitives_row.py` — 5プリミティブ配置
- `memory/basics.md` — 基本操作のリファレンス追加

---

## 2026-05-04: プロジェクト初期化

**目標**: BlenderSkill プロジェクトのフォルダ構成を作成

**実行した手順**:
1. `C:\Users\hoeho\Documents\Claude\BlenderSkill` フォルダを作業ディレクトリとして接続
2. `CLAUDE.md`、`LOG.md`、`TASKS.md` を作成
3. `memory/`、`snippets/`、`outputs/` ディレクトリを作成

**結果**: 成功

**次のアクション**: `TASKS.md` から最初のタスクを選んで開始する
