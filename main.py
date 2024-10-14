import cv2
import numpy as np
from ultralytics import YOLO
from collections import deque

class CentroidTracker:
    def __init__(self, maxDisappeared=50):
        self.nextObjectID = 0
        self.objects = {}
        self.disappeared = {}
        self.maxDisappeared = maxDisappeared

    def register(self, centroid):
        self.objects[self.nextObjectID] = centroid
        self.disappeared[self.nextObjectID] = 0
        self.nextObjectID += 1

    def deregister(self, objectID):
        del self.objects[objectID]
        del self.disappeared[objectID]

    def update(self, inputCentroids):
        if len(inputCentroids) == 0:
            for objectID in list(self.disappeared.keys()):
                self.disappeared[objectID] += 1
                if self.disappeared[objectID] > self.maxDisappeared:
                    self.deregister(objectID)
            return self.objects

        if len(self.objects) == 0:
            for i in range(0, len(inputCentroids)):
                self.register(inputCentroids[i])
        else:
            objectIDs = list(self.objects.keys())
            objectCentroids = list(self.objects.values())

            D = self._euclidean_distances(objectCentroids, inputCentroids)

            rows = D.min(axis=1).argsort()
            cols = D.argmin(axis=1)[rows]

            usedRows = set()
            usedCols = set()

            for (row, col) in zip(rows, cols):
                if row in usedRows or col in usedCols:
                    continue

                objectID = objectIDs[row]
                self.objects[objectID] = inputCentroids[col]
                self.disappeared[objectID] = 0

                usedRows.add(row)
                usedCols.add(col)

            unusedRows = set(range(0, D.shape[0])).difference(usedRows)
            unusedCols = set(range(0, D.shape[1])).difference(usedCols)

            if D.shape[0] >= D.shape[1]:
                for row in unusedRows:
                    objectID = objectIDs[row]
                    self.disappeared[objectID] += 1

                    if self.disappeared[objectID] > self.maxDisappeared:
                        self.deregister(objectID)

            else:
                for col in unusedCols:
                    self.register(inputCentroids[col])

        return self.objects

    def _euclidean_distances(self, ptsA, ptsB):
        D = np.linalg.norm(np.array(ptsA)[:, np.newaxis] - np.array(ptsB), axis=2)
        return D

def process_video_yolov8(video_path):
    model = YOLO('yolov8m.pt')
    cap = cv2.VideoCapture(video_path)
    total_cars = 0
    tracker = CentroidTracker(maxDisappeared=50)
    counted_ids = set()
    confidence_threshold = 0.6

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        results = model(frame)
        input_centroids = []

        for result in results:
            for box in result.boxes:
                if int(box.cls[0]) == 2 and box.conf[0] >= confidence_threshold:
                    x1, y1, x2, y2 = map(int, box.xyxy[0])
                    centroid_x = (x1 + x2) // 2
                    centroid_y = (y1 + y2) // 2
                    input_centroids.append((centroid_x, centroid_y))
                    confidence = box.conf[0]
                    cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                    cv2.putText(frame, f"Car {confidence:.2f}", (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)

        objects = tracker.update(input_centroids)

        for (objectID, centroid) in objects.items():
            if objectID not in counted_ids:
                total_cars += 1
                counted_ids.add(objectID)

        cv2.putText(frame, f"Carros detectados: {total_cars}", (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
        cv2.imshow("Detecção e Contagem de Carros - YOLOv8", frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    print(f"Total de carros contados: {total_cars}")
    cap.release()
    cv2.destroyAllWindows()

process_video_yolov8("C:/Users/dante/Downloads/teste4.mp4")