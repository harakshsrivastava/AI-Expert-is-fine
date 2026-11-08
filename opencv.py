import cv2
import numpy as np
from pathlib import Path
image_path = Path(__file__).resolve().parent / "image.png"
try:
    image = cv2.imdecode(
        np.fromfile(str(image_path), dtype=np.uint8),
        cv2.IMREAD_COLOR
    )
except (OSError, ValueError) as e:
    print(f"Error loading image: {e}")
    raise SystemExit(1)
if image is None:
    print("Error: Could not decode image.png")
    raise SystemExit(1)
height, width = image.shape[:2]
print("=" * 45)
print("          OPENCV IMAGE RESIZER")
print("=" * 45)
print(f"Original image: {width} x {height} pixels\n")
sizes = {
    "small": (200, 200),
    "medium": (400, 400),
    "large": (600, 600)
}
for name, dimensions in sizes.items():
    print(f"Processing {name} image...")
    interpolation = (
        cv2.INTER_AREA
        if dimensions[0] < width or dimensions[1] < height
        else cv2.INTER_LINEAR
    )
    resized = cv2.resize(
        image,
        dimensions,
        interpolation=interpolation
    )
    output_path = image_path.parent / f"image_{name}.png"
    success, encoded = cv2.imencode(".png", resized)
    if success:
        encoded.tofile(str(output_path))
        print(f"Saved: {output_path.name}")
        print(f"Resolution: {dimensions[0]} x {dimensions[1]}")
    else:
        print(f"Error saving {output_path.name}")
    cv2.imshow(
        f"{name.title()} - {dimensions[0]}x{dimensions[1]}",
        resized
    )
    print("-" * 45)
print("\nAll resizing operations completed!")
print("Press any key inside an image window to exit.")
cv2.waitKey(0)
cv2.destroyAllWindows()
print("Program closed successfully.")