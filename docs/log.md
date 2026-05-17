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

## 2026-05-17: Phase 8 — base_motoko を Apply All Transforms 済みでクリーン再構築

**目標**: 旧 base_motoko は Mixamo FBX import の典型的な状態 (Armature rotation_euler=(90°,0,0), scale=0.01) を抱えていて、Combat シーン等で「ポーズ前進方向と座標軸がズレる」問題があった。Apply All Transforms で armature/mesh の全 transform を単位元 (rot=0, scale=1) にした **クリーンな base_motoko** に作り直す。ただし42個のPose Asset、ユーザーカスタム編集 (pose_hook の右腕角度等)、Face shape key、boxing gloves bone parent 設定、Face Overlay マテリアル等 **全て保持** すること。

**実行した手順**:

1. **Phase 1: 素体クリーン構築**
   - 空シーンに `base_motoko.fbx` を import → Armature rot=(90°,0,0), scale=0.01 を確認
   - 全選択して `bpy.ops.object.transform_apply(rotation=True, scale=True)` で Apply All Transforms
   - 結果: Armature dim Z=1.875m, 全mesh rot=0/scale=1, 足元 Z=0.003m で接地
2. **Phase 2: アニメ再生検証** (ユーザーから「先にアニメで動かしてみよう」と提案)
   - 旧blendから pose_hook action を append → assign → Hips が world(14.9, -95.7, -23.6) に飛ぶ
   - 原因: 旧 action の Hips location キーフレームは cm 単位 (100倍値)。旧Armature scale=0.01でつじつまが合っていたが、Apply Scale 後はそのまま100倍に見える
   - 対処: Hips location チャネルを /100 補正 → 完璧に動く
   - Hook.fbx (89フレーム長尺アニメ) でも同様に補正 → 完璧再生
3. **Phase 3: アニメ取り込みユーティリティ作成** (`snippets/retarget_mixamo_action.py`)
   - `mixamorigN:` プレフィックス自動正規化 (既存armatureがある状態でimportすると `mixamorig1:` 等にリネームされる問題)
   - Hips location キーフレーム /100 補正
   - 一時import object 自動クリーンアップ
   - `batch_retarget()` でフォルダ一括処理対応
4. **Phase 4: 42 Pose Asset 移植**
   - 旧blendから `pose_*` 全42個 append → 同じ /100 補正適用
   - 全 Pose Asset (Asset Browser 対応) として保持
   - ユーザーカスタムの pose_hook 右腕角度も保持確認
5. **Phase 5: グローブ装着**
   - 旧 boxing_gloves.L/R をbone parent ごと append
   - 重要: 旧Character.001 も T-pose に明示リセットしてから world transform 取得
   - `matrix_parent_inverse` を再計算して新Character の手首位置に world transform 維持で再 parent
   - 結果: T-pose 時 world diff=0.000000m で完璧装着
6. **Phase 6: Face shape key 移植**
   - 旧Face mesh の 58個 shape key (Basis+57) を新Face mesh に転送
   - Blender標準の `bpy.ops.object.join_shapes()` は **1個まとめてしか作らない** ため使用不可
   - スクリプトで個別に `new_face.shape_key_add(name=...)` → vertex coord copy
7. **Phase 7: 手のメッシュ非表示**
   - グローブから指が出るので、Body に Mask Modifier 追加
   - `mixamorig:*Hand*` 系32個の vertex group の頂点を統合 vertex group `hands_mask` に集約 (1664頂点)
   - Mask modifier (invert=True) で非表示
8. **Phase 8: テクスチャ差し替え** (`face_skin_matched` / `shoes_blue` / `hair_front_a_green` / `boxing_gloves_texture_magenta` / `..._padded_with_swimsuit_recolor`)
   - **Blender の image filepath 変更後の cache バグ** に遭遇: filepath 変えて reload しても viewport の見た目が更新されない
   - 対処: image data block を完全削除 → 新規 `bpy.data.images.load()` → 全 material node の参照を新 image に置換 → 旧名でリネーム
