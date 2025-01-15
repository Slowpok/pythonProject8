import cv2
import json
import numpy as np
import os
from pathlib import Path
import shutil
from transliterate import translit, get_available_language_codes
import xml.etree.ElementTree as ET
from PIL import Image
import glob
import sys
import struct

def relocate_data(old_path, new_path):
    for root, dirs, files in os.walk(old_path):
        for dir in dirs:
            relocate_data(root + "\\" + dir, new_path)

        list_files_bmp = glob.glob('*' + '.bmp', root_dir=old_path)
        list_files_xml = glob.glob('*' + '.xml', root_dir=old_path)

        for file_bmp in list_files_bmp:
            if file_bmp.endswith('.bmp') and file_bmp != "blue_mask.bmp":
                try:
                    shutil.copy2(old_path + "\\" + file_bmp, new_path + "\\" + file_bmp)
                except:
                    print("bmp: ", file_bmp)


        for file_xml in list_files_xml:
            if file_xml.endswith('.xml'):
                filename = os.path.basename(os.path.dirname(old_path + "\\" + file_xml)) + ".xml"
                try:
                    os.rename(old_path + "\\" + file_xml, old_path + "\\" + filename)
                    shutil.copy2(old_path + "\\" + filename, new_path + "\\" + filename)
                except:
                    print("xml: ", file_xml)
                    print(filename)
                    print(old_path)




def del_json(global_way):
    for root, dirs, files in os.walk(global_way):
        for dir in dirs:
            del_json(root + "\\" + dir)

        for file in files:
            if file.endswith('.json'):
                print(file)
                os.remove(global_way + "\\" + file)


def get_bmp_depth(way):
    bpp = 0
    # Read first 100 bytes
    with open(way, 'rb') as f:
        BMP = f.read(100)

    if BMP[0:2] == b'BM':

        # Get BITMAPINFOHEADER size - https://en.wikipedia.org/wiki/BMP_file_format
        BITMAPINFOHEADERSIZE = struct.unpack('<i', BMP[14:18])[0]
        okSizes = [40, 52, 56, 108, 124]
        if BITMAPINFOHEADERSIZE in okSizes:
        # Get bits per pixel
            bpp = struct.unpack('<H', BMP[28:30])[0]
    return bpp

def mass_mk_dir(global_way):
    for root, dirs, files in os.walk(global_way):
        for dir in dirs:
            find_tables(root + "\\" + dir)

        for file in files:
            if file.endswith('.pdf'):
                namedir = Path(file).stem
                tr_namedir = translit(namedir, language_code='ru', reversed=True)
                new_path = root + "/" + tr_namedir
                os.mkdir(new_path)
                shutil.move(root + "/" + file, new_path + "/" + file)

def rename_dir(global_way):
    for fn in os.listdir(global_way):
        if not os.path.isdir(os.path.join(global_way, fn)):
            continue  # Not a directory
        tr_fn = translit(fn, language_code='ru', reversed=True)

        os.rename(os.path.join(global_way, fn),
                  os.path.join(global_way, tr_fn))

def find_tables(global_way):
    for root, dirs, files in os.walk(global_way):
        for dir in dirs:
            find_tables(dir)

        for file in files:
            if file.endswith('.bmp'):
                find_columns(root, file)

def convert_bmp_to_jpeg(global_way):

    ext = '.bmp'
    new = '.jpeg'

    for root, dirs, files in os.walk(global_way):

        for dir in dirs:
            convert_bmp_to_jpeg(global_way + "\\" + dir)

        # Creates a list of all the files with the given extension in the current folder:
        list_files = glob.glob('*' + ext, root_dir=global_way)

        # Converts the images:
        for file in list_files:
            try:
                namefile = global_way + "\\" + file
                im = Image.open(namefile)
                im.save(namefile.replace(ext, new))
                os.remove(namefile)
            except:
                print(namefile)


