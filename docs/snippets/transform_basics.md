# transform_basics.py

オブジェクトの位置・回転・スケールをコードで設定する基本パターン。

## コード

```python
--8<-- "snippets/transform_basics.py"
```

## ポイント

- `obj.rotation_euler` の単位は **ラジアン**。度数で書くなら `math.radians(45)` で変換する。
- 直接タプル代入でも動くが、**`Vector` / `Euler` を使うと意図が読み取りやすい**（特に他の場所で同じ値を使い回す時）。
- 後で度数に戻したいときは `math.degrees(rad)`。

## よくあるパターン

| やりたいこと | 書き方 |
|---|---|
| Z軸まわりに 90° 回転 | `obj.rotation_euler = (0, 0, math.radians(90))` |
| 等倍で2倍に拡大 | `obj.scale = (2, 2, 2)` |
| 真上に 5 持ち上げる | `obj.location.z += 5` |
| 現在値からの相対 | `obj.location += Vector((1, 0, 0))` |
