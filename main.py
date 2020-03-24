import sys
import os
import glob
import shutil
from PyQt5.QtWidgets import *
from PyQt5.QtCore import QDir, Qt, QTimer, QObject, QEvent
from PyQt5.QtGui import *
from PyQt5 import uic, QtCore, QtGui, QtWidgets
import time
from copy import deepcopy
import objectmanager

main_form_class = uic.loadUiType('Form2.ui')[0]

class MainWindow(QMainWindow, main_form_class):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.setWindowTitle("Super Labeler")

        #Initialize GUI
        self.lineEdit_BaseDirectory.setText('/home/yildbs/Train/')

        #Initialize variables
        self.tree = self.treeView_directory_tree
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

        self.scene_background = QGraphicsScene()
        self.graphicsView_background.setScene(self.scene_background)
        self.background_changed = False

        self.scene_diffground = QGraphicsScene()
        self.graphicsView_diffground.setScene(self.scene_diffground)
        self.diffground_changed = False

        self.scene_zoomground = QGraphicsScene()
        self.graphicsView_zoomground.setScene(self.scene_zoomground)
        self.zoomground_changed = False

        self.about_mouse = {}
        self.about_mouse['pressed_left'] = False
        self.about_mouse['pressed_right'] = False
        self.about_mouse['pressed_ctrl'] = False
        self.about_mouse['new_rect'] = False
        self.about_mouse['current_x'] = 0
        self.about_mouse['current_y'] = 0

        self.property_paging = {}
        self.property_paging['current_index_foreground'] = 0
        self.property_paging['current_index_background'] = 0
        self.property_paging['current_index_directories'] = 0

        self.property_folder_strings = []
        self.property_folder_strings.append('for_yolo')
        self.property_folder_strings.append('for_yolobgs')
        self.property_folder_strings.append('there_is_no_car')
        self.property_folder_strings.append('is_gray')
        self.property_folder_strings.append('is_people_NG')
        self.property_folder_strings.append('is_soldier')

        self.zoom = 2.0

        self.property_folder = {}
        for str in self.property_folder_strings:
            self.property_folder[str] = False

        self.comboboxes = []

        self.fg_bg_converted =False

        self.directories = []

        # shortcut
        self.set_shortcuts()

        #Signal & Slots
        self.pushButton_Refresh.clicked.connect(self.refresh)
        self.treeView_directory_tree.clicked.connect(self.on_treeView_clicked)

        self.listWidget_backgrounds.clicked.connect(self.on_background_selected)
        self.listWidget_foregrounds.clicked.connect(self.on_foreground_selected)

        # Callback
        self.treeView_directory_tree.keyPressEvent = self.keyPressEvent
        self.treeView_directory_tree.keyReleaseEvent = self.keyReleaseEvent
        self.listWidget_backgrounds.keyPressEvent = self.keyPressEvent
        self.listWidget_backgrounds.keyReleaseEvent = self.keyReleaseEvent
        self.listWidget_foregrounds.keyPressEvent = self.keyPressEvent
        self.listWidget_foregrounds.keyReleaseEvent = self.keyReleaseEvent

        # multithreading
        self.timer = QTimer()
        self.timer.setInterval(30)
        self.timer.timeout.connect(self.thread_refresh_display)
        self.timer.start()

    def set_count_foregrounds(self, index, total):
        if total > 0:
            self.label_count_foregrounds.setText('(%d / %d)' %(index+1, total))
        else:
            self.label_count_foregrounds.setText('')

    def set_count_backgrounds(self, index, total):
        if total > 0:
            self.label_count_backgrounds.setText('(%d / %d)' %(index+1, total))
        else:
            self.label_count_backgrounds.setText('')

    def refresh(self):
        basedir = self.lineEdit_BaseDirectory.text()

        def on_directory_loaded():
            self.tree.expandAll()

        self.model.setRootPath(basedir)
        self.model.directoryLoaded.connect(on_directory_loaded)

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

        def deep(root, directories):
            row = self.model.rowCount(root)
            for y in range(row):
                child = root.child(y, 0)
                deep(child, directories)

            path = self.model.filePath(root)
            if len(glob.glob(path + '/*.jpg')) > 0:
                directories.append(root)

        directories = []
        root = self.model.index(self.model.rootPath())
        deep(root, directories)
        self.directories = directories

        for index, directory in enumerate(self.directories):
            if self.model.filePath(directory) == dir:
                self.property_paging['current_index_directories'] = index

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
        self.set_count_foregrounds(self.property_paging['current_index_foreground'], len(self.foregrounds) )
        self.set_count_backgrounds(self.property_paging['current_index_background'], len(self.backgrounds) )

        self.zoom = 2.0

        if len(self.foregrounds) > 0:
            if self.property_paging['current_index_foreground'] < 0:
                self.property_paging['current_index_foreground'] = 0
            elif self.property_paging['current_index_foreground'] >= len(self.foregrounds):
                self.property_paging['current_index_foreground'] = len(self.foregrounds) - 1
            self.listWidget_foregrounds.setCurrentRow(self.property_paging['current_index_foreground'])
            self.listWidget_foregrounds.clicked.emit(self.listWidget_foregrounds.currentIndex())
        else:
            self.property_paging['current_index_foreground'] = 0

        if len(self.backgrounds) > 0:
            if self.property_paging['current_index_background'] < 0:
                self.property_paging['current_index_background'] = 0
            elif self.property_paging['current_index_background'] >= len(self.backgrounds):
                # self.property_paging['current_index_background'] = len(self.backgrounds) - 1
                self.property_paging['current_index_background'] = 0

            self.listWidget_backgrounds.setCurrentRow(self.property_paging['current_index_background'])
            self.listWidget_backgrounds.clicked.emit(self.listWidget_backgrounds.currentIndex())
        else:
            self.property_paging['current_index_background'] = 0

    def refresh_folder(self):
        if len(self.directories) > 0:
            if self.property_paging['current_index_directories'] < 0:
                self.property_paging['current_index_directories'] = 0
            elif self.property_paging['current_index_directories'] >= len(self.directories):
                self.property_paging['current_index_directories'] = len(self.directories) - 1
            index = self.directories[self.property_paging['current_index_directories']]
            self.tree.setCurrentIndex(index)
            self.tree.clicked.emit(self.tree.currentIndex())
        else:
            self.property_paging['current_index_directories'] = 0

    def on_foreground_selected(self, index):
        filename =  self.cur_dir + '/' + index.data()
        if self.current_foreground_path != filename:
            self.property_paging['current_index_foreground'] = index.row()
            self.current_foreground_path = filename
            self.new_foreground()
        self.set_count_foregrounds(self.property_paging['current_index_foreground'], len(self.foregrounds) )
        self.set_count_backgrounds(self.property_paging['current_index_background'], len(self.backgrounds) )

    def on_background_selected(self, index):
        if self.property_folder['for_yolobgs']:
            filename =  self.cur_dir + '/' + index.data()
            self.property_paging['current_index_background'] = index.row()
            self.current_background_path = filename
            self.new_background()
        self.set_count_foregrounds(self.property_paging['current_index_foreground'], len(self.foregrounds) )
        self.set_count_backgrounds(self.property_paging['current_index_background'], len(self.backgrounds) )

    def new_foreground(self):
        image = QImage(self.current_foreground_path)
        if not image.isNull():
            # item_rect.mouseMoveEvent = self.on_item_rect_moved
            self.scene_foreground.mouseMoveEvent = self.on_mouse_moved
            self.scene_foreground.mousePressEvent = self.on_mouse_pressed
            self.scene_foreground.mouseReleaseEvent = self.on_mouse_released

            self.graphicsView_foreground.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
            self.graphicsView_foreground.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
            self.graphicsView_foreground.wheelEvent = self.wheelEvent

            self.graphicsView_background.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
            self.graphicsView_background.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
            self.graphicsView_background.wheelEvent = self.wheelEvent

            self.graphicsView_diffground.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
            self.graphicsView_diffground.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
            self.graphicsView_diffground.wheelEvent = self.wheelEvent

            self.graphicsView_zoomground.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
            self.graphicsView_zoomground.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
            self.graphicsView_zoomground.wheelEvent = self.wheelEvent

            size = image.size()
            width_org = size.width()
            height_org = size.height()

            self.objects_foreground.initialize(self.current_foreground_path.replace('jpg', 'xml'), width_org, height_org, 960, 540, self.fg_bg_converted)

            self.foreground_image = image.scaled(960, 540)

            self.foreground_changed = True
            self.fg_bg_converted = False

    def new_background(self):
        image = QImage(self.current_background_path)
        if not image.isNull():
            self.graphicsView_background.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
            self.graphicsView_background.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

            size = image.size()
            width_org = size.width()
            height_org = size.height()

            self.objects_background.initialize(self.current_background_path.replace('jpg', 'xml'), width_org, height_org, 480, 270, do_not_save_xml=True)
            self.background_image = image.scaled(480, 270)

            self.background_changed = True

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

            try:

                self.scene_foreground.clear()
                item_foreground = QGraphicsPixmapItem(QPixmap.fromImage(self.foreground_image))
                self.scene_foreground.addItem(item_foreground)

                objects = self.objects_foreground.getobjects()
                for obj in objects:
                    item_rect = self.DoubleClickableItem(QtCore.QRectF(obj.x1, obj.y1, obj.x2-obj.x1, obj.y2-obj.y1),
                                                         parent=self,
                                                         set_label=obj.set_label,
                                                         get_label=obj.get_label )
                    item_rect.setPen(obj.prop['line_color'])
                    if obj.selected:
                        item_rect.setBrush(obj.prop['highlight_color'])
                    elif obj.prop['area_fulfil']:
                        item_rect.setBrush(obj.prop['area_color'])

                    # label
                    item_label = QGraphicsTextItem(obj.get_label())
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
            except Exception as e:
                print(e)

            ###### zoom
            try:
                width_display = 201
                height_display = 201

                r_width = (width_display - 1) / 2
                r_height = (height_display - 1) / 2
                r_width, r_height = r_width / self.zoom , r_height / self.zoom

                self.scene_zoomground.clear()
                rect = QtCore.QRect(self.about_mouse['current_x'] - r_width - 1, self.about_mouse['current_y'] - r_height -1, r_width * 2 + 1, r_height * 2 + 1)
                item_zoomground = QGraphicsPixmapItem(QPixmap.fromImage(self.foreground_image.copy(rect).scaled(width_display, height_display)))

                item_vertical = QGraphicsLineItem(101, 0, 101, 201)
                item_vertical.setPen(QColor("Red"))
                item_horizontal = QGraphicsLineItem(0, 101, 201, 101)
                item_horizontal.setPen(QColor("Red"))
                self.scene_zoomground.addItem(item_zoomground)
                self.scene_zoomground.addItem(item_vertical)
                self.scene_zoomground.addItem(item_horizontal)

            except Exception as e:
                print(e)


            if self.property_folder['for_yolobgs'] and len(self.backgrounds) > 0:
                differences = self.objects_foreground.getdifference(self.objects_background, 480, 270)
                try:
                    self.scene_diffground.clear()

                    self.diffground_image = self.background_image.copy()
                    painter = QPainter(self.diffground_image)
                    painter.drawImage(0, 0, self.foreground_image.scaled(480, 270))
                    # painter.drawImage(0, 0, self.background_image.scaled(480, 270))
                    painter.end()

                    item_diffground = QGraphicsPixmapItem(QPixmap.fromImage(self.diffground_image))
                    self.scene_diffground.addItem(item_diffground)

                    objects = differences
                    for obj in objects:
                        item_rect = QGraphicsRectItem(QtCore.QRectF(obj.x1, obj.y1, obj.x2-obj.x1, obj.y2-obj.y1))
                        item_rect.setPen(QColor("red"))

                        self.scene_diffground.addItem(item_rect)
                except:
                    pass
            else:
                self.scene_diffground.clear()

        if self.property_folder['for_yolobgs'] and len(self.backgrounds) > 0:
            if self.background_changed:
                self.background_changed = False

                self.scene_background.clear()
                item_background = QGraphicsPixmapItem(QPixmap.fromImage(self.background_image))
                self.scene_background.addItem(item_background)

                objects = self.objects_background.getobjects(for_background=True)
                for obj in objects:
                    # rect
                    item_rect = QGraphicsRectItem(QtCore.QRectF(obj.x1, obj.y1, obj.x2-obj.x1, obj.y2-obj.y1))
                    item_rect.setPen(obj.prop['line_color'])

                    self.scene_background.addItem(item_rect)
        else:
            self.scene_background.clear()

    def refresh_display_diff(self):
        pass

    def set_text_cursor_pos(self, x, y):
        self.label_cursor_pos.setText('Current(%d, %d)'%(x, y))

    def set_text_cursor_size(self, x, y):
        self.label_cursor_size.setText('Size(%d, %d)'%(x, y))

    def set_text_cursor_start(self, x, y):
        self.label_cursor_start.setText('From(%d, %d)'%(x, y))

    ####################################################
    # mouse & keyboard
    ####################################################
    def on_mouse_moved(self, p):
        x = p.scenePos().x()
        y = p.scenePos().y()

        self.about_mouse['current_x'] = x
        self.about_mouse['current_y'] = y
        _, states = self.objects_foreground.mouse_event(self.about_mouse, x, y)

        self.set_text_cursor_pos(states['x'], states['y'])
        if states['dragging_left'] or states['dragging_right']:
            self.set_text_cursor_start(states['start_x'], states['start_y'])
            self.set_text_cursor_size(states['x']-states['start_x'], states['y']-states['start_y'])
        else:
            self.set_text_cursor_start(0, 0)
            self.set_text_cursor_size(0, 0)

        self.foreground_changed =  True

    def on_mouse_pressed(self, p):
        x = p.scenePos().x()
        y = p.scenePos().y()

        if p.button() == 1: self.about_mouse['pressed_left'] = True
        elif p.button() == 2: self.about_mouse['pressed_right'] = True
        self.foreground_changed, states = self.objects_foreground.mouse_event(self.about_mouse, x, y)
        for combo in self.comboboxes:
            combo.close()
        self.comboboxes.clear()

    def on_mouse_released(self, p):
        if p.button() == 1: self.about_mouse['pressed_left'] = False
        elif p.button() == 2: self.about_mouse['pressed_right'] = False

        self.foreground_changed, states = self.objects_foreground.mouse_event(self.about_mouse, p.scenePos().x(), p.scenePos().y())

    def keyPressEvent(self, p):
        self.ctrl_pressed = p.modifiers() == Qt.ControlModifier
        self.about_mouse['pressed_ctrl'] = self.ctrl_pressed

        key = p.key()
        if Qt.Key_0 <= key <= Qt.Key_9 or Qt.Key_A <= key <= Qt.Key_Z or key == Qt.Key_Space:
            try:
                full_key = ['ctrl' if self.ctrl_pressed else ''][0] + QKeySequence(key).toString().lower()
                self.functions[full_key]()
            except Exception as e:
                pass

        elif key == Qt.Key_Return:
            self.refresh()

    def focusNextPrevChild(self, bool): # tab key
        self.go_to_next_backgground()
        return False

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

        self.functions['z'] = self.go_to_previous_folder
        self.functions['x'] = self.go_to_next_folder

        self.functions['space'] = self.popup_edit_label

        self.functions['h'] = self.hot_function

        self.functions['ctrlz'] = self.undo
        self.functions['ctrla'] = self.select_all

        self.functions['-'] = lambda : sys.stdout.flush()

        for index, string in enumerate(self.property_folder_strings):
            self.functions[str(index+1)] = (lambda s: (lambda: self.toggle_property(s)))(string)

    def go_to_previous_foreground(self):
        self.property_paging['current_index_foreground'] -= 1
        self.refresh_page()

    def go_to_next_foreground(self):
        self.property_paging['current_index_foreground'] += 1
        self.refresh_page()

    def go_to_previous_backgground(self):
        try:
            self.property_paging['current_index_background'] -= 1
            self.refresh_page()
        except:
            pass

    def go_to_next_backgground(self):
        try:
            self.property_paging['current_index_background'] += 1
            self.foreground_changed = True
            self.background_changed = True
            self.refresh_page()
        except:
            pass

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
            self.treeView_directory_tree.clicked.emit(self.treeView_directory_tree.currentIndex())

    def go_to_previous_folder(self):
        self.property_paging['current_index_directories'] -= 1
        self.refresh_folder()

    def go_to_next_folder(self):
        self.property_paging['current_index_directories'] += 1
        self.refresh_folder()

    def set_as_background(self):
        src_jpg = self.current_foreground_path
        if '.bgs' not in src_jpg:
            dst_jpg = src_jpg.replace('.jpg', '.bgs.jpg')
            os.rename(src_jpg, dst_jpg)

            src_xml = src_jpg.replace('.jpg', '.xml')
            dst_xml = dst_jpg.replace('.jpg', '.xml')
            os.rename(src_xml, dst_xml)

            self.fg_bg_converted =True
            self.treeView_directory_tree.clicked.emit(self.treeView_directory_tree.currentIndex())

    def set_as_ng(self):
        self.objects_foreground.set_as_ng()
        self.foreground_changed = True

    def set_as_g(self):
        self.objects_foreground.set_as_g()
        self.foreground_changed = True

    def toggle_property(self, key):
        if self.property_folder[key]:
            try:
                shutil.rmtree(self.cur_dir + '/' + key)
            except Exception as e:
                print(e)
        else:
            try:
                os.makedirs(self.cur_dir + '/' + key)
            except Exception as e:
                print(e)
        self.refresh_property_folder()
        self.refresh_page()

    def popup_edit_label(self):
        objects = self.objects_foreground.getobjects()
        for obj in objects:
            if obj.selected:
                combo = QComboBox(self.graphicsView_foreground)
                combo.setGeometry(obj.x1, obj.y1, 130, 40)
                with open("labels.txt", "r") as f:
                    combo.addItem(obj.get_label())
                    for line in f.readlines():
                        line.replace('\n','', len(line))
                        line.replace('\r','', len(line))
                        line.replace('\t','', len(line))
                        combo.addItem(line)
                combo.currentIndexChanged.connect((lambda obj_: lambda: obj_.set_label(combo.currentText()))(obj))
                combo.show()
                self.comboboxes.append(combo)

    def hot_function(self):
        objects = self.objects_foreground.getobjects()
        for obj in objects:
            if obj.selected:
                self.foreground_changed = True
                if obj.get_label() == 'people':
                    obj.set_label('kids')
                else:
                    obj.set_label('kid')

    def undo(self):
        self.objects_foreground.undo()
        self.foreground_changed = True

    def select_all(self):
        self.objects_foreground.select_all()
        self.foreground_changed = True

    def set_zoom(self, increment):
        if increment:
            self.zoom *= 1.3
        else:
            self.zoom /= 1.3
        self.zoom = min(max(self.zoom, 1.), 6.)
        self.foreground_changed = True

    def wheelEvent(self, QWheelEvent):
        if QWheelEvent.angleDelta().y() > 0:
            self.set_zoom(True)
        else:
            self.set_zoom(False)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    app.exec_()

