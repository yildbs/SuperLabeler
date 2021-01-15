from threading import Thread, Lock
from copy import deepcopy
from PyQt5.QtGui import QColor
import math
import sys
import cv2
import random
from SuperLabeler import objectextractor
from SuperLabeler import util


class Object():
    def __init__(self, label, x1, y1, x2, y2, width =0, height=0):
        self.selected = False
        self.__label = label.replace('\n', '', len(label)).replace('\r', '', len(label))
        self.x1 = x1
        self.y1 = y1
        self.x2 = x2
        self.y2 = y2
        self.prop = {}

        self.width = width
        self.height = height

        self.circle_small = 10
        self.circle_big = 20

        self.reset_property()

    def __eq__(self, other):
        isequal = True
        if self.x1 != other.x1: isequal = False
        if self.y1 != other.y1: isequal = False
        if self.x2 != other.x2: isequal = False
        if self.y2 != other.y2: isequal = False
        if self.__label != other.__label: isequal = False
        return isequal

    def set_label(self, label):
        self.__label = label.replace('\n', '', len(label)).replace('\r', '', len(label))

    def get_label(self):
        return self.__label

    def set_as_ng(self):
        if '_NG' in self.__label:
            self.__label = self.__label.replace('_NG', '')

    def set_as_g(self):
        if '_NG' not in self.__label:
            self.__label = self.__label + '_NG'

    def reset_property(self):
        self.prop['text_color'] = QColor("yellow")
        self.prop['line_color'] = QColor("black")
        self.prop['area_color'] = QColor("black")

        self.prop['highlight_color'] = QColor.fromRgb(232, 255, 158, 150)

        self.prop['area_fulfil'] = False

        self.prop['vertex_color'] = QColor("green")
        self.prop['vertex_r_lt'] = self.circle_small
        self.prop['vertex_r_rt'] = self.circle_small
        self.prop['vertex_r_lb'] = self.circle_small
        self.prop['vertex_r_rb'] = self.circle_small

        if self.__label == 'nothing':
            self.prop['text_color'] = QColor.fromRgb(173, 148, 108)
            self.prop['area_color'] = QColor.fromRgb(173, 148, 108, 80)
            self.prop['line_color'] = QColor.fromRgb(173, 148, 108)
            self.prop['area_fulfil'] = True
        elif '_NG' in self.__label:
            self.prop['text_color'] = QColor("red")
            self.prop['line_color'] = QColor("red")

    def click_vertex(self, x, y):
        p = [x, y]
        lt = [self.x1, self.y1]
        rt = [self.x2, self.y1]
        lb = [self.x1, self.y2]
        rb = [self.x2, self.y2]

        if util.get_distance(lt, p) < self.circle_small:
            self.selected = True
            self.x1, self.y1 = x, y
            return self.moved_lt
        elif util.get_distance(rt, p) < self.circle_small:
            self.selected = True
            self.x2, self.y1 = x, y
            return self.moved_rt
        elif util.get_distance(lb, p) < self.circle_small:
            self.selected = True
            self.x1, self.y2 = x, y
            return self.moved_lb
        elif util.get_distance(rb, p) < self.circle_small:
            self.selected = True
            self.x2, self.y2 = x, y
            return self.moved_rb
        return None

    def click_area(self, x, y):
        p = [x, y]
        lt = [self.x1, self.y1]
        rt = [self.x2, self.y1]
        lb = [self.x1, self.y2]
        rb = [self.x2, self.y2]

        if self.x1 < x < self.x2 and self.y1 < y < self.y2:
            self.selected = not self.selected
            return self.moved_rect
        return None

    def react_mouse_vertex(self, x, y):
        p = [x, y]
        lt = [self.x1, self.y1]
        rt = [self.x2, self.y1]
        lb = [self.x1, self.y2]
        rb = [self.x2, self.y2]

        if util.get_distance(lt, p) < self.circle_small:
            self.prop['vertex_r_lt'] = self.circle_big
            return True
        elif util.get_distance(rt, p) < self.circle_small:
            self.prop['vertex_r_rt'] = self.circle_big
            return True
        elif util.get_distance(lb, p) < self.circle_small:
            self.prop['vertex_r_lb'] = self.circle_big
            return True
        elif util.get_distance(rb, p) < self.circle_small:
            self.prop['vertex_r_rb'] = self.circle_big
            return True
        return False

    def react_mouse_area(self, x, y):
        p = [x, y]
        lt = [self.x1, self.y1]
        rt = [self.x2, self.y1]
        lb = [self.x1, self.y2]
        rb = [self.x2, self.y2]

        if self.x1 < x < self.x2 and self.y1 < y < self.y2:
            self.prop['area_fulfil'] = True
            self.prop['area_color'] = QColor.fromRgb(252, 186, 3, 80)
            return True
        return False

    def drag(self, start, end):
        start_x = start[0]
        start_y = start[1]
        end_x = end[0]
        end_y = end[1]

        if start_x <= self.x1 <= self.x2 <= end_x and start_y <= self.y1 <= self.y2 <= end_y:
            self.selected = True
            return True
        return False

    def moved_lt(self, dx, dy):
        self.selected = True
        self.x1 += dx
        self.y1 += dy
        self.x1 = min(max(self.x1, 0), self.width-1)
        self.y1 = min(max(self.y1, 0), self.height-1)
        return self

    def moved_rt(self, dx, dy):
        self.selected = True
        self.x2 += dx
        self.y1 += dy
        self.x2 = min(max(self.x2, 0), self.width-1)
        self.y1 = min(max(self.y1, 0), self.height-1)
        return self

    def moved_lb(self, dx, dy):
        self.selected = True
        self.x1 += dx
        self.y2 += dy
        self.x1 = min(max(self.x1, 0), self.width-1)
        self.y2 = min(max(self.y2, 0), self.height-1)
        return self

    def moved_rb(self, dx, dy):
        self.selected = True
        self.x2 += dx
        self.y2 += dy
        self.x2 = min(max(self.x2, 0), self.width-1)
        self.y2 = min(max(self.y2, 0), self.height-1)
        return self

    def moved_rect(self, dx, dy):
        self.selected = True
        dx = max(dx, -self.x1)
        dy = max(dy, -self.y1)
        dx = min(dx, self.width-1-self.x2)
        dy = min(dy, self.height-1-self.y2)
        self.x1 += dx
        self.y1 += dy
        self.x2 += dx
        self.y2 += dy
        return self

    def arrange(self):
        x1 = self.x1
        y1 = self.y1
        x2 = self.x2
        y2 = self.y2
        self.x1 = min(x1, x2)
        self.y1 = min(y1, y2)
        self.x2 = max(x1, x2)
        self.y2 = max(y1, y2)

    def area(self):
        return abs((self.x2-self.x1) * (self.y2-self.y1))

    def length_intersection(self, other):
        left = max(self.x1, other.x1)
        right = min(self.x2, other.x2)
        top = max(self.y1, other.y1)
        bot = min(self.y2, other.y2)
        return [right - left, bot - top]

    def area_intersection(self, other):
        w, h = self.length_intersection(other)
        if w < 0 or h < 0:
            return 0
        area = w * h
        return area

    def area_union(self, other):
        i = self.area_intersection(other)
        u = self.area() + other.area() - i
        return u

    def iou(self, other):
        self.arrange()
        other.arrange()
        i = self.area_intersection(other)
        u = self.area_union(other)
        return i / u

    def union(self, other):
        self.arrange()
        other.arrange()

        x1 = min(self.x1, other.x1)
        x2 = max(self.x2, other.x2)
        y1 = min(self.y1, other.y1)
        y2 = max(self.y2, other.y2)

        self.x1 = x1
        self.x2 = x2
        self.y1 = y1
        self.y2 = y2

    def scale(self, fx, fy):
        self.x1 = self.x1 * fx
        self.x2 = self.x2 * fx
        self.y1 = self.y1 * fy
        self.y2 = self.y2 * fy