9. **Phase 9: Material node graph 完全コピー** (←最大の発見)
   - テクスチャ差し替えしても **Face の見た目がアニメ調にならない** (目・口・眉が消えた状態)
   - 原因判明: 旧 Face material は **VRoid Add-on で組まれた FaceOverlayMix1→2→3 チェイン** で、複数オーバーレイ画像を Mix で合成して目・口・眉等を表示していた
   - Mixamo経由 FBX import で **Mix node 構造が完全に失われた** ため、新Face material は単純な Principled BSDF + 1枚 image だけになっていた
   - 解決: 旧blendから 12個の material を node graph ごと append → 新mesh の material_slot を旧版に差し替え → 旧material 内の image 参照 (30個) を canonical な新版 (face_skin_matched 等) に置換
10. **Phase 10: 旧 base_motoko のアーカイブ + フォルダリネーム**
    - 旧 `library/characters/base_motoko/` → `_archive/base_motoko_old/` に移動、`base_motoko.blend` → `base_motoko_old.blend` にリネーム
    - 新 `base_motoko_2/` → `base_motoko/` にフォルダリネーム、`base_motoko_2.blend` → `base_motoko.blend` にファイルリネーム

**結果**: 成功 (9.6 MB の極小サイズに収まる)

**学んだこと**:

- **Apply All Transforms は Mixamoアニメと完全互換**: 補正は Hips location チャネル /100 のみ。ボーン回転は座標系不変なのでそのまま動く
- **Pose Asset は何度でも再利用可能**: 旧blendから append → /100 補正で、ユーザーカスタム編集ごと完全継承できる
- **Mixamo経由FBXは VRoid material 構造を破壊する**: Face Overlay などの Mix node チェインは保持されない。これに気付かないと「テクスチャ差し替えしても見た目変わらない」の沼にハマる
- **テクスチャ差し替えで cache バグに遭遇したら**: `image.filepath = new` + `image.reload()` ではダメ。`bpy.data.images.remove()` → `bpy.data.images.load()` → 全 material node 参照差し替え、で確実
- **bone parent の matrix_parent_inverse 計算**: `parent_matrix = arm.matrix_world @ pose_bone.matrix @ Matrix.Translation((0, bone.length, 0))` (bone の tail を origin にぶら下がる仕様)
- **join_shapes は Blender 5.x では複数 shape key を一気にcopy できない**: スクリプトで vertex coord 個別 copy が必要

**つまずいた点**:

- 「靴下のグレー」を「靴のメッシュ」と勘違いして material BSDF をいじり倒した → 実は **足ボーンの表示** だった。ユーザーに「色は変わらない、ボーンだ」と指摘されて気付いた
- 「髪がオレンジ」と思って戸惑った → object 選択枠のオレンジ色だった
- material 移植時、BSDF input default value (Metallic/Roughness) だけ見て合わせて「旧と同じ」と報告した → 実は **node graph 構造 (Mix チェイン)** が全然違っていた。「node graph 全体」レベルで比較するべきだった
- **これがユーザーを長時間イライラさせた最大原因**: 表面パラメータだけでなく、material の **接続構造** を最初から確認すべき

**再利用可能な成果物**:

- `snippets/retarget_mixamo_action.py` — Mixamo FBX 取り込み補正ユーティリティ (ボーン名正規化 + Hips loc /100)
- `library/characters/base_motoko/base_motoko.blend` (9.6 MB) — クリーン素体 + 42 Pose Asset + Face Overlay material + magenta gloves
- `library/characters/_archive/base_motoko_old/base_motoko_old.blend` (92 MB) — 旧版アーカイブ (心配なときの safe net)

**残タスク**:

- `scenes/combat/combat_template.blend` と `scenes/single_render/base_motoko_pose_pipeline.blend` の中の base_motoko を、新版で再 append する作業 (旧構造のまま残っている)

---

## 2026-05-15: Phase 7 — 42ポーズ×5アングル×4パス量産 + HTMLギャラリー構築

