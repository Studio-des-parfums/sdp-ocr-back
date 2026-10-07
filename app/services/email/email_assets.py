import os

STATIC_IMAGES_PATH = os.path.join(os.path.dirname(__file__), "../../static/images")
PYRAMID_IMAGE_PATH = os.path.join(STATIC_IMAGES_PATH, "pyramide.png")
LOGO_IMAGE_PATH = os.path.join(STATIC_IMAGES_PATH, "logoSDP.png")


def _read_image_bytes(path):
    try:
        if os.path.exists(path):
            with open(path, "rb") as img_file:
                return img_file.read()
    except Exception as e:
        print(f"Erreur lecture image {path}: {e}")
    return None


def get_pyramid_image_bytes():
    return _read_image_bytes(PYRAMID_IMAGE_PATH)


def get_logo_image_bytes():
    return _read_image_bytes(LOGO_IMAGE_PATH)
