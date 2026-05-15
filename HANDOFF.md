# BlenderSkill 引継ぎメモ（2026-05-15 時点）

## プロジェクト概要

VRoid キャラ「base_motoko」+ Mixamo モーション 42 ポーズ で、
Stable Diffusion の ControlNet 入力用に **5アングル × 4パス（beauty/depth/normal/openpose）**
画像をバッチ生成するパイプライン。出力はディレクトリ階層 + HTML ギャラリーで閲覧。

- プロジェクトルート: `C:\Users\hoeho\Documents\Claude\BlenderSkill`
- CLAUDE.md に基本ルール・ディレクトリ構成・bash キャッシュ問題が書いてある

---

## 現在のシーン状態

`.blend` 保存先: `blender\project\base_motoko_pose_pipeline.blend`

- VRoid「base_motoko」素体（VRM → FBX (T-Pose) → Mixamo 自動リグ → With Skin DL）
- シェイプキー 65→69 個（VRMから個別復活、ユーザ追加カスタム含む）
- 両手にボクシンググローブ（pivot は wrist、scale 100倍、parent_inverse=Identity パターン）
- Mask Modifier で手の頂点を非表示
- マテリアル: 髪緑、体青水着、靴青、グローブマゼンタ

---

## ポーズ・カメラ・表情設定

すべて `snippets\character_render_poses.py` の上部 dict にまとまっている：

- `POSE_FRAMES`: 41エントリ（livershot_knockdown だけ中央フレームdefault）
- `STANDARD_CAMERA_ANGLES`: front / left_45 / right_45 / left_side / right_side の5アングル
- `CATEGORIES_HEAD_FACE_FORWARD = {"attacks"}` — attacks カテゴリは Track To で頭が常に正面（-Y方向）を向く
- `EXPRESSION_LIST`: 68エントリ（VRoidの単体表情中心、合成系13個は微妙なので削除済み）

ユーザがフレーム指定した motion_memo.md は `blender\project\motion_memo.md` にある。

---

## レンダー出力

`blender\outputs\character\base_motoko\` 配下：

- `poses\<category>\<pose>\<angle>\{beauty,depth,normal,openpose}.png` — 42ポーズ × 5アングル × 4パス
- `expressions\<category>\<expression>\{beauty,depth,normal,openpose}.png` — 68表情 × 4パス

レンダーは MCP タイムアウト対策で **カテゴリ分割で実行**（idles → downd+moves → cinematics → damaged 8+7 → attacks 5+5+4）。

---

## HTML ギャラリー（直近作業）

`snippets\generate_gallery.py` で生成。出力先 `blender\outputs\character\base_motoko\index.html`。

### 構造
- **トップ** `index.html`: ポーズ＆表情を 1枚サムネで一覧、カテゴリでグループ化、リンクで詳細へ
- **詳細（ポーズ）** `poses\<cat>\<pose>\index.html`: 5アングル × 4パスを表示
- **詳細（表情）** `expressions\<cat>\<expr>\index.html`: 4パスのみ表示

### 直近修正した不具合（重要）
1. **インライン画像が原寸 1024px で表示されてた** → 原因は CSS セレクタ `.pass figure a img` の書き間違い。`<figure class="pass">` なので正しくは `figure.pass a img`。`width:100%` が効いてなかった。→ 修正済
2. **クリック時に原寸 PNG が新規タブで開く** → リンクの `target="_blank"` 削除＋ライトボックスJS追加
3. **ライトボックスが viewport より大きく出る** → `width:85vmin / height:85vmin` 固定＋`object-fit:contain` で短辺基準 85% に強制縮小
4. **ブラウザの file:// キャッシュが頑固** → デバッグ用にピンクの BUILD 帯を一時的に出した（**確認後の今は削除済**）

### 現状の見え方
- インラインサムネは **220px 固定の auto-fill グリッド**
- サムネクリックで **ライトボックス**（85vmin、Esc または背景クリックで閉じる）
- 背景スクロールは `body.lb-open { overflow:hidden }` で抑止

---

## 既知の落とし穴・ハマりどころ

### 1. Cowork bash サンドボックスのキャッシュ問題（CLAUDE.md 参照）
`mcp__workspace__bash` から Windows 側マウントを `ls`/`find` すると **最大1時間古い** 状態が返る。
→ ファイル存在確認は **Glob/Read ツール**を使う。書き込みも bash 経由だと失敗することあり、**Blender MCP の `execute_blender_code` で Python 直接実行**が確実。

### 2. ギャラリー再生成は Blender 経由で
```python
import importlib.util
spec = importlib.util.spec_from_file_location("g",
    r"C:\Users\hoeho\Documents\Claude\BlenderSkill\snippets\generate_gallery.py")
mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
mod.generate()
```

### 3. CSS セレクタは要確認
`figure.pass` と `.pass figure` は別物（前者は要素＋クラス、後者は子孫）。今回ハマった。

### 4. file:// プロトコルのブラウザキャッシュ
Ctrl+F5 が効かないことがある。URL に `?v=2` 等付けると確実に再読み込み。

---

## 次にやりそうなこと（候補）

- **シェイプキー追加**: ユーザがネットでシェイプキーについて調べた後、BRW+EYE+MTH の合成表情を再検討するかも
- **オーバーレイテクスチャ**: 顔の涙・怒りマーク・赤面の上書きテクスチャ系（未着手）
- **ControlNet 実投入テスト**: 生成した画像を実際に Stable Diffusion に投げて品質確認
- **新ポーズ追加**: Mixamo から追加DLしてフレーム決め＆レンダー

---

## 主要ファイル一覧

| パス | 役割 |
|---|---|
| `CLAUDE.md` | プロジェクトルール（公開しない） |
| `snippets\character_setup.py` | シーン初期化（カメラ・ライト・FBX読込） |
| `snippets\character_render_poses.py` | メインレンダーパイプライン |
| `snippets\generate_gallery.py` | HTMLギャラリー生成 |
| `blender\project\base_motoko_pose_pipeline.blend` | 保存済みシーン |
| `blender\project\motion_memo.md` | ユーザ指定のポーズ別フレーム表 |
| `blender\outputs\character\base_motoko\index.html` | ギャラリートップ |

---

## 直近セッションの未完タスク
なし。ギャラリーの不具合修正＋ピンクの BUILD 帯削除まで完了済。
