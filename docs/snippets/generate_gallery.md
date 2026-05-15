# generate_gallery.py

`character_render_poses.py` が大量に出力したPNG群を **階層型HTMLギャラリー** にして、ローカルブラウザで快適に閲覧できるようにするスクリプト。Pythonの標準ライブラリだけで動く（Blender不要、外部依存ゼロ）。

## コード

```python
--8<-- "snippets/generate_gallery.py"
```

## 出力構造

```
outputs/character/<キャラ名>/
├── index.html                           # トップ: 全アイテムをカテゴリ別サムネ表示
├── poses/<category>/<pose>/
│   ├── index.html                       # 詳細: 5アングル × 4パス
│   └── <angle>/{beauty,depth,normal,openpose}.png
└── expressions/<category>/<expr>/
    ├── index.html                       # 詳細: 4パス
    └── {beauty,depth,normal,openpose}.png
```

## 設計のポイント

### 1. スキャンは2モード

`scan_section(section_root, has_angles=False/True)` で配下を `os.walk` する。

- **`has_angles=True`** (poses 用): `category/name/angle/` の3階層を期待
- **`has_angles=False`** (expressions 用): `category/name/` の2階層

戻り値は `(category, name, item_rel, variants)` のリスト。`variants` は `{angle名: {pass名: 相対パス}}` の dict。

### 2. インラインサムネは固定幅グリッド

```css
.pass-grid { display:grid;
             grid-template-columns: repeat(auto-fill, 220px);
             gap:12px; }
figure.pass a img { width:100% !important; height:auto !important; }
```

viewport幅に応じて列数が変わる auto-fill にして、各セルは **220px固定**。横並びが多すぎないので 1024×1024 のレンダー画像でもサムネ感を維持できる。

### 3. ライトボックスは vmin で強制縮小

```css
.lightbox img { width:85vmin !important;
                height:85vmin !important;
                object-fit:contain !important; }
```

**`max-width:95vw`** だけだと 1024px画像が大きい画面では制約を素通りする（1920×1080なら 95vw=1824px、画像は1024でフィット）。これだと「縮小されない」と感じるので、`width:85vmin` で短辺基準85%に **強制リサイズ** + `object-fit:contain` でアスペクト保持。

### 4. リンクから `target="_blank"` を外す

`<a target="_blank">` を残すと、JSがクリックを取りこぼした場合に **原寸PNGが新規タブで開く**。これを嫌ってリンクからは `target` を消し、`e.preventDefault()` でライトボックス専用に。万一JSが死んでも新規タブが乱発するリスクがない。

## CSSセレクタの罠（実際にハマった）

```html
<figure class="pass">
  <a><img></a>
</figure>
```

このHTMLに対して、

| セレクタ | マッチ |
|---|---|
| `.pass figure a img` | ❌ figure 自身は対象外（祖先に `.pass` が要る） |
| `figure.pass a img` | ✅ figure に class があるのでマッチ |
| `.pass a img` | ✅ class からの子孫として a → img |

descendant combinator は **「祖先＋子孫」** であって、要素そのものは含まない。`<figure class="pass">` を指したいなら `figure.pass` と書く。

## 使い方

```bash
python snippets/generate_gallery.py
```

または Blender 経由：

```python
import importlib.util
spec = importlib.util.spec_from_file_location("g",
    r"C:\Users\hoeho\Documents\Claude\BlenderSkill\snippets\generate_gallery.py")
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
mod.generate()
```

実行すると `CHARACTER_ROOT` 配下の構造を走査して、トップ＋全詳細ページの `index.html` を生成する。