**目標**: base_motoko を本格運用に乗せる。Mixamoから42モーションを追加DLし、各ポーズに **5方向のカメラ** からレンダーする多角度パイプラインへ拡張。さらに68種類の表情も追加レンダー。最終的に **840+272枚** の生成画像を階層型HTMLギャラリーで閲覧できる状態にする。

**実行した手順**:

1. **シェイプキー復活**: VRM→FBX→Mixamoの往復で消えていた58個のVRoid表情シェイプキーを、`join_shapes` 非依存で頂点座標を手動コピーする方式で個別復元（VRoidの`Face.003`から`base_motoko_Body`へ）
2. **シェイプキー並べ替え**: `bpy.ops.object.shape_key_move` を「現在位置を毎回再取得 → UP方向のみで挿入ソート」する `while True` パターンで安定収束させた（単純なindexベースのソートは100iter以上収束せず）
3. **ボクシンググローブ装着**:
   - Hyper3D 系で生成、両手の手首ボーンに `parent_type='BONE'` で装着
   - **pivotがfingertipsに来る問題** → 3Dカーソルを bone head（手首）に移動 → `bpy.ops.object.origin_set(type='ORIGIN_CURSOR')` で原点を手首に移動
   - **scale 100倍 + parent_inverse=Identity + location=(0,-bone_length,0)** で正しい位置に配置（Mixamoアーマチュアの 0.01スケールとの相殺）
   - Mask Modifier + 頂点グループで手のメッシュを非表示
4. **モーション一覧テーブル作成**: `blender/project/motion_memo.md` をユーザに記入してもらい、42ポーズの「撮影フレーム」を確定（hookは37、idleは1、upperは22 etc）
5. **5アングルカメラシステム**: `character_render_poses.py` に `STANDARD_CAMERA_ANGLES` を追加（front / left_45 / right_45 / left_side / right_side、距離4.5m）。キャラのspineを基準に毎フレーム動的に再配置
6. **頭の向き制御**: `CATEGORIES_HEAD_FACE_FORWARD = {"attacks"}` でattacksカテゴリだけ Track To constraint で頭を常に -Y 方向（仮想対戦相手）に向ける
7. **大量レンダー実行**: MCP タイムアウト対策のため、カテゴリ分割で順次実行（idles → downd+moves → cinematics → damaged 8+7 → attacks 5+5+4）。**42ポーズ×5アングル×4パス = 840枚** + **68表情×4パス = 272枚** = 計1112枚
8. **階層型HTMLギャラリー作成**: `snippets/generate_gallery.py` を新規作成
   - トップ `index.html`: 110アイテムをカテゴリ別にサムネ一覧
   - 詳細（ポーズ）: 5アングル×4パス＝20枚を1ページに
   - 詳細（表情）: 4パスを1ページに
   - **画像クリック→ライトボックスでviewportにフィット**（85vmin強制縮小）

**結果**: **成功**。実用レベルのControlNet入力パックが完成。ローカルブラウザでサクサク閲覧可能。

**学んだこと**:
- **CSSセレクタの「子孫」と「要素＋クラス」の罠**: `<figure class="pass">` に対して `.pass figure a img` と書くと figure 自身は対象外（descendant selector は祖先を要求）。正しくは `figure.pass a img`。30分ハマった
- **vmin単位の有効性**: ライトボックスで `max-width:95vw / max-height:95vh` だと 1024px画像が1920×1080画面でまったく縮小されない（95vh=1026px、すり抜ける）。`width:85vmin / height:85vmin` + `object-fit:contain` で必ず短辺基準85%に強制縮小できる
- **シェイプキーは個別コピーが必要**: Blenderの `join_shapes` 演算子は「全シェイプの差分を1つに合成」してしまう。58個を個別に保ちたい場合は、ソース・ターゲット両方を `eval_get` した上でループで `shape_key_add` + 頂点座標コピーが必要
- **Bone parent + 子オブジェクトのスケール処理**: 親アーマチュアがscale=0.01だと、子オブジェクトはローカルでscale=100倍にしないと実寸にならない。さらに `matrix_parent_inverse` を手動でIdentityに設定しないと座標が二重補正される
- **Cowork bashキャッシュは書き込みも壊す**: bash経由でWindowsマウントに書き込もうとすると古いキャッシュ状態で「ディレクトリが存在しない」エラーが出る。Blender MCPの `execute_blender_code` で Python を直接Windows側プロセスで実行するのが確実

