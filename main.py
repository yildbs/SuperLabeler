import sys
import os
import glob
import shutil
from PyQt5.QtWidgets import *
from PyQt5.QtCore import QDir, Qt, QTimer, pyqtSignal
from PyQt5.QtGui import *
from PyQt5 import uic, QtCore, QtGui, QtWidgets

from copy import deepcopy

import objectmanager

main_form_class = uic.loadUiType('Form2.ui')[0]

class MainWindow(QMainWindow, main_form_class):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.setWindowTitle("Super Labeler")

        #Initialize GUI
        self.lineEdit_BaseDirectory.setText('/home/yildbs/Train/Anyang_Temp')

        #Initialize variables
        self.tree = self.treeView_DirectoryTree
        self.model = QFileSystemModel()

        self.foregrounds = []
        self.backgrounds = []

        self.cur_dir = ''

        self.current_foreground_path = ''
        self.current_background_path = ''

        self.objects_foreground = objectmanager.ObjectManager()
        self.objects_background = objectmanager.ObjectManager()

        self.ctrl_pressed = False

        self.scene_foreground = QGraphicsScene()
        self.graphicsView_foreground.setScene(self.scene_foreground)

        self.foreground_changed = False

        self.about_mouse = {}
        self.about_mouse['pressed_left'] = False
        self.about_mouse['pressed_right'] = False
        self.about_mouse['pressed_ctrl'] = False
        self.about_mouse['new_rect'] = False

        self.property_paging = {}
        self.property_paging['current_index_foreground'] = 0

        self.property_folder_strings = []
        self.property_folder_strings.append('for_yolo')
        self.property_folder_strings.append('for_yolobgs')
        self.property_folder_strings.append('for_classifier')
        self.property_folder_strings.append('there_is_not_car')
        self.property_folder_strings.append('is_gray')
        self.property_folder_strings.append('is_people_NG')
        self.property_folder_strings.append('is_soldier')

        self.property_folder = {}
        for str in self.property_folder_strings:
            self.property_folder[str] = False

        self.comboboxes = []

        self.fg_bg_converted =False

        # shortcut
        self.set_shortcuts()

        #Signal & Slots
        self.pushButton_Refresh.clicked.connect(self.refresh)
        self.treeView_DirectoryTree.clicked.connect(self.on_treeView_clicked)

        self.listWidget_backgrounds.clicked.connect(self.on_background_selected)
        self.listWidget_foregrounds.clicked.connect(self.on_foreground_selected)

        self.treeView_DirectoryTree.keyPressEvent = self.keyPressEvent
        self.treeView_DirectoryTree.keyReleaseEvent = self.keyReleaseEvent
        self.listWidget_backgrounds.keyPressEvent = self.keyPressEvent
        self.listWidget_backgrounds.keyReleaseEvent = self.keyReleaseEvent
        self.listWidget_foregrounds.keyPressEvent = self.keyPressEvent
        self.listWidget_foregrounds.keyReleaseEvent = self.keyReleaseEvent

        #multithreading
        self.timer = QTimer()
        self.timer.setInterval(30)
        self.timer.timeout.connect(self.thread_refresh_display)
        self.timer.start()

    def refresh(self):
        basedir = self.lineEdit_BaseDirectory.text()

        self.model.setRootPath(basedir)
        self.model.setFilter(QDir.Dirs | QDir.NoDotAndDotDot)

        self.tree.setModel(self.model)
        self.tree.setRootIndex(self.model.index(basedir))
        self.tree.header().hideSection(1)
        self.tree.header().hideSection(2)
        self.tree.header().hideSection(3)

    def on_treeView_clicked(self, index):
        index_item = self.model.index(index.row(), 0, index.parent())

        filename = self.model.fileName(index_item)
        filepath = self.model.filePath(index_item)

        self.dir_selected(filepath)

    def dir_selected(self, dir):
        self.cur_dir = dir
        self.foregrounds = sorted([os.path.basename(x) for x in glob.glob(dir + '/*.jpg')])
        self.backgrounds = sorted([os.path.basename(x) for x in glob.glob(dir + '/*.bgs.jpg')])

        self.listWidget_foregrounds.clear()
        self.listWidget_backgrounds.clear()

        if not self.fg_bg_converted:
            self.property_paging['current_index_foreground'] = 0

        for foreground in self.foregrounds:
            self.listWidget_foregrounds.addItem(foreground)
        for background in self.backgrounds:
            self.listWidget_backgrounds.addItem(background)

        self.refresh_property_folder()
        self.refresh_page()

    def refresh_property_folder(self):
        for str in self.property_folder_strings:
            if len(glob.glob(self.cur_dir + '/' + str)):
                self.property_folder[str] = True
            else:
                self.property_folder[str] = False

        table = self.tableWidget_folder_property
        table.clear()
        table.setColumnCount(2)
        table.setRowCount(len(self.property_folder_strings))

        table.setHorizontalHeaderLabels(["Property", "Value"])
        table.horizontalHeaderItem(0).setTextAlignment(Qt.AlignCenter)

        for index, str in enumerate(self.property_folder_strings):
            table.setItem(index, 0, QTableWidgetItem(str))
            table.setItem(index, 1, QTableWidgetItem("True" if self.property_folder[str] else "False"))


    def refresh_page(self):
        if len(self.foregrounds) > 0:
            if self.property_paging['current_index_foreground'] < 0:
                self.property_paging['current_index_foreground'] = 0
            elif self.property_paging['current_index_foreground'] >= len(self.foregrounds):
                self.property_paging['current_index_foreground'] = len(self.foregrounds) - 1
            self.listWidget_foregrounds.setCurrentRow(self.property_paging['current_index_foreground'])
            self.listWidget_foregrounds.clicked.emit(self.listWidget_foregrounds.currentIndex())
        else:
            self.property_paging['current_index_foreground'] = 0


    def on_foreground_selected(self, index):
        filename =  self.cur_dir + '/' + index.data()
        if self.current_foreground_path != filename:
            print(filename)
            self.property_paging['current_index_foreground'] = index.row()
            self.current_foreground_path = filename
            self.new_foreground()

    def on_background_selected(self, index):
        filename =  self.cur_dir + '/' + index.data()
        if self.current_background_path != filename:
            print(filename)
            self.current_background_path = filename
            self.background_changed()

    def new_foreground(self):
        image = QImage(self.current_foreground_path)
        if not image.isNull():

            # item_rect.mouseMoveEvent = self.on_item_rect_moved
            self.scene_foreground.mouseMoveEvent = self.on_mouse_moved
            self.scene_foreground.mousePressEvent = self.on_mouse_pressed
            self.scene_foreground.mouseReleaseEvent = self.on_mouse_released

            self.graphicsView_foreground.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
            self.graphicsView_foreground.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

            size = image.size()
            width_org = size.width()
            height_org = size.height()

            self.objects_foreground.initialize(self.current_foreground_path.replace('jpg', 'xml'), width_org, height_org, 960, 540, self.fg_bg_converted)


            self.foreground_image = image.scaled(960, 540)
            item_foreground = QGraphicsPixmapItem(QPixmap.fromImage(self.foreground_image))

            self.foreground_changed = True
            self.fg_bg_converted = False

    def background_changed(self):
        pass

    class DoubleClickableItem(QGraphicsRectItem):
        def __init__(self, rect, parent, set_label, get_label):
            super().__init__(rect)
            self.parent = parent
            self.set_label = set_label
            self.get_label = get_label

        def mouseDoubleClickEvent(self, e):
            self.combo = QComboBox(self.parent.graphicsView_foreground)
            self.combo.setGeometry(e.scenePos().x(), e.scenePos().y(), 130, 40)
            with open("labels.txt", "r") as f:
                self.combo.addItem(self.get_label())
                for line in f.readlines():
                    line.replace('\n','', len(line))
                    line.replace('\r','', len(line))
                    line.replace('\t','', len(line))
                    self.combo.addItem(line)
            self.combo.currentIndexChanged.connect(lambda: self.set_label(self.combo.currentText()))
            self.combo.show()
            self.parent.comboboxes.append(self.combo)

    def thread_refresh_display(self):
        if self.foreground_changed:
            self.foreground_changed = False

            self.scene_foreground.clear()
            item_foreground = QGraphicsPixmapItem(QPixmap.fromImage(self.foreground_image))
            self.scene_foreground.addItem(item_foreground)

            objects = self.objects_foreground.getobjects()
            for obj in objects:
                # rect
                # item_rect = QGraphicsRectItem(QtCore.QRectF(obj.x1, obj.y1, obj.x2-obj.x1, obj.y2-obj.y1))
                item_rect = self.DoubleClickableItem(QtCore.QRectF(obj.x1, obj.y1, obj.x2-obj.x1, obj.y2-obj.y1),
                                                     parent=self,
                                                     set_label=obj.set_label,
                                                     get_label=obj.get_label )
                item_rect.setPen(obj.prop['line_color'])
                if obj.selected:
                    item_rect.setBrush(obj.prop['highlight_color'])
                elif obj.prop['area_fullfill']:
                    item_rect.setBrush(obj.prop['area_color'])

                # label
                item_label = QGraphicsTextItem(obj.label)
                item_label.setPos(QtCore.QPoint(obj.x1, obj.y1))
                item_label.setDefaultTextColor(obj.prop['text_color'])

                item_lt = QGraphicsEllipseItem(obj.x1-obj.prop['vertex_r_lt']/2, obj.y1-obj.prop['vertex_r_lt']/2, obj.prop['vertex_r_lt'], obj.prop['vertex_r_lt']); item_lt.setBrush(obj.prop['vertex_color'])
                item_rt = QGraphicsEllipseItem(obj.x2-obj.prop['vertex_r_rt']/2, obj.y1-obj.prop['vertex_r_rt']/2, obj.prop['vertex_r_rt'], obj.prop['vertex_r_rt']); item_rt.setBrush(obj.prop['vertex_color'])
                item_lb = QGraphicsEllipseItem(obj.x1-obj.prop['vertex_r_lb']/2, obj.y2-obj.prop['vertex_r_lb']/2, obj.prop['vertex_r_lb'], obj.prop['vertex_r_lb']); item_lb.setBrush(obj.prop['vertex_color'])
                item_rb = QGraphicsEllipseItem(obj.x2-obj.prop['vertex_r_rb']/2, obj.y2-obj.prop['vertex_r_rb']/2, obj.prop['vertex_r_rb'], obj.prop['vertex_r_rb']); item_rb.setBrush(obj.prop['vertex_color'])

                # add
                self.scene_foreground.addItem(item_rect)
                self.scene_foreground.addItem(item_label)

                self.scene_foreground.addItem(item_lt)
                self.scene_foreground.addItem(item_rt)
                self.scene_foreground.addItem(item_lb)
                self.scene_foreground.addItem(item_rb)


    def refresh_display_background(self):
        pass

    def refresh_display_diff(self):
        pass

    ####################################################
    # mouse & keyboard
    ####################################################
    def on_mouse_moved(self, p):
        self.foreground_changed = self.objects_foreground.mouse_event(self.about_mouse, p.scenePos().x(), p.scenePos().y())

    def on_mouse_pressed(self, p):
        if p.button() == 1: self.about_mouse['pressed_left'] = True
        elif p.button() == 2: self.about_mouse['pressed_right'] = True
        self.foreground_changed = self.objects_foreground.mouse_event(self.about_mouse, p.scenePos().x(), p.scenePos().y())

        for combo in self.comboboxes:
            combo.close()
        self.comboboxes.clear()

    def on_mouse_released(self, p):
        if p.button() == 1: self.about_mouse['pressed_left'] = False
        elif p.button() == 2: self.about_mouse['pressed_right'] = False
        self.foreground_changed = self.objects_foreground.mouse_event(self.about_mouse, p.scenePos().x(), p.scenePos().y())

    def keyPressEvent(self, p):
        self.ctrl_pressed = p.modifiers() == Qt.ControlModifier
        self.about_mouse['pressed_ctrl'] = self.ctrl_pressed

        try:
            if p.text() == '1' :
                print('')
            self.functions[p.text()]()
        except Exception as e:
            print(e)
            pass

    def keyReleaseEvent(self, p):
        self.ctrl_pressed = p.modifiers() == Qt.ControlModifier
        self.about_mouse['pressed_ctrl'] = self.ctrl_pressed

    #####################################################################################
    # shortcut functions
    #####################################################################################
    def set_shortcuts(self):
        self.functions = {}
        self.functions['a'] = self.go_to_previous_foreground
        self.functions['d'] = self.go_to_next_foreground

        self.functions['e'] = self.delete_selected

        self.functions['c'] = self.copy_selected
        self.functions['v'] = self.paste_objects

        self.functions['w'] = self.make_new_object

        self.functions['f'] = self.set_as_foreground
        self.functions['b'] = self.set_as_background

        self.functions['r'] = self.set_as_ng
        self.functions['t'] = self.set_as_g

        for index, string in enumerate(self.property_folder_strings):
            self.functions[str(index+1)] = (lambda s: (lambda: self.toggle_property(s)))(string)

    def go_to_previous_foreground(self):
        self.property_paging['current_index_foreground'] -= 1
        self.refresh_page()

    def go_to_next_foreground(self):
        self.property_paging['current_index_foreground'] += 1
        self.refresh_page()

    def delete_selected(self):
        self.objects_foreground.delete_selected()
        self.foreground_changed = True

    def copy_selected(self):
        self.objects_foreground.copy_selected()
        self.foreground_changed = True

    def paste_objects(self):
        self.objects_foreground.paste_objects()
        self.foreground_changed = True

    def make_new_object(self):
        self.objects_foreground.make_new_object()
        self.foreground_changed = True

    def set_as_foreground(self):
        src_jpg = self.current_foreground_path
        if '.bgs' in src_jpg:
            dst_jpg = src_jpg.replace('.bgs', '')
            os.rename(src_jpg, dst_jpg)

            src_xml = src_jpg.replace('.jpg', '.xml')
            dst_xml = dst_jpg.replace('.jpg', '.xml')
            os.rename(src_xml, dst_xml)

            self.fg_bg_converted =True
            self.treeView_DirectoryTree.clicked.emit(self.treeView_DirectoryTree.currentIndex())

    def set_as_background(self):
        src_jpg = self.current_foreground_path
        if '.bgs' not in src_jpg:
            dst_jpg = src_jpg.replace('.jpg', '.bgs.jpg')
            os.rename(src_jpg, dst_jpg)

            src_xml = src_jpg.replace('.jpg', '.xml')
            dst_xml = dst_jpg.replace('.jpg', '.xml')
            os.rename(src_xml, dst_xml)

            self.fg_bg_converted =True
            self.treeView_DirectoryTree.clicked.emit(self.treeView_DirectoryTree.currentIndex())

    def set_as_ng(self):
        self.objects_foreground.set_as_ng()
        self.foreground_changed = True

    def set_as_g(self):
        self.objects_foreground.set_as_g()
        self.foreground_changed = True

    def toggle_property(self, key):
        print(key)
        if self.property_folder[key]:
            try:
                # os.remove(self.cur_dir + '/' + key + '/.*')
                # os.removedirs(self.cur_dir + '/' + key)
                shutil.rmtree(self.cur_dir + '/' + key)
            except Exception as e:
                print(e)
        else:
            try:
                os.makedirs(self.cur_dir + '/' + key)
            except Exception as e:
                print(e)
        self.refresh_property_folder()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    app.exec_()
