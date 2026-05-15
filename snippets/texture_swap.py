"""texture_swap.py
-------------------
キャラのテクスチャ画像を別ファイルに差し替える小ユーティリティ。
2通りの使い方:

(A) **同じファイル名で上書き編集**しただけ → 単に reload で反映
    reload_all() を呼べば textures/ 配下を全部読み直す。

(B) **新規ファイル名で別バリエーション**を作った → swap で参照先を切替
    swap("body_skin", "body_skin_with_clothes.png")
    swap_path("_10.003", r"C:\\full\\path\\to\\file.png")

切替後はそのまま render_all_poses() を走らせれば新テクスチャで再レンダーされる。
"""

import bpy
import os

# テクスチャフォルダのデフォルト
TEXTURE_DIR = r"C:\Users\hoeho\Documents\Claude\BlenderSkill\blender\assets\vroid\base_motoko\textures"


def _find_images_by_label(label):
    """label に一致するimageを返す。

    マッチ条件（広めに取る）:
      1. image.name 完全一致
      2. filepath basename without ext が完全一致
      3. filepath basename without ext が `<label>` または `<label>_` で始まる
         （例: "body_skin" でも "body_skin_with_clothes" にヒット）
    """
    results = []
    for img in bpy.data.images:
        if img.name == label:
            results.append(img)
            continue
        if not img.filepath:
            continue
        base = os.path.basename(img.filepath).rsplit('.', 1)[0]
        if base == label or base.startswith(label + "_"):
            results.append(img)
    return results


def swap(label, new_filename, texture_dir=TEXTURE_DIR):
    """テクスチャ参照先を `<texture_dir>/<new_filename>` に切替。

    label は以下のいずれかで指定可能:
      - image data block の name（例: "_10.003"）
      - filepath の basename without ext（例: "body_skin"）

    `new_filename` には拡張子を含めるか省略可能（.pngを補完）。
    """
    if not new_filename.endswith(('.png', '.jpg', '.tga')):
        new_filename += '.png'
    new_path = os.path.join(texture_dir, new_filename)
    if not os.path.exists(new_path):
        raise FileNotFoundError(f"Texture not found: {new_path}")

    imgs = _find_images_by_label(label)
    if not imgs:
        raise ValueError(f"No image data block matches label: {label}")

    for img in imgs:
        old = img.filepath
        img.filepath = new_path
        img.filepath_raw = new_path
        img.reload()
        print(f"  [swap] '{img.name}': {os.path.basename(old)} -> {new_filename}")
    return imgs


def swap_path(label, full_path):
    """`new_filename` 経由の補完を避けて、フルパス指定で切替したいとき用。"""
    if not os.path.exists(full_path):
        raise FileNotFoundError(f"Texture not found: {full_path}")
    imgs = _find_images_by_label(label)
    for img in imgs:
        old = img.filepath
        img.filepath = full_path
        img.filepath_raw = full_path
        img.reload()
        print(f"  [swap_path] '{img.name}': {os.path.basename(old)} -> {os.path.basename(full_path)}")
    return imgs


def reload_all(texture_dir=TEXTURE_DIR):
    """textures/ 配下を参照している全 image を reload（同名で上書き保存した時用）。"""
    n = 0
    for img in bpy.data.images:
        if img.filepath and texture_dir.lower() in img.filepath.lower():
            img.reload()
            n += 1
    print(f"[reload_all] reloaded {n} textures from {texture_dir}")
    return n


def list_textures():
    """現在シーンが参照している textures/ 配下のファイルを列挙。"""
    refs = {}
    for img in bpy.data.images:
        if img.filepath and TEXTURE_DIR.lower() in img.filepath.lower():
            refs.setdefault(os.path.basename(img.filepath), []).append(img.name)
    print(f"=== Active texture references ({len(refs)}) ===")
    for fname, names in sorted(refs.items()):
        print(f"  {fname}  <- {names}")


if __name__ == "__main__":
    list_textures()