**つまずいた点**:
- ライトボックスの画像が原寸表示される → 何度も試行錯誤後、原因は **インラインのCSSセレクタが効いてなかった** だけだった（ライトボックスは正しく動いてた）。ユーザのスクリーンショットで「インラインのサムネが大きい」と気づいて判明
- BUILD タイムスタンプ帯をデバッグ用に表示 → file:// プロトコルでブラウザキャッシュが頑固な問題と切り分けできた

**再利用可能な成果物**:
- `snippets/generate_gallery.py` (階層型HTMLギャラリー生成、ライトボックスJS+CSS同梱)
- `snippets/character_render_poses.py` 拡張版（5アングルカメラ、Head Track To、表情リスト68個）
- `blender/project/motion_memo.md` (42ポーズのフレーム表)
- `blender/project/base_motoko_pose_pipeline.blend` (シェイプキー69個・グローブ装着・全マテリアル設定済み)
- 出力: `blender/outputs/character/base_motoko/index.html`（ローカル閲覧用）

**Phase 7 ステータス**: **完了** ✅

次のフェーズ候補:
- ComfyUI実機でのControlNet通し検証
- オーバーレイテクスチャ系（涙・怒りマーク・赤面）
- 追加ポーズ・追加キャラ

---

## 2026-05-14: Phase 6 第2段 — VRoid (base_motoko) × 同7ポーズで再走、最終ゴール達成

**目標**: 自作VRoidキャラ (base_motoko.vrm) を Mixamo に再アップロードして自動リグ → 既存パイプラインに乗せて「自前キャラ × 複数ポーズ」を完成させる。

**実行した手順**:
1. VRM Add-on for Blender (v3.26.8) で `base_motoko.vrm` をインポート → 127ボーンのHumanoid Tポーズで読み込み確認
2. `snippets/vrm_to_fbx_for_mixamo.py` を新規作成: VRMインポート → アーマチュア込みでFBXエクスポート
3. **1回目失敗**: Mixamoにアップしたが、ダウンロードしたFBXのボーン名が `J_Bip_C_Hips` 等のVRoid Humanoid命名のまま。auto-rigが走っていない
4. **原因特定**: `object_types={'ARMATURE', 'MESH'}` で出していたため、Mixamoが「既にリグ済み」と判定してauto-rig画面そのものをスキップしていた
5. `vrm_to_fbx_for_mixamo.py` を `object_types={'MESH'}` に変更して再エクスポート
6. ユーザがMixamoに再アップロード → 今度はauto-rigger画面が出て、ジョイントマーカー配置 → auto-rig完了 → With Skin/T-Pose でDL
7. 新FBXをBlenderにインポート → ボーン名が `mixamorig:Hips` 等の Mixamo 命名に変わったことを確認（65ボーン、Jennifer同等）
8. `character_render_poses.py` で全7ポーズ一括レンダー → `blender/outputs/character/base_motoko/poses/` に 7×4=28枚生成
9. .blend保存: `blender/project/base_motoko_pose_pipeline.blend` (25MB)

**結果**: **成功**。Jenniferとbase_motokoで同じパイプラインを通せることを実証。最終ゴール「複数キャラ × 複数ポーズの量産」基盤が完成。

**学んだこと**:
- **Mixamo auto-rigはメッシュのみのFBXを期待する**。アーマチュア込みで投げるとauto-rigスキップされ、元のリグのまま返ってくる罠 → `object_types={'MESH'}` 必須
- VRoidキャラのFBXは VRM Add-on でVRMを読み込めば中間ファイルを作れる。`use_mesh_modifiers=True` でT-poseバインドが焼き込まれる
- Mixamo経由でMToonシェーダーは失われるが、**実レンダー結果は意外と綺麗**（ビューポートのSolidモードだけマゼンタに見える）。ControlNet用途なら問題なし
- 既存のスニペット (`character_setup.py`, `character_render_poses.py`) は **キャラのFBXパスを切り替えるだけ**で別キャラに転用可能。汎用性が証明された

