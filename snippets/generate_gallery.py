"""generate_gallery.py
----------------------
階層型ギャラリー生成。

- index.html : トップページ。ポーズ＆表情を 1枚サムネで一覧 → 詳細ページへリンク
- <section>/<category>/<name>/index.html : 詳細ページ。全角度×全パスを表示

ポーズは 5アングル × 4パス = 20画像、表情は 4パス を詳細ページで見せる。
"""

import os
import html


CHARACTER_ROOT = r"C:\Users\hoeho\Documents\Claude\BlenderSkill\blender\outputs\character\base_motoko"
PASS_NAMES = ["beauty", "depth", "normal", "openpose"]


def find_image(folder, basename):
    for ext in (".png", ".jpg", ".jpeg"):
        full = os.path.join(folder, basename + ext)
        if os.path.exists(full):
            return basename + ext
    return None


def scan_section(section_root, has_angles=False):
    """セクション配下を走査して item リストを返す。

    has_angles=True (poses):  category/name/angle/<pass>.png 形式
    has_angles=False (expressions): category/name/<pass>.png 形式

    Returns: [(category, name, rel_dir_of_item, variants), ...]
      variants: dict {variant_name: {pass_name: rel_image_path_from_section}, ...}
                ポーズなら variant_name = angle名、表情なら ""
    """
    items = {}  # (category, name) -> variants
    if not os.path.isdir(section_root):
        return []
    for dirpath, dirnames, filenames in os.walk(section_root):
        # _test系をスキップ
        rel = os.path.relpath(dirpath, section_root)
        if rel == ".":
            continue
        if any(p.startswith("_") for p in rel.split(os.sep)):
            continue
        passes = {}
        for p in PASS_NAMES:
            f = find_image(dirpath, p)
            if f:
                passes[p] = f
        if not passes:
            continue
        parts = rel.split(os.sep)
        if has_angles:
            # 3レベル必要: category[/...]/name/angle
            if len(parts) < 3:
                continue
            category = "/".join(parts[:-2])
            name = parts[-2]
            variant = parts[-1]
            item_rel = "/".join(parts[:-1])
        else:
            # 2レベル: category/name
            if len(parts) == 1:
                category = ""
                name = parts[0]
                item_rel = parts[0]
            else:
                category = "/".join(parts[:-1])
                name = parts[-1]
                item_rel = "/".join(parts)
            variant = ""
        key = (category, name, item_rel)
        if key not in items:
            items[key] = {}
        # rel path from section root to image
        for p, f in passes.items():
            items[key].setdefault(variant, {})[p] = f"{rel}/{f}".replace(os.sep, "/")
    result = []
    for (category, name, item_rel), variants in sorted(items.items()):
        result.append((category, name, item_rel, variants))
    return result


CSS_COMMON = """
body { font-family: -apple-system, "Segoe UI", "Hiragino Sans", "Yu Gothic", sans-serif;
       background:#1a1a1a; color:#eaeaea; padding:24px; margin:0; }
h1 { color:#fff; margin:0 0 8px; }
h1 small { color:#888; font-weight:normal; font-size:14px; }
h2 { color:#fff; margin:32px 0 12px; border-bottom:1px solid #333; padding-bottom:6px; }
h2 .count { color:#888; font-weight:normal; font-size:14px; }
h3.cat { color:#aaa; font-size:13px; font-weight:500; margin:18px 0 8px;
         text-transform:uppercase; letter-spacing:0.5px; }
a { color:#7ab; text-decoration:none; }
a:hover { text-decoration:underline; }
.back { display:inline-block; margin-bottom:16px; padding:6px 12px; background:#333;
        border-radius:4px; color:#eaeaea; font-size:13px; }
.back:hover { background:#444; text-decoration:none; }
"""

