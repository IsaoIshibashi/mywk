# -*- coding: utf-8 -*-

# [how to use]
# python image_process.py image:=/image_raw

import rospy
from sensor_msgs.msg import Image
from cv_bridge import CvBridge, CvBridgeError
import cv2
import matplotlib.pyplot as plt
import matplotlib.animation as anim
from collections import OrderedDict
import numpy as np
import time


class ImageShow():

    def __init__(self, rows, cols):
        self._rows = rows      # for matplotlib
        self._cols = cols      # for matplotlib
        self._max_num = rows * cols
        self._cv_images = OrderedDict()     # support GrayScale only
        self._fig = plt.figure()

    def _reDraw(self, data):
        # print ('ImageShow._reDraw() start')
        plt.cla()
        index = 0
        for key in self._cv_images.keys():
            index = index + 1
            if (index > self._max_num):
                ros.loginfo('show space is overflow')
                break
            plt.subplot(self._rows, self._cols, index)
            plt.imshow(self._cv_images[key], 'gray')
            plt.title(key)
            plt.tick_params(labelbottom='off', labelleft='off')
            plt.subplots_adjust(left=0.075, bottom=0.05, right=0.95, top=0.95, wspace=0.15, hspace=0.15)

    def addCvImage(self, key, cv_image):
        self._cv_images[key] = cv_image

    def show(self):
        ani = anim.FuncAnimation(self._fig, self._reDraw, interval=300)
        plt.show()