**つまずいた点**:
- 1回目のMixamoアップで「auto-rigが走らないバグ？」と疑ったが、実は仕様（アーマチュア入りFBXのスキップ動作）。回避策のために `motoko_v2.fbx` というy軸+1mmずらした別ファイルまで作ったが、結局アーマチュア除外で解決した（v2は不要だった）
- ビューポートでマゼンタ顔・髪欠落に見えて慌てたが、レンダー結果は綺麗 → Solidビューポートと Eevee レンダーの評価の差を理解する必要

**再利用可能な成果物**:
- `snippets/vrm_to_fbx_for_mixamo.py` (VRM→Mixamo向けFBX変換、mesh-only版)
- `blender/project/base_motoko_pose_pipeline.blend` (base_motokoシーン)
- `docs/memory/character.md` に「VRoid → Mixamo の落とし穴」セクション追加

**Phase 6 ステータス**: **完了** ✅

次のフェーズ候補:
- ComfyUIで実際にControlNetを通して画像生成、品質検証
- 別キャラ追加（VRoidで複数体）
- 別ポーズ追加（Mixamoから新規モーションDL）
- マテリアル本格復元（MToonライクなトゥーンシェーダー再構築）

---

## 2026-05-14: Phase 6 着手 — Jennifer × 7ポーズ ControlNet入力量産

**目標**: AI画像生成（Stable Diffusion + ControlNet）の入力画像を Blender で量産する基盤を作る。1キャラに対し、Mixamoの複数モーションFBXからポーズだけを抜き出して当て、Beauty / Depth / Normal / OpenPose の4種類PNGを一括出力するパイプラインを構築。

**調べた情報**:
- Mixamo は素体FBXに対して「Without Skin」でモーションだけのFBXがDLでき、ボーンは Mixamo命名規則で統一されている
- ControlNet 4入力（Depth, OpenPose, Canny素材=Beauty, Normal）の規格と色付け
- Blender 5.1.1 のコンポジタAPI（5.x で大改修されている）

**実行した手順**:
1. **計画＆フォルダ準備**: `docs/tasks.md` に Phase 6 を追加、`assets/mixamo/` と `outputs/character/poses/` を作成
2. **素材取得**（ユーザ作業）: Jennifer (With Skin, T-Pose) と 7モーション (Without Skin) をMixamoからDL
3. **スニペット作成**:
   - `snippets/character_setup.py`: クリーンシーン → Jenniferインポート → カメラ・ライト・レンダー設定
   - `snippets/character_render_poses.py`: ポーズ転写 → 4種類画像生成 のメインパイプライン
4. **デバッグ反復**（ここが本日の山場、5.x の罠の連発）:
   - `scene.node_tree` が無い → `scene.compositing_node_group` に変更
   - `MixRGB`/`MapRange` 等のノードが消失 → Depth/Normal は生EXRで書き出して numpy で後段処理
   - `OutputFile.base_path` → `directory`、`file_slots` → `file_output_items`
   - `format.media_type = 'IMAGE'` を立てないと OPEN_EXR_MULTILAYER 固定 になる
   - Pillow が入っていない → numpy + `bpy.data.images.new()` + `image.save_render()` で全PNG出力に切替
   - ボーン名が `mixamorig1:` になっていた（重複回避でユニーク化） → 接尾辞マッチに変更
   - Jennifer に `Armature|mixamo.com|Layer0` アクションが勝手にバインドされていて、`frame_set(1)` で T-pose に巻き戻る → インポート直後に `animation_data.action = None` で外す
5. **全7ポーズの一括レンダー**: `boxing`, `hook`, `idle`, `receiving_a_big_uppercut`, `running`, `victory`, `walking` で 7×4=28枚生成
6. **目視確認**: Idle / Victory / Boxing / Running の4ポーズが明確に別物、OpenPose 18点全て可視、Depth はクリーンなシルエット、Normal は教科書通りの色配置