CSS_TOP = CSS_COMMON + """
.grid { display:grid; grid-template-columns: repeat(auto-fill, minmax(180px, 1fr)); gap:12px; }
.card { background:#262626; padding:8px; border-radius:6px; box-shadow:0 1px 2px rgba(0,0,0,0.5);
        display:block; }
.card:hover { background:#303030; text-decoration:none; }
.card img { width:100%; display:block; background:#000; border-radius:4px; }
.card .name { color:#fff; font-size:13px; margin-top:6px; text-align:center;
              white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }
"""

CSS_DETAIL = CSS_COMMON + """
.angle-block { margin-bottom:32px; }
.angle-block h3 { color:#fff; margin:0 0 8px; font-size:16px; }
.pass-grid { display:grid; grid-template-columns: repeat(auto-fill, 220px);
             gap:12px; }
figure.pass { margin:0; }
figure.pass a img { width:100% !important; height:auto !important; display:block;
                    background:#000; border-radius:4px; cursor:zoom-in; }
figure.pass figcaption { font-size:11px; text-align:center; color:#aaa; margin-top:4px; }

/* ライトボックス: クリックで viewport にフィット */
.lightbox { position:fixed !important; top:0 !important; left:0 !important;
            width:100vw !important; height:100vh !important;
            background:rgba(0,0,0,0.92) !important;
            display:flex !important; align-items:center !important; justify-content:center !important;
            z-index:9999 !important; cursor:zoom-out !important; margin:0 !important; padding:0 !important; }
.lightbox img { width:85vmin !important; height:85vmin !important;
                max-width:90vw !important; max-height:90vh !important;
                object-fit:contain !important;
                box-shadow:0 0 30px rgba(0,0,0,0.8) !important;
                display:block !important; }
html.lb-open, body.lb-open { overflow:hidden !important; }
"""

JS_LIGHTBOX = """
(function(){
  function closeLb(){
    var ov = document.querySelector('.lightbox');
    if (ov) { ov.remove(); document.body.classList.remove('lb-open'); document.documentElement.classList.remove('lb-open'); }
  }
  document.addEventListener('click', function(e) {
    var link = e.target.closest('.pass a');
    if (!link) return;
    e.preventDefault();
    e.stopPropagation();
    closeLb();
    var ov = document.createElement('div');
    ov.className = 'lightbox';
    var img = document.createElement('img');
    img.src = link.getAttribute('href');
    ov.appendChild(img);
    ov.addEventListener('click', closeLb);
    document.body.appendChild(ov);
    document.body.classList.add('lb-open');
    document.documentElement.classList.add('lb-open');
  }, true);
  document.addEventListener('keydown', function(e) {
    if (e.key === 'Escape') closeLb();
  });
})();
"""


def write_top_index(poses_items, expressions_items, out_path):
    """トップページ: 1枚サムネ × アイテム数 のグリッド。"""
    parts = []
    parts.append('<!DOCTYPE html><html><head><meta charset="utf-8">')
    parts.append('<title>base_motoko renders</title>')
    parts.append(f'<style>{CSS_TOP}</style></head><body>')
    parts.append('<h1>base_motoko Renders <small>— click any thumbnail for full angles/passes</small></h1>')

    def render_items(title, items, section_path):
        if not items:
            return ""
        # カテゴリ別グループ化
        by_cat = {}
        for category, name, item_rel, variants in items:
            by_cat.setdefault(category, []).append((name, item_rel, variants))
        out = [f'<h2>{html.escape(title)} <span class="count">({len(items)})</span></h2>']
        for category in sorted(by_cat.keys()):
            entries = by_cat[category]
            cat_label = category if category else "(uncategorized)"
            out.append(f'<h3 class="cat">{html.escape(cat_label)} ({len(entries)})</h3>')
            cards = []
            for name, item_rel, variants in entries:
                # 代表サムネ: front があれば front の beauty、なければ最初の variant の beauty
                preferred_variant = 'front' if 'front' in variants else (
                    '' if '' in variants else next(iter(variants.keys()), None))
                thumb = None
                if preferred_variant is not None:
                    thumb = variants[preferred_variant].get('beauty')
                if not thumb:
                    continue
                thumb_url = f"{section_path}/{thumb}"
                detail_url = f"{section_path}/{item_rel}/index.html"
                cards.append(
                    f'<a class="card" href="{html.escape(detail_url)}">'
                    f'<img src="{html.escape(thumb_url)}" loading="lazy">'
                    f'<div class="name">{html.escape(name)}</div></a>'
                )
            out.append(f'<div class="grid">{"".join(cards)}</div>')
        return "".join(out)

    parts.append(render_items("Poses", poses_items, "poses"))
    parts.append(render_items("Expressions", expressions_items, "expressions"))
    parts.append('</body></html>')

    with open(out_path, 'w', encoding='utf-8') as f:
        f.write("".join(parts))