class ProcessingImage():

    def __init__(self, img):
        self.img = img

    # 現在grayでも3channel colorで返す。
    def get_img(self):
        if len(self.img.shape) < 3:     # iplimage.shape is [x,y,colorchannel]
            return cv2.cvtColor(self.img, cv2.COLOR_GRAY2RGB)
        else:
            return self.img

    def __to_gray(self):
        self.img = cv2.cvtColor(self.img, cv2.COLOR_RGB2GRAY)

    def __detect_edge(self):
        EDGE_TH_LOW = 50
        EDGE_TH_HIGH = 150
        self.img = cv2.Canny(self.img, EDGE_TH_LOW, EDGE_TH_HIGH)

    def __threshold(self):
        self.img = cv2.adaptiveThreshold(self.img, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 5)

    def __blur(self):
        FILTER_SIZE = (5, 5)
        # bilateralFilterだと色の差も加味してそう
        # self.img = cv2.bilateralFilter(self.img, 5, 75, 75)
        self.img = cv2.GaussianBlur(self.img, FILTER_SIZE, 0)

    def __mask(self, vertices):
        # defining a blank mask to start with
        mask = np.zeros_like(self.img)

        # defining a 3 channel or 1 channel color to fill the mask with depending on the input image
        if len(self.img.shape) > 2:
            channel_count = self.img.shape[2]  # i.e. 3 or 4 depending on your image
            ignore_mask_color = (255,) * channel_count
        else:
            ignore_mask_color = 255

        vertices[0][0:, 0] = vertices[0][0:, 0] * self.img.shape[1]
        vertices[0][0:, 1] = vertices[0][0:, 1] * self.img.shape[0]

        int_vertices = vertices.astype(np.int32)

        # filling pixels inside the polygon defined by "vertices" with the fill color
        cv2.fillPoly(mask, int_vertices, ignore_mask_color)

        # trancerate the image only where mask pixels are nonzero
        self.img = cv2.bitwise_and(self.img, mask)

    def __houghline(self):
        THRESHOLD = 100
        MIN_LINE_LENGTH = 100.0
        MAX_LINE_GAP = 10.0
        return cv2.HoughLinesP(self.img, 1, np.pi / 180, THRESHOLD, MIN_LINE_LENGTH, MAX_LINE_GAP)

    def __get_segment(self, x1, y1, x2, y2):
        vy = y2 - y1
        vx = x2 - x1

        if vx == 0:
            m = 0.
        else:
            m = (float)(vy) / vx

        b = y1 - (m * x1)
        return m, b

    def __get_point_horizontal(self, m, b, y_ref):
        x = (y_ref - b) / m
        return x

    def __extrapolation_lines(self, lines):
        # 検出する線の傾き範囲
        EXPECT_RIGHT_LINE_M_MIN = -0.8
        EXPECT_RIGHT_LINE_M_MAX = -0.4
        EXPECT_LEFT_LINE_M_MIN = 0.4
        EXPECT_LEFT_LINE_M_MAX = 0.8

        if lines is None:
            return None

        right_line = np.empty((0, 6), float)
        left_line = np.empty((0, 6), float)

        for line in lines:
            for tx1, ty1, tx2, ty2 in line:
                if ty2 > ty1:
                    x1 = tx1
                    x2 = tx2
                    y1 = ty1
                    y2 = ty2
                else:
                    x1 = tx2
                    x2 = tx1
                    y1 = ty2
                    y2 = ty1

                m, b = self.__get_segment(x1, y1, x2, y2)
                if EXPECT_RIGHT_LINE_M_MIN < m < EXPECT_RIGHT_LINE_M_MAX:
                    # right side
                    right_line = np.append(right_line, np.array([[x1, y1, x2, y2, m, b]]), axis=0)
                elif EXPECT_LEFT_LINE_M_MIN < m < EXPECT_LEFT_LINE_M_MAX:
                    # left side
                    left_line = np.append(left_line, np.array([[x1, y1, x2, y2, m, b]]), axis=0)

        print 'right lines num:', right_line.size
        print 'left lines num:', left_line.size

        if (right_line.size == 0) and (left_line.size == 0):
            return None

        extrapolation_lines = []

        if (right_line.size > 0):

            right_m = right_line[:, 4].mean(axis=0)
            right_b = right_line[:, 5].mean(axis=0)
            right_y_max = right_line[:, 3].max(axis=0)
            right_y_min = right_line[:, 1].min(axis=0)

            right_x_min = self.__get_point_horizontal(right_m, right_b, right_y_min)
            right_x_max = self.__get_point_horizontal(right_m, right_b, right_y_max)

            right_x_min = int(right_x_min)
            right_x_max = int(right_x_max)
            right_y_min = int(right_y_min)
            right_y_max = int(right_y_max)

            extrapolation_lines.append([[right_x_min, right_y_min, right_x_max, right_y_max]])

        if (left_line.size > 0):

            left_m = left_line[:, 4].mean(axis=0)
            left_b = left_line[:, 5].mean(axis=0)
            left_y_max = left_line[:, 3].max(axis=0)
            left_y_min = left_line[:, 1].min(axis=0)

            left_x_min = self.__get_point_horizontal(left_m, left_b, left_y_min)
            left_x_max = self.__get_point_horizontal(left_m, left_b, left_y_max)

            left_x_min = int(left_x_min)
            left_x_max = int(left_x_max)
            left_y_min = int(left_y_min)
            left_y_max = int(left_y_max)

            extrapolation_lines.append([[left_x_min, left_y_min, left_x_max, left_y_max]])

        return extrapolation_lines

    def preprocess(self):
        self.__to_gray()
        self.__blur()
        self.__detect_edge()

    def detect_line(self, color_pre=[0, 255, 0], color_final=[255, 0, 0], thickness=4):
        MASK_V1 = [0. / 640., 479. / 480.]
        MASK_V2 = [100. / 640., 200. / 480.]
        MASK_V3 = [540. / 640., 200. / 480.]
        MASK_V4 = [640. / 640., 479. / 480.]

        # image mask
        vertices = np.array([[MASK_V1, MASK_V2, MASK_V3, MASK_V4]], dtype=np.float)
        self.__mask(vertices)

        # line detect
        pre_lines = self.__houghline()
        final_lines = self.__extrapolation_lines(pre_lines)

        # create image
        if len(self.img.shape) == 3:
            line_img = np.zeros((self.img.shape), np.uint8)
        else:
            line_img = np.zeros((self.img.shape[0], self.img.shape[1], 3), np.uint8)

        # draw pre_lines
        if (pre_lines is None):
            return
        for x1, y1, x2, y2 in pre_lines[0]:
            cv2.line(line_img, (x1, y1), (x2, y2), color_pre, thickness)
        self.img = line_img

        # draw final_lines
        if (final_lines is None):
            return
        for x1, y1, x2, y2 in final_lines[0]:
            cv2.line(line_img, (x1, y1), (x2, y2), color_final, thickness)
        self.img = line_img

    def overlay(self, img):
        ALPHA = 1.0
        BETA = 0.8
        GAMMA = 1.8
        color_img = self.get_img()
        self.img = cv2.addWeighted(color_img, ALPHA, img, BETA, GAMMA)


class RosImage():

    def __init__(self):
        rospy.init_node('image_process')
        self.__cv_bridge = CvBridge()
        self.__show = ImageShow(2, 3)
        self.__sub = rospy.Subscriber('image', Image, self.callback, queue_size=1)
        self.__pub = rospy.Publisher('image_processed', Image, queue_size=1)

    def callback(self, image_msg):
        # rospy.loginfo('rosImage.callback()')
        cv_image = self.__cv_bridge.imgmsg_to_cv2(image_msg, 'rgb8')

        pimg = ProcessingImage(cv_image)
        pimg.preprocess()
        pre_img = pimg.get_img()
        pimg.detect_line()
        pimg.overlay(pre_img)

        self.__pub.publish(self.__cv_bridge.cv2_to_imgmsg(pimg.get_img(), 'rgb8'))

    def main(self):
        # self.__show.show()
        rospy.spin()


if __name__ == '__main__':
    process = RosImage()
    process.main()
