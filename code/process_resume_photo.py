from pathlib import Path

from PIL import Image, ImageEnhance, ImageFilter, ImageOps


PROJECT_DIR = Path(__file__).resolve().parents[1]
RESUME_DIR = PROJECT_DIR / "简历"
INPUT_FILE = RESUME_DIR / "证件照原图.jpg"
OUTPUT_FILE = RESUME_DIR / "证件照_简历版.jpg"


def main():
    if not INPUT_FILE.exists():
        raise FileNotFoundError(
            "请先将照片保存为："
            f"{INPUT_FILE}"
        )

    image = Image.open(INPUT_FILE).convert("RGB")
    width, height = image.size

    # 先去掉照片四周可能存在的白色拍摄边框。
    left = int(width * 0.04)
    right = int(width * 0.96)
    top = int(height * 0.02)
    bottom = int(height * 0.98)
    image = image.crop((left, top, right, bottom))

    # 35mm x 45mm 常用证件照比例，输出适合放入简历的清晰尺寸。
    image = ImageOps.fit(
        image,
        (826, 1062),
        method=Image.Resampling.LANCZOS,
        centering=(0.5, 0.46),
    )

    # 轻微增强，不进行夸张美颜或改变面部特征。
    image = ImageEnhance.Contrast(image).enhance(1.04)
    image = ImageEnhance.Brightness(image).enhance(1.03)
    image = image.filter(ImageFilter.UnsharpMask(radius=1.0, percent=45, threshold=3))

    image.save(
        OUTPUT_FILE,
        format="JPEG",
        quality=95,
        dpi=(300, 300),
    )
    print(f"Saved: {OUTPUT_FILE}")
    print(f"Size: {image.size[0]} x {image.size[1]} pixels")


if __name__ == "__main__":
    main()
