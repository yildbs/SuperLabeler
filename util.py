import xml.etree.ElementTree as ET
import math
from bs4 import BeautifulSoup

def make_xml_annotation(image_width, image_height):
    xml_annotation = ET.Element("annotation")
    xml_source = ET.SubElement(xml_annotation, 'source')
    ET.SubElement(xml_source, 'database').text = 'Unknown'
    xml_size = ET.SubElement(xml_annotation, 'size')
    ET.SubElement(xml_size, 'width').text = str(image_width)
    ET.SubElement(xml_size, 'height').text = str(image_height)
    ET.SubElement(xml_annotation, 'segmented').text = '0'
    return xml_annotation


def add_object_element(parent, name, xmin, ymin, xmax, ymax):
    xml_object = ET.SubElement(parent, 'object')
    ET.SubElement(xml_object, 'name').text = name
    xml_bndbox = ET.SubElement(xml_object, 'bndbox')
    ET.SubElement(xml_bndbox, 'xmin').text = str(xmin)
    ET.SubElement(xml_bndbox, 'ymin').text = str(ymin)
    ET.SubElement(xml_bndbox, 'xmax').text = str(xmax)
    ET.SubElement(xml_bndbox, 'ymax').text = str(ymax)


def indent(elem, level=0):
    i = "\n" + level *"  "
    if len(elem):
        if not elem.text or not elem.text.strip():
            elem.text = i + "  "
        if not elem.tail or not elem.tail.strip():
            elem.tail = i
        for elem in elem:
            indent(elem, level +1)
        if not elem.tail or not elem.tail.strip():
            elem.tail = i
    else:
        if level and (not elem.tail or not elem.tail.strip()):
            elem.tail = i


def read_xml(xmlpath):
    fileread = False
    changed = False
    objects = []
    try:
        soup = BeautifulSoup(open(xmlpath, 'r', encoding='utf-8').read(), "lxml")
        fileread = True
        for idx, object in enumerate(soup.findAll('object')):
            name = object.find('name').text
            name = name.replace('\n', '', len(name)).replace('\r', '', len(name))

            x1_ = int(float(object.bndbox.xmin.text))
            y1_ = int(float(object.bndbox.ymin.text))
            x2_ = int(float(object.bndbox.xmax.text))
            y2_ = int(float(object.bndbox.ymax.text))

            x1 = min(x1_, x2_)
            y1 = min(y1_, y2_)
            x2 = max(x1_, x2_)
            y2 = max(y1_, y2_)

            therearesameobject = False
            for exist in objects:
                exist_name = exist[0]
                exist_x1 = exist[1]
                exist_y1 = exist[2]
                exist_x2 = exist[3]
                exist_y2 = exist[4]

                isdifferent = False
                if exist_name.replace('_NG', '') != name.replace('_NG', ''):
                    isdifferent = True
                if exist_x1 != x1:
                    isdifferent = True
                if exist_y1 != y1:
                    isdifferent = True
                if exist_x2 != x2:
                    isdifferent = True
                if exist_y2 != y2:
                    isdifferent = True
                if not isdifferent:
                    therearesameobject = True

            if not therearesameobject or len(objects) == 0:
                objects.append([name, x1, y1, x2, y2])

            if therearesameobject:
                changed = True

    except Exception as e:
        print(e)
        pass
    return objects, fileread, changed


def save_xml(foregroundimagexmlpath, objects, image_width, image_height ):
    xml_annotation = make_xml_annotation(image_width, image_height)
    for index, object in enumerate(objects):
        label = object.get_label()
        if label == '@DRAG':
            continue
        x1 = int(object.x1)
        y1 = int(object.y1)
        x2 = int(object.x2)
        y2 = int(object.y2)

        add_object_element(xml_annotation, label, str(x1), str(y1), str(x2), str(y2))
    indent(xml_annotation)
    xml_tree = ET.ElementTree(xml_annotation)
    xml_tree.write(foregroundimagexmlpath)


def get_distance(p1, p2):
    ax, ay = p1
    bx, by = p2
    return math.sqrt(pow(bx-ax, 2) + pow(by-ay, 2))