**結果**: **成功**。`outputs/character/poses/<pose_name>/` 配下に `beauty.png` / `depth.png` (16bit) / `normal.png` / `openpose.png` が全7ポーズ分揃った。そのまま Stable Diffusion の ControlNet に流せる品質。

**学んだこと**:
- Blender 5.x はコンポジタを「Realtime Compositor」として書き直し中で、3.x/4.x のサンプルコードはほぼ全滅する。`Scene.compositing_node_group`, `OutputFile.directory`, `format.media_type = 'IMAGE'` の3点をまず知っていれば足りる
- Mixamo の「Without Skin」FBXからポーズだけ転写する方式は、リギング知識ゼロでも回せる優秀なテクニック。両側Mixamoボーン命名で接尾辞マッチすればVRoidや他のリグへの展開も可能
- インポート時に勝手につくアクションは、後段でposeを上書きする処理と相性が悪い。**素体を読み込んだら即 action=None** が定石
- OpenPose 画像は Blender からアーマチュアのボーン頭尾をカメラ平面に投影＋numpyで描画するだけで自前生成できる。OpenPose検出器を後段で使う必要なし

**つまずいた点**:
- `if __name__ == "__main__": main()` ガードが `exec(open(...).read())` でスキップされる → `importlib.util.spec_from_file_location` でモジュール化して `mod.main()` 直叩きに
- 「コンポジタが動いてるが何も出力されない」状態にハマる。原因は `file_output_items` の追加忘れ＋`media_type` の初期値
- Pillow が無いことに気づくのに少し時間がかかった（試行錯誤の途中でPILが在ったように見えた瞬間があったが、新規モジュール環境では消えていた）

**再利用可能な成果物**:
- `snippets/character_setup.py` (Jenniferをスケール正規化＋カメラ/ライト/レンダー設定)
- `snippets/character_render_poses.py` (ポーズ転写＋4種類画像出力パイプライン、Pillow非依存)
- `docs/memory/character.md` (Phase 6 のノウハウ・ハマリ全集)
- `docs/snippets/character_setup.md`, `docs/snippets/character_render_poses.md`

**次に向けて**:
- 次回: VRoid VRMキャラを Mixamo に再アップロードして再リグ → 同じパイプラインに乗せて「VRoidキャラ × 複数ポーズ」を実現
- VRoid のトゥーンシェーダーは Mixamo再リグで失われるので、Principled BSDF から NPR寄りシェーダーへの再構築が次の課題
- ControlNet 実機テスト（出力画像を実際に Stable Diffusion に通して品質検証）

---

## 2026-05-04: フォローアップ — 集大成シーンを保存

**目標**: 集大成作品を「再開できる状態」にする

**実行した手順**:
1. **`.blend` 保存**: `bpy.ops.wm.save_as_mainfile(filepath=..., compress=True)` で `outputs/final_snowy_chair.blend`（220KB、圧縮済み）に保存。`.gitignore` の `*.blend` で除外済みなので git には上がらない（ローカル専用）。
2. **スクリプト保存忘れ修正**: 集大成のコード本体を `snippets/final_snowy_chair.py`（192行）として保存。`docs/snippets/final_snowy_chair.md` から `pymdownx.snippets` で参照できるように更新。
3. **再現性の確認**: スクリプトだけでシーンを再構築できる。`.blend` ファイルがあれば即時再開、無くてもスクリプト実行で完全復元可能。

**学んだこと**:
- **作品スクリプトはセッションごとに必ず `snippets/.py` に保存する**（インライン実行だけだと履歴に残らない）
- `.blend` は `compress=True` で大幅に縮む（800オブジェクト=220KB）
- 「コード = 真実」「.blend = 編集作業の出発点」という二重管理が安全

**再利用可能な成果物**:
- `outputs/final_snowy_chair.blend` — 開けば即編集可能なシーン（git追跡外）
- `snippets/final_snowy_chair.py` — コードから完全再現

---

