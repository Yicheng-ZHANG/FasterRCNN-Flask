from flask import Flask, request, send_from_directory, jsonify
import os
from PIL import Image
import cv2
import numpy as np
import json

img_dir = "faster-rcnn.pytorch/images/"
pred_dir = "faster-rcnn.pytorch/predicts/"
json_dir = "faster-rcnn.pytorch/json_files/"
THRESHOLD = 0.5
 

app = Flask(__name__)

app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024

@app.route("/", methods=['POST'])
def predict():

    for i in os.listdir(img_dir):
        file_path = os.path.join(img_dir, i)
        os.remove(file_path)

    for i in os.listdir(pred_dir):
        file_path = os.path.join(pred_dir, i)
        os.remove(file_path)

    img = request.files.get("file")
    imgName = img.filename
    img.save(os.path.join(img_dir, imgName))
    os.system("cd faster-rcnn.pytorch && python demo.py --net res101 --dataset Emotion --checksession 1 --checkepoch 10 --checkpoint 1915 --load_dir models")
    os.system("cd faster-rcnn.pytorch && python demo.py --net res101 --dataset Age --checksession 1 --checkepoch 10 --checkpoint 1915 --load_dir models")
    os.system("cd faster-rcnn.pytorch && python demo.py --net res101 --dataset Gender --checksession 1 --checkepoch 10 --checkpoint 1915 --load_dir models")
    os.system("cd faster-rcnn.pytorch && python demo.py --net res101 --dataset Race --checksession 1 --checkepoch 10 --checkpoint 1915 --load_dir models")
    obj_list = []
    
    with open(os.path.join(pred_dir, imgName[:imgName.find(".")] + "_Gender.txt"), 'r') as f:
        for line in f:
            line = line.strip().split(" ")
            x1, y1, x2, y2 = float(line[0]), float(line[1]), float(line[2]), float(line[3])
            score = float(line[4])
            cls = line[5]
            overlap = False
            if score < THRESHOLD:
                continue
            for obj in obj_list:
                if abs(obj["x1"] - x1) < 10 and abs(obj["y1"] - y1) < 10 and abs(obj["x2"] - x2) < 10 and abs(obj["y2"] - y2) < 10:
                    if "gender_score" not in obj or obj["gender_score"] < score:
                        overlap = True
                    if obj["gender_score"] < score:
                        obj["x1"], obj["y1"], obj["x2"], obj["y2"] = x1, y1, x2, y2
                        obj["gender_score"] = score
                        obj["gender"] = cls
            if not overlap:
                new_obj = {}
                new_obj["object"] = len(obj_list) + 1
                new_obj["x1"], new_obj["y1"], new_obj["x2"], new_obj["y2"] = x1, y1, x2, y2
                new_obj["gender_score"] = score
                new_obj["gender_class_label"] = cls
                obj_list.append(new_obj)
    
    with open(os.path.join(pred_dir, imgName[:imgName.find(".")] + "_Age.txt"), 'r') as f:
        for line in f:
            line = line.strip().split(" ")
            x1, y1, x2, y2 = float(line[0]), float(line[1]), float(line[2]), float(line[3])
            score = float(line[4])
            cls = line[5]
            for obj in obj_list:
                if abs(obj["x1"] - x1) < 10 and abs(obj["y1"] - y1) < 10 and abs(obj["x2"] - x2) < 10 and abs(obj["y2"] - y2) < 10:
                    if "age_score" not in obj or obj["age_score"] < score:
                        obj["age_score"] = score
                        obj["age_class_label"] = cls

    with open(os.path.join(pred_dir, imgName[:imgName.find(".")] + "_Emotion.txt"), 'r') as f:
        for line in f:
            line = line.strip().split(" ")
            x1, y1, x2, y2 = float(line[0]), float(line[1]), float(line[2]), float(line[3])
            score = float(line[4])
            cls = line[5]
            overlap = False
            for obj in obj_list:
                if abs(obj["x1"] - x1) < 10 and abs(obj["y1"] - y1) < 10 and abs(obj["x2"] - x2) < 10 and abs(obj["y2"] - y2) < 10:
                    if "emo_score" not in obj or obj["emo_score"] < score:
                        obj["emo_score"] = score
                        obj["emo_class_label"] = cls

    with open(os.path.join(pred_dir, imgName[:imgName.find(".")] + "_Race.txt"), 'r') as f:
        for line in f:
            line = line.strip().split(" ")
            x1, y1, x2, y2 = float(line[0]), float(line[1]), float(line[2]), float(line[3])
            score = float(line[4])
            cls = line[5]
            for obj in obj_list:
                if abs(obj["x1"] - x1) < 10 and abs(obj["y1"] - y1) < 10 and abs(obj["x2"] - x2) < 10 and abs(obj["y2"] - y2) < 10:
                    if "ethnicity_score" not in obj or obj["ethnicity_score"] < score:
                        obj["ethnicity_score"] = score
                        obj["ethnicity_class_label"] = cls

    resultName = imgName[:imgName.find(".")] + "_det.jpg"
    im = Image.open(os.path.join(img_dir, imgName))
    RGB_img = drawBoundingBoxes(np.array(im), obj_list)
    # RGB_img = cv2.cvtColor(img_draw, cv2.COLOR_BGR2RGB)
    RGB_img = Image.fromarray(RGB_img)
    RGB_img.save(os.path.join(img_dir, resultName))

    
    with open(os.path.join(json_dir, imgName[:imgName.find(".")] + ".json"), 'w', encoding="utf-8") as f:
        # obj_json = json.dumps(obj_list)
        json.dump(obj_list, f)
        

    return send_from_directory(img_dir, os.path.join(img_dir, resultName), resultName)

@app.route("/detections", methods=['POST'])
def return_json():
    json_name = request.data.decode("utf-8")
    with open(os.path.join(json_dir, json_name + ".json"), 'r', encoding="utf-8") as f:
        obj_list = json.load(f)

    for i in os.listdir(json_dir):
        file_path = os.path.join(json_dir, i)
        os.remove(file_path)

    return jsonify({"response": obj_list})
    # return jsonify({"objects":[{"name": "Person_1", "Age": "0-3", "Gender": "Male", "Race": "Asian", "Emotion": "Anger"}, 
    # {"name": "Person_2", "Age": "20-39", "Gender": "Female", "Emotion": "Happiness"}]})
    # return jsonify({"objects": []})


def drawBoundingBoxes(imageData, inferenceResults): 
    """Draw bounding boxes on an image.
    imageData: image data in numpy array format
    imageOutputPath: output image file path
    inferenceResults: inference results array off object (l,t,w,h)
    colorMap: Bounding box color candidates, list of RGB tuples.
    """
    for res in inferenceResults:
        x1 = int(res['x1'])
        y1 = int(res['y1'])
        x2 = int(res['x2']) 
        y2 = int(res['y2']) 
        label = "Person_" + str(res['object'])
        color = (255, 199, 50)
        imgHeight, imgWidth, _ = imageData.shape
        thick = int((imgHeight + imgWidth) // 300)
        cv2.rectangle(imageData,(x1, y1), (x2, y2), color, thick)
        cv2.putText(imageData, label, (x1, y1 - 5), 2, 1e-3 * (imgHeight + imgWidth), color, thick//2)
    return imageData

    
if __name__ == '__main__':
    app.debug = False
    app.run(host='0.0.0.0', port=5000)
