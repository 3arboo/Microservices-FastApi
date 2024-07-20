import shutil
import io
from fastapi.testclient import TestClient
from app.main import app, BASE_DIR, UPLOAD_DIR, get_settings
from PIL import Image, ImageChops

client = TestClient(app)

def test_prediction_upload_missing_headers():
    img_saved_path = BASE_DIR / "images"
    for path in img_saved_path.glob("*"):
        with open(path, 'rb') as img_file:
            response = client.post("/",
                files={"file": img_file}
            )
            assert response.status_code == 401


def test_prediction_upload():
    img_saved_path = BASE_DIR / "images"
    settings = get_settings()
    for path in img_saved_path.glob("*"):
        with open(path, 'rb') as img_file:
            response = client.post("/",
                files={"file": img_file},
                headers={"Authorization": f"Bearer {settings.app_auth_token}"}
            )
            try:
                img = Image.open(path)
                assert response.status_code == 200
                data = response.json()
                assert "results" in data
                assert "original" in data
            except:
                assert response.status_code == 400


def test_echo_upload():
    img_saved_path = BASE_DIR / "images"
    settings = get_settings()
    for path in img_saved_path.glob("*"):
        with open(path, 'rb') as img_file:
            response = client.post("/img-echo/",
                files={"file": img_file},
                headers={"Authorization": f"Bearer {settings.app_auth_token}"}
            )
            try:
                img = Image.open(path)
                assert response.status_code == 200
                r_stream = io.BytesIO(response.content)
                echo_img = Image.open(r_stream)
                difference = ImageChops.difference(echo_img, img).getbbox()
                assert difference is None
            except:
                assert response.status_code == 400

    shutil.rmtree(UPLOAD_DIR)
