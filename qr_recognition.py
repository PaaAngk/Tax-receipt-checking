import cv2
from pyzbar import pyzbar
from PIL import Image
import PIL
import numpy as np
import streamlit as st
import PyPDF2
import PIL
import io
from PIL import Image, ImageEnhance


def decode_qr_data(texts):
  qr_data_list = []
  try:
    text_value = texts.data.decode('utf-8')
    qr_data_row = text_value.split('?')[-1].split('&')
    qr_data = {}
    for split_row_value in qr_data_row:
      data = split_row_value.split('=')
      qr_data[data[0]] = data[1]
    if qr_data:
      qr_data_list.append(qr_data)
  except IndexError:
    return None
  return qr_data_list

def plot_qr_image(texts, img):
    try:
        (x, y, w, h) = texts.rect
        dst = img
        cx = int(x + w / 2)
        cy = int(y + h / 2)
        cv2.circle(dst, (cx, cy), 2, (0, 255, 0), 8)
        print('center coords', cx, cy)
        coordinate = (cx, cy)
        cv2.putText(dst, 'QRcode_location' + str(coordinate), (20, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
        cv2.rectangle(dst, (x, y), (x + w, y + h), (0, 255, 255), 2)
        cv2.line(dst, texts.polygon[0], texts.polygon[1], (255, 0, 0), 2)
        cv2.line(dst, texts.polygon[1], texts.polygon[2], (255, 0, 0), 2)
        cv2.line(dst, texts.polygon[2], texts.polygon[3], (255, 0, 0), 2)
        cv2.line(dst, texts.polygon[3], texts.polygon[0], (255, 0, 0), 2)
        txt = '(' + texts.type + ')  ' + texts.data.decode('utf-8')
        cv2.putText(dst, txt, (x - 300, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 50, 255), 2)
        return dst, None
    except Exception:
        return dst, "can not plot qr info"


def read_qr(img1, print_result = True):
  text = pyzbar.decode(img1)
  img = np.array(img1) 
  img = img[:, :, ::-1].copy()
  readed_image = {}
  if text:
    for texts in text:
      qr_data = decode_qr_data(texts)
      if qr_data:
        if print_result:
          image, warn = plot_qr_image(texts, img)
          readed_image["image"] = image
          if warn:
            readed_image["warn"] = warn   
          readed_image["data"] = qr_data
        return readed_image
      else:
        readed_image["image"] = img1
        readed_image["warn"] = "qr is not correct"   
        readed_image["data"] = None
    return readed_image 
  else:
    readed_image["image"] = img1
    readed_image["warn"] = "can not read"
    readed_image["data"] = None
    return readed_image

def run_read_image(img):
  pil_image = PIL.Image.open(img)
  return read_qr(pil_image)


def get_image_from_pdf(document):
  # pdfFileObj = open('exDoc.pdf', 'rb')
  pdfReader = PyPDF2.PdfFileReader(document)

  count = 0
  images = []
  for pageObj_images_number in range(pdfReader.numPages):
    for image_file_object in pdfReader.getPage(pageObj_images_number).images:
      # enhancer = ImageEnhance.Sharpness(PIL.Image.open(io.BytesIO(image_file_object.data)))
      # im_output = enhancer.enhance(1.5)
      images.append( PIL.Image.open(io.BytesIO(image_file_object.data)) )
      count += 1
  return images