def write_detail_page(item_root_dir, title, category, variants, back_url):
    """詳細ページ: 各 variant ごとに 4パスをグリッド表示。"""
    parts = []
    parts.append('<!DOCTYPE html><html><head><meta charset="utf-8">')
    parts.append(f'<title>{html.escape(title)}</title>')
    parts.append(f'<style>{CSS_DETAIL}</style></head><body>')
    parts.append(f'<a class="back" href="{html.escape(back_url)}">← Back to top</a>')
    cat_label = category if category else "(uncategorized)"
    parts.append(f'<h1>{html.escape(title)} <small>— {html.escape(cat_label)}</small></h1>')

    # variants をソート（front 優先、その他アルファベット）
    angle_priority = {"front": 0, "left_45": 1, "right_45": 2, "left_side": 3, "right_side": 4, "": 99}
    sorted_variants = sorted(variants.items(), key=lambda kv: angle_priority.get(kv[0], 50))

    for variant_name, passes in sorted_variants:
        if variant_name:
            parts.append(f'<div class="angle-block"><h3>{html.escape(variant_name)}</h3>')
        else:
            parts.append('<div class="angle-block">')
        cells = []
        for p in PASS_NAMES:
            rel_path = passes.get(p)
            if rel_path:
                # rel_path は section_root からのパス、しかし詳細ページから見ると
                # variant フォルダから section_root への上り階段を計算する必要あり
                # ただし、ファイル自体は variant ディレクトリにあるので 単に basename.png
                fname = os.path.basename(rel_path)
                cells.append(
                    f'<figure class="pass"><a href="{html.escape(fname)}">'
                    f'<img src="{html.escape(fname)}" loading="lazy"></a>'
                    f'<figcaption>{html.escape(p)}</figcaption></figure>'
                )
            else:
                cells.append('<figure class="pass missing"><div>—</div><figcaption>(none)</figcaption></figure>')
        parts.append(f'<div class="pass-grid">{"".join(cells)}</div></div>')

    parts.append('</body></html>')

    # variant に共通の親フォルダに保存
    # item_root_dir は category/name のフォルダ
    out_path = os.path.join(item_root_dir, "index.html")
    with open(out_path, 'w', encoding='utf-8') as f:
        f.write("".join(parts))


def generate():
    poses_root = os.path.join(CHARACTER_ROOT, "poses")
    exprs_root = os.path.join(CHARACTER_ROOT, "expressions")

    poses_items = scan_section(poses_root, has_angles=True)
    exprs_items = scan_section(exprs_root, has_angles=False)

    # トップページ
    top_path = os.path.join(CHARACTER_ROOT, "index.html")
    write_top_index(poses_items, exprs_items, top_path)

    # 詳細ページ
    for category, name, item_rel, variants in poses_items:
        item_dir = os.path.join(poses_root, *item_rel.split('/'))
        # back URL は item から見てトップへ
        depth = len(item_rel.split('/'))  # category subdirs + name
        back = "../" * depth + "../index.html"
        # variants の画像パス（rel from section_root）→ basename だけ抽出するので OK
        # しかし variants[*][pass] = "category/name/angle/file.png" 形式
        # 詳細ページは category/name/index.html 配置 → 画像は angle/file.png
        # write_detail_page は basename を使ってるので不正確
        # → 修正: variant ごとに rel をきちんと処理
        write_detail_page_for_pose(item_dir, name, category, variants, back)
    for category, name, item_rel, variants in exprs_items:
        item_dir = os.path.join(exprs_root, *item_rel.split('/'))
        depth = len(item_rel.split('/'))
        back = "../" * depth + "../index.html"
        write_detail_page_for_expression(item_dir, name, category, variants, back)

    print(f"Generated: {top_path}")
    print(f"  Poses: {len(poses_items)}")
    print(f"  Expressions: {len(exprs_items)}")


