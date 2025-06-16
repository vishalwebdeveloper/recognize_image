from django.shortcuts import render
from .form import ImageUploadForm
from .models import ImageModel
from PIL import Image
from io import BytesIO
from django.core.files.base import ContentFile
import imagehash
import numpy as np
import random
from ultralytics import YOLO
import cv2


model = YOLO('yolov8n.pt')  # Or 'yolov5s.pt' if you're using YOLOv5 model file
# Dummy object detection (simulate real ML)
def detect_objects(image):
    # Convert PIL image to OpenCV format
    image_np = np.array(image)
    image_cv = cv2.cvtColor(image_np, cv2.COLOR_RGB2BGR)

    results = model(image_cv)[0]  # detect once
    detected_labels = [model.names[int(cls)] for cls in results.boxes.cls]

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
            uploaded_hash = calculate_image_hash(uploaded_image)
            uploaded_hist = uploaded_image.histogram()
            uploaded_objects = detect_objects(uploaded_image)

            existing_images = ImageModel.objects.all()

            if not existing_images.exists():
                # First image — directly save
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
