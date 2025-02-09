import numpy as np
import os
import cv2
import pickle
from PIL import Image

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
image_dir = os.path.join(BASE_DIR, "imgs")
caffe_model_dir = os.path.join(BASE_DIR, "caffe_model")

caffeModel = os.path.join(caffe_model_dir, "res10_300x300_ssd_iter_140000.caffemodel")
prototextPath = os.path.join(caffe_model_dir, "deploy.prototxt.txt")

net = cv2.dnn.readNetFromCaffe(prototextPath, caffeModel)

curr_id = 0
labelToId = {}
train_x = []
train_y = []

recognizer = cv2.face.LBPHFaceRecognizer_create()

for root, dirs, files in os.walk(image_dir):
    for file in files:
        if file.endswith("png") or file.endswith("jpg") or file.endswith("jpeg"):
            path = os.path.join(root, file)
            label = os.path.basename(root).lower()
            if labelToId.get(label) is None:
                labelToId[label] = curr_id
                curr_id += 1
            image = cv2.imread(path)
            h, w = image.shape[:2]
            blob = cv2.dnn.blobFromImage(cv2.resize(image, (300, 300)), 1.0, (300, 300), (104.0, 177.0, 123.0))
            net.setInput(blob)
            detections = net.forward()
            confidence = detections[0, 0, 0, 2]
            if confidence >= 0.5:
                box = detections[0, 0, 0, 3:7] * np.array([w, h, w, h])
                startX, startY, endX, endY = box.astype("int")
                pil_image = Image.open(path).convert("L")
                image_array = np.array(pil_image, "uint8")
                roi = image_array[startY:endY, startX:endX]
                roi = cv2.resize(roi, (64, 64))
                train_x.append(roi)
                train_y.append(labelToId[label])

with open(os.path.join(BASE_DIR, "labels.pickle"), "wb") as f:
    pickle.dump(labelToId, f)

recognizer.train(train_x, np.array(train_y))
recognizer.save(os.path.join(BASE_DIR, "model.yml"))