def find_columns(way, name_of_pic, make_dir=False):
    namedir = Path(name_of_pic).stem

    if make_dir:
        tr_name_of_pic = translit(name_of_pic, language_code='ru', reversed=True)
        tr_namedir = translit(namedir, language_code='ru', reversed=True)
        new_path = way + "\\" + tr_namedir
        os.mkdir(new_path)
    else:
        new_path = way
        tr_name_of_pic = name_of_pic

    image1 = None
    depth = get_bmp_depth(way + "\\" + name_of_pic)

    try:
        if make_dir:
            shutil.move(way + "\\" + name_of_pic, new_path + "\\" + tr_name_of_pic)
        image1 = cv2.imread(new_path + "\\" + tr_name_of_pic)
    except:
         print(name_of_pic)
         print(new_path + "\\" + tr_name_of_pic)



    if image1 is None:
        return


    # preparing image
    image = image1.copy()

    # Convert the image to HSV color space
    hsv_image = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)

    lower = np.array([0, 0, 0])
    upper = np.array([40, 40, 255])

    # Create a mask with cv2.inRange to detect blue colors
    blue_mask = cv2.inRange(hsv_image, lower, upper)
    cv2.imwrite(new_path + "\\" + "blue_mask.bmp", blue_mask)
    ret, bin_img = cv2.threshold(blue_mask, 127, 255, cv2.THRESH_BINARY)

     # show the binary image on the newly created image window
    # cv2.imshow('Intermediate',bin_img)

    # extracting the contours from the given binary image
    contours, hierarchy = cv2.findContours(bin_img, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

    # это надо было чтоб посмотреть, что ж там внутри-то
    # with open('example.txt', 'w') as file:
    #     arr = []
    #     for t in contours:
    #         arr.append(str(t))
    #         print(str(t))
    #     stringnp = '\n'.join(arr)
    #
    #     file.write(stringnp)

    # #  Это надо было для того, чтоб визуализировать, как накладываются контуры
    # yy = np.array(hierarchy)
    # # # отображаем контуры поверх изображения
    # cv2.drawContours(image2, contours, -1, (0, 0, 255), 3, cv2.LINE_AA, yy, 1)
    #
    '''в contours лежит следующеее - первый кортеж - всегда контуры самого изображения
     второй кортеж - очертания самой таблицы. т к  контур не по одному пикселю, 
     то одну точку описывают условные 4 координаты - два массива по 2 элемента.
     там 8 массивов по 2 элемента, соответственно, 4 точки
     третий и далее - это контуры колонок. идут задом наперед'''


    pic = contours[0].tolist()

    xmin_bol = pic[0][0][0]
    xmax_bol = pic[0][0][0]
    ymin_bol = pic[0][0][1]
    ymax_bol = pic[0][0][1]

    for point in range(len(pic)-1):
        x, y = pic[point + 1][0]
        if x < xmin_bol:
            xmin_bol = x
        if x > xmax_bol:
            xmax_bol = x

        if y < ymin_bol:
            ymin_bol = y
        if y > ymax_bol:
            ymax_bol = y

    # create data xml - first step
    root = ET.Element("annotation")
    root.set("verified", "yes")

    # создаём вложенные элементы
    ex_folder = ET.SubElement(root, 'folder')
    ex_folder.text = "Scan_documents"

    ex_filename = ET.SubElement(root, 'filename')
    ex_filename.text = tr_name_of_pic

    ex_path = ET.SubElement(root, 'path')
    ex_path.text = new_path

    ex_source = ET.SubElement(root, 'source')

    ex_database = ET.SubElement(ex_source, 'database')
    ex_database.text = "Unknown"

    ex_size = ET.SubElement(root, 'size')
    ex_width = ET.SubElement(ex_size, 'width')
    ex_width.text = str(xmax_bol + 1)
    ex_height = ET.SubElement(ex_size, 'height')
    ex_height.text = str(ymax_bol + 1)
    ex_depth = ET.SubElement(ex_size, 'depth')
    ex_depth.text = str(depth)

    ex_segmented = ET.SubElement(root, 'segmented')
    ex_segmented.text = "0"

    # for json file:
    # dict_column = dict()
    # num_col = 1
    # for c in range(len(contours)-1, 1, -1):
    #     col = contours[c]
    #     namecol = "column" + str(num_col)
    #     dict_named_col = dict()
    #     for p in range(len(col)):
    #         point = col[p][0]
    #         dict_named_col["point" + str(p+1)] = {"x": str(point[0]), "y": str(point[1])}
    #         # dict_named_col["x"] = point[0]
    #         # dict_named_col["y" + str(p+1)] = point[1]
    #     num_col += 1
    #     dict_column[namecol] = dict_named_col

    for c in range(len(contours)-1, 1, -1):
        col = contours[c]
        if len(col) != 4:
            print("missed column")
            print(new_path)
            print(tr_name_of_pic)
            continue

        ex_object = ET.SubElement(root, 'object')
        ex_name = ET.SubElement(ex_object, 'name')
        ex_name.text = "column"
        ex_pose = ET.SubElement(ex_object, 'pose')
        ex_pose.text = "Unspecified"
        ex_truncated = ET.SubElement(ex_object, 'truncated')
        ex_truncated.text = "0"
        ex_difficult = ET.SubElement(ex_object, 'difficult')
        ex_difficult.text = "0"

        p_1 = col[0][0]
        p_4 = col[2][0]

        xmin = p_1[0]
        xmax = p_4[0]
        ymin = p_1[1]
        ymax = p_4[1]

        ex_bndbox = ET.SubElement(ex_object, 'bndbox')
        ex_xmin = ET.SubElement(ex_bndbox, 'xmin')
        ex_xmin.text = str(xmin)
        ex_ymin = ET.SubElement(ex_bndbox, 'ymin')
        ex_ymin.text = str(ymin)
        ex_xmax = ET.SubElement(ex_bndbox, 'xmax')
        ex_xmax.text = str(xmax)
        ex_ymax = ET.SubElement(ex_bndbox, 'ymax')
        ex_ymax.text = str(ymax)

    # вывод xml-документа в файл
    tr = ET.ElementTree(root)
    tr.write(new_path + "\\" + "data.xml")

    # with open(new_path + "\\" + 'data.json', 'w') as outfile:
    #     json.dump(dict_column, outfile)


# mass_mk_dir(r"C:\Users\79118\OneDrive\Документы\Перечни")
# find_tables(r"C:\Users\79118\OneDrive\Документы\perechni")
# rename_dir(r"C:\perechni")
# find_tables(r"C:\perechnicopy")
# del_json(r"C:\perechnicopy")
# convert_bmp_to_jpeg(r"C:\perechnicopy")

relocate_data(r"C:\perechnicopy", r"C:\perechni_new")
