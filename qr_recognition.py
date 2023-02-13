import cv2
from pyzbar import pyzbar
import numpy as np
import streamlit as st
import PyPDF2
import PIL
import torch
import io
# from kraken import binarization

torch.hub._validate_not_a_forked_repo=lambda a,b,c: True
model = torch.hub.load('ultralytics/yolov5', 'custom', path='./best_6.pt', force_reload=True)

def prepare_image(image):
  original = image.copy()
  gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
  blur = cv2.GaussianBlur(gray, (9,9), 0)
  thresh = cv2.threshold(blur, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)[1]

  # Morph close
  kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3,3))
  close = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel, iterations=2)

  # Find contours and filter for QR code
  cnts = cv2.findContours(close, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
  cnts = cnts[0] if len(cnts) == 2 else cnts[1]
  ROI = []
  for c in cnts:
    peri = cv2.arcLength(c, True)
    approx = cv2.approxPolyDP(c, 0.02 * peri, True)
    x,y,w,h = cv2.boundingRect(approx)
    area = cv2.contourArea(c)
    ar = w / float(h)
    if len(approx) == 4 and area > 1000 and (ar > .9 and ar < 1.3):
      cv2.rectangle(image, (x, y), (x + w, y + h), (36,255,12), 3)
      ROI = original[y:y+h, x:x+w]
  if len(ROI)>0:
    return ROI
  else:
    return image


def decode_qr_data(texts):
  try:
    text_value = texts.data.decode('utf-8')
    qr_data_row = text_value.split('?')[-1].split('&')
    qr_data = {}
    for split_row_value in qr_data_row:
      data = split_row_value.split('=')
      qr_data[data[0]] = data[1]
    if qr_data:
      return qr_data
  except IndexError:
    return None

# Print qr info on recognized qr
def plot_qr_image(texts, img):
  try:
    (x, y, w, h) = texts.rect
    dst = img
    cx = int(x + w / 2)
    cy = int(y + h / 2)
    cv2.circle(dst, (cx, cy), 2, (0, 255, 0), 8)
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

# Concate two image from qr detection else check exist two qr
def concat_image(img):
  images = [PIL.Image.fromarray(x) for x in img]
  min_shape = sorted( [(np.sum(i.size), i.size ) for i in images])[-1][-1]
  imgs_comb = np.hstack([i.resize(min_shape) for i in images])
  return imgs_comb


def read_qr(img_row, print_result = True):
  # img = prepare_image(img)

  detection_qr = get_prediction(img_row)
  cropped_detection_qr = [x['im'] for x in detection_qr.crop()]
  if len(cropped_detection_qr)>1:
    img = concat_image(cropped_detection_qr)
    # st.image(img)
  else:
    img = cropped_detection_qr[0]
  st.image
  st.image(img)

  img = img[:, :, ::-1].copy()
  scanned_qr = pyzbar.decode(img)
  
  # st.image(detection_qr.render()[0])
  format_decode = formating_decode_qr_result(scanned_qr, img, print_result)
  if format_decode["warn"] == "can not read":
    for i in range(4):
      img = cv2.rotate(img, cv2.ROTATE_90_CLOCKWISE)
      scanned_qr = pyzbar.decode(img)
      format_decode = formating_decode_qr_result(scanned_qr, img, print_result)
      st.write("Rotate")
      st.image(img)
      if format_decode["data"] is not None:
        st.write("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
        st.image(format_decode["image"])
        break
  return format_decode

# Formate decoded qr data to output dict: success scan, is not check qr and is not read 
def formating_decode_qr_result(scanned_qr, image, print_result = True):
  readed_image = {}
  if scanned_qr:
    for qrs in scanned_qr:
      qr_data = decode_qr_data(qrs)
      if qr_data:
        if print_result:
          image_with_info, warn = plot_qr_image(qrs, image)
          readed_image["image"] = image_with_info
          if warn:
            readed_image["warn"] = warn   
          else:
            readed_image["warn"] = "ok"
          readed_image["data"] = qr_data
        return readed_image
      else:
        readed_image["image"] = image
        readed_image["warn"] = "qr is not correct"   
        readed_image["data"] = None
    return readed_image 
  else:
    readed_image["image"] = image
    readed_image["warn"] = "can not read"
    readed_image["data"] = None
  return readed_image


def run_read_image(img):
  pil_image = PIL.Image.open(img)
  nn = get_prediction(pil_image)
  return read_qr(nn.crop()[0]['im'])

# Return all photo from pdf document with its name
def get_image_from_pdf(document):
  pdfReader = PyPDF2.PdfReader(document)

  count = 0
  images = []
  for pageObj_images_number in range(len(pdfReader.pages)):
    for image_file_object in pdfReader.pages[pageObj_images_number].images:
      images.append({
        "image" : PIL.Image.open(io.BytesIO(image_file_object.data)),
        "name" : image_file_object.name
      })
      count += 1
  return images


def get_prediction(img):
  model.conf = 0.56
  results = model(img)
  return results