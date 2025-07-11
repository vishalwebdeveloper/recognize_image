from django.shortcuts import render
from .form import ImageUploadForm
from .models import ImageModel
from PIL import Image
from io import BytesIO
from django.core.files.base import ContentFile
import imagehash
import numpy as np
from ultralytics import YOLO
import cv2,os,gc,torch
from django.conf import settings

torch.set_num_threads(1)  # ✅ Limit CPU usage

# ✅ Environment tweaks to suppress caching/logging
os.environ["YOLO_LOGGING"] = "false"
os.environ["YOLO_CACHE"] = "false"
# model = YOLO('yolov8n.pt')  # Or 'yolov5s.pt' if you're using YOLOv5 model file

# ✅ Lazy loading YOLOv8n model
def get_yolo_model():
    if not hasattr(settings, 'YOLO_MODEL'):
        settings.YOLO_MODEL = YOLO('yolov8n.pt')
    return settings.YOLO_MODEL

# Dummy object detection (simulate real ML)
def detect_objects(pil_image):
    # ✅ Resize to 320x320 before detection
    image = pil_image.resize((224, 224)) 
    image_np = np.array(image)
    image_cv = cv2.cvtColor(image_np, cv2.COLOR_RGB2BGR)
    model = get_yolo_model()  # Get the YOLO model instance

    # ✅ Use .predict(), not direct call; disable fuse and force CPU
    results = model.predict(image_cv, device='cpu', fuse=False, verbose=False)[0]
    detected_labels = [model.names[int(cls)] for cls in results.boxes.cls]
    # ✅ Cleanup
    del image_np, image_cv, results
    gc.collect()

    return list(set(detected_labels))

def calculate_image_hash(image):
    return imagehash.average_hash(image)

def compare_color_histogram(hist1, hist2):
    if len(hist1) != len(hist2):
        return 0
    score = sum(1 - (abs(a - b) / max(a + b, 1)) for a, b in zip(hist1, hist2)) / len(hist1)
    return round(score * 100, 2)

def object_match_score(objs1, objs2):
    common = set(objs1) & set(objs2)
    total = set(objs1) | set(objs2)
    if not total:
        return 100
    return round((len(common) / len(total)) * 100, 2)

def upload_image(request):
    if request.method == 'POST':
        form = ImageUploadForm(request.POST, request.FILES)
        if form.is_valid():
            uploaded_file = request.FILES['image']
            uploaded_image = Image.open(uploaded_file).convert('RGB')
            uploaded_image = uploaded_image.resize((320, 320))  # ✅ Resize for speed
            uploaded_hash = calculate_image_hash(uploaded_image)
            uploaded_hist = uploaded_image.resize((32, 32)).convert('P').histogram()
            uploaded_objects = detect_objects(uploaded_image)

            existing_images = ImageModel.objects.all()

            if not existing_images.exists():
                # First image — directly save
                buffer = BytesIO()
                # uploaded_image.save(buffer, format='JPEG')
                uploaded_image.save(buffer, format='JPEG', quality=80, optimize=True)  # ✅ Compressed save
                image_file = ContentFile(buffer.getvalue(), name=uploaded_file.name)

                ImageModel.objects.create(
                    image=image_file,
                    hash=str(uploaded_hash),
                    color_histogram=uploaded_hist,
                    object_list=uploaded_objects
                )

                return render(request, 'upload.html', {
                    'form': ImageUploadForm(),
                    'hash_match': 100,
                    'object_match': 100,
                    'color_match': 100,
                    'final_avg': 100,
                    'detected_objects': uploaded_objects,
                })

            # Match against existing images
            best_match = {
                'average': 0,
                'hash': 0,
                'color': 0,
                'object': 0
            }

            for existing in existing_images:
                try:
                    existing_image = Image.open(existing.image).convert('RGB')
                    existing_hash = imagehash.hex_to_hash(existing.hash)
                    existing_hist = existing.color_histogram
                    existing_objs = existing.object_list
                except Exception:
                    continue

                hash_diff = uploaded_hash - existing_hash
                hash_match = max(0, 100 - (hash_diff / 100) * 100)

                color_match = compare_color_histogram(uploaded_hist, existing_hist)
                object_match = object_match_score(uploaded_objects, existing_objs)

                final_avg = round((hash_match + color_match + object_match) / 3)

                if final_avg > best_match['average']:
                    best_match = {
                        'average': final_avg,
                        'hash': round(hash_match),
                        'color': round(color_match),
                        'object': round(object_match)
                    }

            # Save if match ≥ 70
            if best_match['average'] >= 70:
                buffer = BytesIO()
                uploaded_image.save(buffer, format='JPEG')
                image_file = ContentFile(buffer.getvalue(), name=uploaded_file.name)

                ImageModel.objects.create(
                    image=image_file,
                    hash=str(uploaded_hash),
                    color_histogram=uploaded_hist,
                    object_list=uploaded_objects
                )

            return render(request, 'upload.html', {
                'form': ImageUploadForm(),
                'hash_match': best_match['hash'],
                'object_match': best_match['object'],
                'color_match': best_match['color'],
                'final_avg': best_match['average'],
                'detected_objects': uploaded_objects,
            })

    return render(request, 'upload.html', {'form': ImageUploadForm(), 'final_avg': None})