## 2026-05-04: Phase 5 完了 — アニメ / パーティクル / ジオメトリノード / AI生成 / 集大成作品

**目標**: 応用編5項目を全部消化し、**Phase 1〜5 の集大成シーン** を1本のスクリプトで再現できる状態にする。

**実行した手順**:
1. **キーフレームアニメ**: Suzanne を Z軸回転＋上下動でループアニメ化（24fps、60フレーム）。3つの代表フレーム（1/30/60）をレンダー。
2. **パーティクル → 散布へ切替**: 本物のパーティクルシステムは設定したものの雪片が見えなかったので、**Linked Duplicate で球600個を散布** する確実方式に変更。雪が積もる絵が一発で出た。
3. **ジオメトリノード**: `GeometryNodeDistributePointsOnFaces` + `InstanceOnPoints` + `ObjectInfo` + `RealizeInstances` + `JoinGeometry` の標準パターンで Plane に立方体を散布。**Blender 4.0+ の interface API**（`ng.interface.new_socket`）対応。最初は散布元が原点になく空中に飛んでた → 修正で岩場の絵に。
4. **AI生成（Hyper3D / Hunyuan3D / Sketchfab）**: 全部 OFF だったので有効化手順とワークフローを完全文書化。次回 ON 後にすぐ使える状態に。
5. **集大成シーン**: 雪景色の椅子（プロシージャル木目 + 鏡面金属脚 + Sky Texture曇り空 + DoF + 800個の雪片散布 + Cycles）を1本のスクリプトで構築。Phase 1〜5 の技を全部使った作品が完成。

**結果**: Phase 5 完全制覇 + 全フェーズ統合作品まで完了。**5段階のロードマップが全部 ✅** に。

**学んだこと**:
- `obj.keyframe_insert(data_path="location", frame=N)` で記録、属性を **変更してから** insert するのが鉄則
- パーティクルシステムは設定が複雑で学習中は散布スクリプトのほうが確実
- Linked Duplicate は `new = template.copy()` だけで `new.data = ...` を **やらない** のがポイント
- ジオメトリノードの散布元は **原点に置いて hide_render**（ワールド位置がオフセットになるため）
- Blender 4.0+ の `ng.interface.new_socket(name=..., in_out='INPUT', socket_type='NodeSocketGeometry')` API
- `JoinGeometry` の入力は **複数接続可能**（元メッシュ + 散布結果の両方を繋いで合成）
- AI生成系（Hyper3D/Hunyuan3D/Sketchfab/Polyhaven）はチェックボックス ON で全部使える、ワークフローはどれも `生成 → poll → import` の3ステップ

**つまずいた点**:
- パーティクルが見えない問題: 物理シミュレーションのステップ評価とレンダリングフレームのタイミングの絡みで複雑。学習用なら散布スクリプトに切り替えるのが楽。
- ジオメトリノードの散布元オブジェクトが (20,20,0) にあって全部空中に出た。原点に置いて非表示が定石。
- 集大成作品で雪片が床と同色のため見えにくい。次回は薄青や淡い色で差別化。

**再利用可能な成果物**:
- `snippets/keyframe_animation.py` — キーフレーム最小例
- `snippets/snow_scatter.py` — Linked Duplicate 散布パターン
- `snippets/geometry_nodes_scatter.py` — `add_scatter_modifier()` ヘルパー（Blender 4.0+ 対応）
- `snippets/ai_model_workflow.py` — AI生成・外部アセット連携の完全ワークフロー
- `docs/memory/animation.md` 新設（Phase 5 ノウハウ）
- 画像5枚: `anim_frame{1,30,60}.png` `particles_snow.png` `geonodes_scatter.png` `final_snowy_chair.png`

**Phase 1〜5 を通した総括**:
- 全5フェーズ消化、画像作品15枚以上、スニペット20本以上、ノウハウ5カテゴリ
- 「ネット検索 → Blender実行 → 振り返り → ノウハウ蓄積」のサイクルが完全に回る状態に
- 次は **作品ターゲット（部屋・食べ物・小道具・キャラ）** に挑戦できる土台が整った

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