def write_detail_page_for_pose(item_dir, name, category, variants, back_url):
    """poses 用: variants = {angle: {pass: rel_path}}, 詳細ページは category/name/index.html"""
    parts = []
    parts.append('<!DOCTYPE html><html><head><meta charset="utf-8">')
    parts.append(f'<title>{html.escape(name)}</title>')
    parts.append(f'<style>{CSS_DETAIL}</style></head><body>')
    parts.append(f'<a class="back" href="{html.escape(back_url)}">← Back to top</a>')
    cat_label = category if category else "(uncategorized)"
    parts.append(f'<h1>{html.escape(name)} <small>— {html.escape(cat_label)}</small></h1>')

    angle_priority = {"front": 0, "left_45": 1, "right_45": 2, "left_side": 3, "right_side": 4}
    sorted_variants = sorted(variants.items(), key=lambda kv: angle_priority.get(kv[0], 50))

    for angle, passes in sorted_variants:
        parts.append(f'<div class="angle-block"><h3>{html.escape(angle)}</h3>')
        cells = []
        for p in PASS_NAMES:
            rel_path = passes.get(p)
            if rel_path:
                # 詳細ページから見たパス: angle/<pass>.png
                fname = os.path.basename(rel_path)
                local_path = f"{angle}/{fname}"
                cells.append(
                    f'<figure class="pass"><a href="{html.escape(local_path)}">'
                    f'<img src="{html.escape(local_path)}" loading="lazy"></a>'
                    f'<figcaption>{html.escape(p)}</figcaption></figure>'
                )
            else:
                cells.append('<figure class="pass"><div>—</div><figcaption>(none)</figcaption></figure>')
        parts.append(f'<div class="pass-grid">{"".join(cells)}</div></div>')

    parts.append(f'<script>{JS_LIGHTBOX}</script></body></html>')
    out_path = os.path.join(item_dir, "index.html")
    with open(out_path, 'w', encoding='utf-8') as f:
        f.write("".join(parts))


def write_detail_page_for_expression(item_dir, name, category, variants, back_url):
    """expressions 用: variants = {"": {pass: rel_path}}, 詳細ページは category/name/index.html"""
    parts = []
    parts.append('<!DOCTYPE html><html><head><meta charset="utf-8">')
    parts.append(f'<title>{html.escape(name)}</title>')
    parts.append(f'<style>{CSS_DETAIL}</style></head><body>')
    parts.append(f'<a class="back" href="{html.escape(back_url)}">← Back to top</a>')
    cat_label = category if category else "(uncategorized)"
    parts.append(f'<h1>{html.escape(name)} <small>— {html.escape(cat_label)}</small></h1>')

    parts.append('<div class="angle-block">')
    passes = variants.get("", {})
    cells = []
    for p in PASS_NAMES:
        rel_path = passes.get(p)
        if rel_path:
            fname = os.path.basename(rel_path)
            cells.append(
                f'<figure class="pass"><a href="{html.escape(fname)}">'
                f'<img src="{html.escape(fname)}" loading="lazy"></a>'
                f'<figcaption>{html.escape(p)}</figcaption></figure>'
            )
    parts.append(f'<div class="pass-grid">{"".join(cells)}</div></div>')
    parts.append(f'<script>{JS_LIGHTBOX}</script></body></html>')
    out_path = os.path.join(item_dir, "index.html")
    with open(out_path, 'w', encoding='utf-8') as f:
        f.write("".join(parts))


if __name__ == "__main__":
    generate()
