"""生成 app 图标 resources/icon.ico（仅构建期使用，可删除）。"""
from PIL import Image, ImageDraw, ImageFont

SIZE = 256


def _font(size: int):
    candidates = ["segoeuib.ttf", "arialbd.ttf", "arial.ttf", "consola.ttf"]
    for name in candidates:
        try:
            return ImageFont.truetype(name, size)
        except Exception:  # noqa: BLE001
            continue
    return ImageFont.load_default()


def main() -> None:
    img = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([8, 8, SIZE - 8, SIZE - 8], radius=48, fill=(31, 111, 235, 255))
    font = _font(150)
    d.text((SIZE / 2, SIZE / 2 - 6), "U", font=font, fill=(255, 255, 255, 255), anchor="mm")
    img.save(
        "resources/icon.ico",
        sizes=[(256, 256), (128, 128), (64, 64), (48, 48), (32, 32), (16, 16)],
    )
    print("icon written -> resources/icon.ico")


if __name__ == "__main__":
    main()
