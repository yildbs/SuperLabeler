import numpy as np
import cv2
from PyQt5.QtCore import QDir, Qt, QTimer, QObject, QEvent
import sys
from copy import deepcopy
import math


class ObjectExtractor:
    def __init__(self):
        pass

    def initialize(self, image):
        self.image = image
        self.mask = np.zeros(self.image.shape[:2], np.uint8)
        # self.mask.fill(cv2.GC_PR_BGD)
        self.mask.fill(cv2.GC_PR_FGD)
        self.bgd_model = np.zeros((1, 65), np.float64)
        self.fgd_model = np.zeros((1, 65), np.float64)

        self.radius_brush = 10

        self.x1 = sys.maxsize
        self.y1 = sys.maxsize
        self.x2 = 0
        self.y2 = 0

    def reset_mask(self):
        self.mask = np.zeros(self.image.shape[:2], np.uint8)
        # self.mask.fill(cv2.GC_PR_BGD)
        self.mask.fill(cv2.GC_PR_FGD)

        self.x1 = sys.maxsize
        self.y1 = sys.maxsize
        self.x2 = 0
        self.y2 = 0

    def draw_mask(self, x, y):
        x1 = x - self.radius_brush
        y1 = y - self.radius_brush
        x2 = x + self.radius_brush
        y2 = y + self.radius_brush
        # self.mask[y1:y2, x1:x2] = 3
        # self.mask[y1:y2, x1:x2] = cv2.GC_FGD
        self.mask[y1:y2, x1:x2] = cv2.GC_BGD

        self.x1 = min(self.x1, x1)
        self.y1 = min(self.y1, y1)
        self.x2 = max(self.x2, x2)
        self.y2 = max(self.y2, y2)

    def analyze(self):
        x1 = self.x1
        y1 = self.y1
        x2 = self.x2
        y2 = self.y2

        if (x2-x1) < 100 or (y2-y1) < 100:
            return None

        if (x2-x1) > 600 or (y2-y1) > 600:
            return None

        target = self.image[y1:y2, x1:x2, :]
        mask = self.mask[y1:y2, x1:x2]

        bgd_model = np.zeros((1, 65), np.float64)
        fgd_model = np.zeros((1, 65), np.float64)

        mask, bgd_model, fgd_model = cv2.grabCut(target, mask, None, bgd_model, fgd_model, 5, cv2.GC_INIT_WITH_MASK)
        mask2 = np.where((mask == cv2.GC_BGD) | (mask == cv2.GC_PR_BGD), 0, 1).astype('uint8')

        mask3 = deepcopy(mask2)
        mask3 = cv2.dilate(mask3, (3, 3))
        mask3 = cv2.dilate(mask3, (3, 3))
        mask3 = cv2.erode(mask3, (3, 3))
        mask3 = cv2.erode(mask3, (3, 3))
        mask3 = cv2.dilate(mask3, (3, 3))
        mask3 = cv2.erode(mask3, (3, 3))

        _, contours, hierarchy = cv2.findContours(mask3, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

        if len(contours):
            def box_area(contour):
                return abs(contour[2])*(contour[3])
            max_contour = deepcopy(contours[0])
            max_box = cv2.boundingRect(max_contour)
            for contour in contours:
                box = cv2.boundingRect(contour)
                if box_area(max_box) < box_area(box):
                    max_contour = deepcopy(contour)
                    max_box = box

            target2 = target * mask3[:, :, np.newaxis]
            cv2.drawContours(target2, [max_contour], 0, (0,0,255), 2)
            max_box = [ max_box[0]+x1, max_box[1]+y1, max_box[2], max_box[3]]
            return target2, max_box

        return None


if __name__ == '__main__':
    print('Test Zone')

    e = ObjectExtractor()
    e.initialize('test1.jpg')