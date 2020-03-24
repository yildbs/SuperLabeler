import numpy as np
import cv2


class ObjectExtractor:
    def __init__(self):
        pass

    def initialize(self, image_path):
        self.image = cv2.imread(image_path)
        self.mask = np.zeros(self.image.shape[:2], np.uint8)
        self.bgd_model = np.zeros((1, 65), np.float64)
        self.fgd_model = np.zeros((1, 65), np.float64)

        # # rect = (0, 0, 1280, 960)
        # rect = (0, 0, 500, 500)
        # cv2.grabCut(image, mask, rect, bgd_model, fgd_model, 5, cv2.GC_INIT_WITH_RECT)
        # mask2 = np.where((mask==2) |(mask==0), 0, 1).astype('uint8')
        # image = image * mask2[:, : , np.newaxis]
        # cv_image = image.astype(np.uint8)
        #
        # cv2.imshow('image', cv_image)
        # cv2.waitKey(0)



if __name__ == '__main__':
    print('Test Zone')

    e = ObjectExtractor()
    e.initialize('test1.jpg')