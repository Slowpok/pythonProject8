import cv2
import json
import numpy as np
import os
from pathlib import Path
import shutil
from transliterate import translit, get_available_language_codes


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


def find_columns(way, name_of_pic):
    namedir = Path(name_of_pic).stem
    tr_name_of_pic = translit(name_of_pic, language_code='ru', reversed=True)
    tr_namedir = translit(namedir, language_code='ru', reversed=True)

    new_path = way + "\\" + tr_namedir
    os.mkdir(new_path)
    image1 = None

    # try:
    shutil.move(way + "\\" + name_of_pic, new_path + "\\" + tr_name_of_pic)
    image1 = cv2.imread(new_path + "\\" + tr_name_of_pic)
    # except:
    #     print(name_of_pic)
    #     print(new_path + "\\" + tr_name_of_pic)


    if image1 is None:
        return

    image = image1.copy()

    # Convert the image to HSV color space
    hsv_image = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)

    lower = np.array([0, 0, 0])
    upper = np.array([40, 40, 255])

    # Create a mask with cv2.inRange to detect blue colors
    blue_mask = cv2.inRange(hsv_image, lower, upper)

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


    pic = contours[0][1].tolist()

    xmin = pic[0][0]
    xmax = pic[0][0]
    ymin = pic[0][1]
    ymax = pic[0][1]

    for point in range(len(pic)-1):
        x, y = pic[point + 1]
        if x < xmin:
            xmin = x
        if x > xmax:
            xmax = x

        if y < ymin:
            ymin = y
        if y > ymax:
            ymax = y

    dict_column = dict()
    num_col = 1

    for c in range(len(contours)-1, 1, -1):
        col = contours[c]
        namecol = "column" + str(num_col)
        dict_named_col = dict()
        for p in range(len(col)):
            point = col[p][0]
            dict_named_col["point" + str(p+1)] = {"x": str(point[0]), "y": str(point[1])}
            # dict_named_col["x"] = point[0]
            # dict_named_col["y" + str(p+1)] = point[1]
        num_col += 1
        dict_column[namecol] = dict_named_col

    with open(new_path + "\\" + 'data.json', 'w') as outfile:
        json.dump(dict_column, outfile)



# find_tables(r"C:\Users\79118\OneDrive\Документы\perechni")
# rename_dir(r"C:\perechni")
# find_tables(r"C:\perechni")