class ObjectManager():
    def __init__(self):
        self.width_display = 0
        self.height_display = 0
        self.__objects = []
        self.__objects_previous = []
        self.__objects_copied = []

        self.states_command = {}
        self.states_command['move_vertex'] = False
        self.states_command['move_rect'] = False
        self.states_command['make_new_rect'] = False
        self.states_command['dragging_left'] = False
        self.states_command['dragging_right'] = False
        self.states_command['x'] = 0
        self.states_command['y'] = 0
        self.states_command['start_x'] = 0
        self.states_command['start_y'] = 0

        self.xml_path = None
        self.initialized = False

        self.extractor = objectextractor.ObjectExtractor()

        self.roi = None

    def initialize(self, xml_path, jpg_path, width_org, height_org, width_display, height_display, do_not_save_xml):
        if self.xml_path is not None and not do_not_save_xml:
            util.save_xml(self.xml_path, self.__objects, width_org, height_org)

        self.image = cv2.imread(jpg_path)
        self.extractor.initialize(self.image)

        self.width_org = width_org
        self.height_org = height_org
        self.width_display = width_display
        self.height_display = height_display

        self.fx = self.width_display/ self.width_org
        self.fy = self.height_display / self.height_org

        self.states_command['move_vertex'] = False
        self.states_command['move_rect'] = False
        self.states_command['make_new_rect'] = False
        self.states_command['dragging_left'] = False
        self.states_command['dragging_right'] = False
        self.states_command['drawing_mask'] = False
        self.states_command['x'] = 0
        self.states_command['y'] = 0
        self.states_command['start_x'] = 0
        self.states_command['start_y'] = 0
        self.states_command['states_key_input'] = {}

        objects, fileread, changed = util.read_xml(xml_path)
        self.xml_path = xml_path

        self.__objects_previous = []
        self.__objects = []
        for label, x1, y1, x2, y2 in objects:
            do_not_add = False
            if x1 < 0 or y1 < 0 or x2 < 0 or y2 < 0:
                do_not_add = True
            if x1 >= width_org or y1 >= height_org or x2 >= width_org or y2 >= height_org :
                do_not_add = True

            if not do_not_add:
                obj = Object(label, x1, y1, x2, y2, width_org, height_org)
                obj.selected = True
                self.__objects.append(obj)

        self.initialized = True

    def get_objects(self, for_background=False, do_scale=True):
        objects = []

        try:
            if self.states_command['states_key_input']['pressed_shift'] :
                return objects
        except Exception as e:
            pass

        for object_ in self.__objects:
            label = object_.get_label()
            x1 = min(object_.x1, object_.x2)
            x2 = max(object_.x1, object_.x2)
            y1 = min(object_.y1, object_.y2)
            y2 = max(object_.y1, object_.y2)

            if do_scale:
                obj = Object(label, int(x1 * self.fx), int(y1 * self.fy), int(x2 * self.fx), int(y2 * self.fy))
            else:
                obj = Object(label, int(x1), int(y1), int(x2), int(y2))
            obj.selected = object_.selected
            obj.prop = object_.prop
            obj.set_label = object_.set_label

            if not for_background:
                objects.append(obj)
            else:
                if 'unrelated_with_yolobgs' in label:
                    pass
                elif 'nothing' in label:
                    pass
                else:
                    objects.append(obj)

        if not for_background:
            if self.states_command['dragging_left'] or self.states_command['dragging_right']:
                x1 = min(self.states_command['x'], self.states_command['start_x'])
                x2 = max(self.states_command['x'], self.states_command['start_x'])
                y1 = min(self.states_command['y'], self.states_command['start_y'])
                y2 = max(self.states_command['y'], self.states_command['start_y'])
                obj = Object( '@DRAG', int(x1 * self.fx), int(y1 * self.fy), int(x2 * self.fx), int(y2 * self.fy))

                if do_scale:
                    obj = Object( '@DRAG', int(x1 * self.fx), int(y1 * self.fy), int(x2 * self.fx), int(y2 * self.fy))
                else:
                    obj = Object( '@DRAG', int(x1), int(y1), int(x2), int(y2))

                obj.prop['area_color'] = QColor.fromRgb(220, 232, 58, 122)
                obj.prop['area_fulfil'] = True
                objects.append(obj)
        return objects

    def get_difference(self, other, width_display=0, height_display=0):
        objects1 = self.get_objects(True, do_scale=False)
        objects2 = other.get_objects(True, do_scale=False)

        sameobjects = []
        for object1 in objects1:
            for object2 in objects2:
                iou = object1.iou(object2)
                if iou > 0.9:
                    sameobjects.append(object1)
                    sameobjects.append(object2)

        for sameobject in sameobjects:
            try: objects1.remove(sameobject)
            except: pass
            try: objects2.remove(sameobject)
            except: pass

        differences = []
        for object1 in objects1:
            differences.append(object1)
        for object2 in objects2:
            differences.append(object2)

        while True:
            if len(differences) == 0:
                break
            object1 = differences[0]
            object2 = differences[0]

            overlapped = False
            for diff1 in differences:
                for diff2 in differences:
                    if diff1 is diff2:
                        continue
                    iou = diff1.iou(diff2)
                    if iou > 0.1:
                        object1 = diff1
                        object2 = diff2
                        overlapped = True
                        break
                if overlapped:
                    break
            if not overlapped:
                break

            integrated = deepcopy(object1)
            integrated.union(object2)

            try: differences.remove(object1)
            except: pass
            try: differences.remove(object2)
            except: pass
            differences.append(integrated)


        if width_display != 0 and height_display!=0:
            fx = width_display / self.width_org
            fy = height_display / self.height_org

            for diff in differences:
                diff.scale(fx, fy)

        return differences

    def key_input_event(self, states_key_input, x, y):
        if not self.initialized:
            return False, self.states_command
        changed = False

        self.states_command['states_key_input'] = states_key_input
        org_x = x
        org_y = y

        x = min(math.ceil(max(x, 0) / self.fx), self.width_org - 1)
        y = min(math.ceil(max(y, 0) / self.fy), self.height_org - 1)

        dx = x - self.states_command['x']
        dy = y - self.states_command['y']

        if not states_key_input['slow_mode']:
            self.states_command['x'] = x
            self.states_command['y'] = y
        else:
            if dx > 6:
                dx = 1
                self.states_command['x'] = x
            elif dx<-6:
                dx = -1
                self.states_command['x'] = x
            else:
                dx = 0
            if dy > 6:
                dy = 1
                self.states_command['y'] = y
            elif dy<-6:
                dy = -1
                self.states_command['y'] = y
            else:
                dy = 0

        #####################################################
        if self.states_command['move_vertex']:
            changed = True
            try:
                self.roi = deepcopy(self.function_moved(dx, dy))
                self.roi.scale(self.fx, self.fy)
                self.roi.arrange()
            except Exception as e:
                pass

            if states_key_input['pressed_left']:
                pass
            else:
                self.states_command['move_vertex'] = False
                self.function_moved = None
                for obj in self.__objects:
                    obj.arrange()

        elif self.states_command['move_rect']:
            pass
        elif self.states_command['make_new_rect']:
            pass
        elif self.states_command['dragging_left']:
            if states_key_input['pressed_left']:
                pass
            else:
                self.states_command['dragging_left'] = False
                for obj in self.__objects:
                    start = [min(self.states_command['start_x'], x), min(self.states_command['start_y'], y)]
                    end = [max(self.states_command['start_x'], x), max(self.states_command['start_y'], y)]
                    obj.drag(start, end)
            changed = True
        elif self.states_command['dragging_right']:
            if states_key_input['pressed_right']:
                pass
            else:
                self.states_command['dragging_right'] = False

                for obj in self.__objects:
                    obj.selected = False

                if abs((self.states_command['start_x']-x) * (self.states_command['start_y']-y)) > 10:
                    make_new = False
                    x1 = sys.maxsize
                    y1 = sys.maxsize
                    x2 = 0
                    y2 = 0
                    for obj in self.__objects:
                        start = [min(self.states_command['start_x'], x), min(self.states_command['start_y'], y)]
                        end = [max(self.states_command['start_x'], x), max(self.states_command['start_y'], y)]
                        if obj.drag(start, end):
                            x1 = min(x1, obj.x1)
                            y1 = min(y1, obj.y1)
                            x2 = max(x2, obj.x2)
                            y2 = max(y2, obj.y2)
                            make_new = True

                    if make_new:
                        self.keep_current()
                        exist = False
                        new_obj = Object('people', x1, y1, x2, y2, self.width_org, self.height_org)
                        new_obj.selected = True
                        for obj in self.__objects:
                            if new_obj == obj:
                                exist = True
                                break
                        if not exist:
                            self.__objects.append(new_obj)

                else:
                    for obj in self.__objects:
                        if obj.click_area(x, y) is not None:
                            break
                    if not self.delete_selected():
                        width_half = random.randint(20, 100)
                        height_half = random.randint(20, 100)
                        new_obj = Object('nothing', x-width_half, y-height_half, x+width_half, y+height_half, self.width_org, self.height_org)
                        new_obj.selected = True
                        self.__objects.append(new_obj)


            changed = True
        elif self.states_command['drawing_mask']:
            self.extractor.draw_mask(x, y)
            if states_key_input['pressed_left']:
                pass
            else:
                self.states_command['drawing_mask'] = False
                ret = self.extractor.analyze()
                if ret is None:
                    pass
                else:
                    for obj in self.__objects:
                        obj.selected = False

                    image, box = ret
                    x1, y1, w, h = box
                    new_obj = Object('@CONTOUR', x1, y1, x1+w, y1+h, self.width_org, self.height_org)
                    new_obj.selected = True
                    for obj in self.__objects:
                        if new_obj == obj:
                            break
                    else:
                        self.__objects.append(new_obj)

        #####################################################
        else:
            if states_key_input['pressed_left']:
                if states_key_input['new_rect']:
                    pass

                elif states_key_input['pressed_shift']:
                    self.states_command['drawing_mask'] = True
                    self.extractor.reset_mask()

                elif states_key_input['pressed_ctrl']:
                    for obj in self.__objects:
                        ret = obj.click_vertex(x, y) or obj.click_area(x, y)
                        if ret is None:
                            continue
                        else:
                            break
                else:
                    for obj in self.__objects:
                        obj.selected = False

                    self.function_moved = None
                    for obj in self.__objects:
                        self.function_moved = obj.click_vertex(x, y)
                        if self.function_moved is None:
                            continue
                        else:
                            self.states_command['move_vertex'] = True
                            break

                    if not self.states_command['move_vertex'] :
                        for obj in self.__objects:
                            self.function_moved = obj.click_area(x, y)
                            if self.function_moved is None:
                                continue
                            else:
                                self.states_command['move_vertex'] = True
                                break

                    if self.function_moved is None:
                        self.states_command['dragging_left'] = True
                        self.states_command['start_x'] = x
                        self.states_command['start_y'] = y
                    else:
                        self.keep_current()
                        self.function_moved(dx, dy)

            elif states_key_input['pressed_right']:
                self.states_command['dragging_right'] = True
                self.states_command['start_x'] = x
                self.states_command['start_y'] = y
            else:
                changed = True
                for obj in self.__objects:
                    obj.reset_property()

                react = False
                for obj in self.__objects:
                    if obj.react_mouse_vertex(x, y):
                        react = True
                        break

                if not react:
                    for obj in self.__objects:
                        if obj.react_mouse_area(x, y):
                            break
        return changed, self.states_command

    def delete_selected(self):
        self.keep_current()
        len_prev = len(self.__objects)
        self.__objects = [obj for obj in self.__objects if not obj.selected]
        return True if len_prev != len(self.__objects) else False

    def copy_selected(self):
        self.__objects_copied = deepcopy([obj for obj in self.__objects if obj.selected])

    def paste_objects(self):
        self.keep_current()
        for copied in self.__objects_copied:
            exist = False
            for obj in self.__objects:
                if copied == obj:
                    exist = True
                    break

            if not exist:
                self.__objects.append(deepcopy(copied))

    def make_new_object(self):
        self.keep_current()

        obj = Object('@NEW', self.states_command['x'] - 50, self.states_command['y'] - 50, self.states_command['x'] + 50, self.states_command['y'] + 50, self.width_org, self.height_org)
        self.__objects.append(obj)

    def set_as_g(self):
        self.keep_current()
        for obj in self.__objects:
            if obj.selected:
                obj.set_as_g()
                obj.reset_property()

    def set_as_ng(self):
        self.keep_current()
        for obj in self.__objects:
            if obj.selected:
                obj.set_as_ng()
                obj.reset_property()

    def keep_current(self):
        self.__objects_previous.append(deepcopy(self.__objects))
        if len(self.__objects_previous) > 30:
            self.__objects_previous.pop(0)

    def undo(self):
        if len(self.__objects_previous) > 0:
            self.__objects = deepcopy(self.__objects_previous.pop())

    def select_all(self):
        for obj in self.__objects:
            obj.selected = True

    def get_roi(self):
        if self.roi is not None:
            return self.roi
        return None
