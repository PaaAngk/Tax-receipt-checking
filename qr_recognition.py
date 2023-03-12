import cv2
from pyzbar import pyzbar
from pyzbar.pyzbar import ZBarSymbol
import numpy as np
import streamlit as st
import PyPDF2
import PIL
import torch
import io
from PIL import Image, ImageOps, ImageEnhance
# from kraken import binarization
#https://kdmurray.id.au/post/2022-03-21_decode-qrcodes/

#TODO: parce two qr from yolo in loop 
torch.hub._validate_not_a_forked_repo=lambda a,b,c: True
model = torch.hub.load('ultralytics/yolov5', 'custom', path='./best_6.pt', force_reload=True )

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

#Getting only croped image from yolo
def crop_qr(detection_qr):
  cropped_detection_qr = [x['im'] for x in detection_qr.crop(save=False)]
  
  # Concate image if check exist two qr
  if len(cropped_detection_qr)>1:
    img = concat_image(cropped_detection_qr)
  else:
    img = cropped_detection_qr[0]

  return img

# Concate two image from qr detection else check exist two qr
def concat_image(img):
  images = [PIL.Image.fromarray(x) for x in img]
  min_shape = sorted( [(np.sum(i.size), i.size ) for i in images])[-1][-1]
  imgs_comb = np.hstack([i.resize(min_shape) for i in images])
  return imgs_comb

def sharpen(image, amount=1):
  sharpener = ImageEnhance.Sharpness(image)
  return sharpener.enhance(amount)

def rotate(image, rot=30):
  return image.copy().rotate(rot, expand=1)

def scale_image(image, scalar=None, h=None):
  if scalar == 1:
    return image
  x, y = image.size
  if scalar is None:
    if h is None:
      raise ValueError("give either h or scalar")
    scalar = 1 if h > y else h/y
  return image.resize((int(round(x*scalar)), int(round(y*scalar))))

def modify_image_read_qr(img, print_result):
  formating_decode = None

  for rotate_val in [0, 90, 45]:
    for sharpness in [1, 1.5, 2, 3, 0.5]:
      for scalar in [1, 2, 3, 0.7, 0.3]:

        if sharpness != 1:
          prep_image = rotate(sharpen(img, sharpness), rotate_val)
        else:
          prep_image = rotate(img, rotate_val)

        if scalar != 1:
            prep_image = scale_image(prep_image, scalar=scalar)

        scanned_qr = pyzbar.decode(prep_image, [ZBarSymbol.QRCODE])
        formating_decode = formating_decode_qr_result(scanned_qr, img, print_result)
        
        st.write("sharpe ", sharpness, ' rotate ', rotate_val, ' scale ', scalar)
        st.image(prep_image)
        if formating_decode["data"] is not None:
          st.write("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
          st.image(formating_decode["image"])
          break

      if formating_decode["data"] is not None:
        break
    if formating_decode["data"] is not None:
        break

  return formating_decode

def read_qr(img_row, print_result = True):
  detection_qr = qr_nn_rec(img_row)

  #Getting only croped image from yolo
  img = crop_qr(detection_qr)
  
  img = Image.fromarray(img)
  st.image(img)

  scanned_qr = pyzbar.decode(img, [ZBarSymbol.QRCODE])
  formating_decode = formating_decode_qr_result(scanned_qr, img, print_result)

  if formating_decode["warn"] == "can not read":
    formating_decode = modify_image_read_qr(img, print_result)

  return formating_decode

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
  nn = qr_nn_rec(pil_image)
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


def qr_nn_rec(img):
  model.conf = 0.56
  results = model(img)
  return results






# original = image.copy()
# gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
# blur = cv2.GaussianBlur(gray, (9,9), 0)
# thresh = cv2.threshold(blur, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)[1]

# # Morph close
# kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3,3))
# close = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel, iterations=2)

# return thresh

# # Find contours and filter for QR code
# cnts = cv2.findContours(close, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
# cnts = cnts[0] if len(cnts) == 2 else cnts[1]
# ROI = []
# for c in cnts:
#   peri = cv2.arcLength(c, True)
#   approx = cv2.approxPolyDP(c, 0.02 * peri, True)
#   x,y,w,h = cv2.boundingRect(approx)
#   area = cv2.contourArea(c)
#   ar = w / float(h)
#   if len(approx) == 4 and area > 1000 and (ar > .9 and ar < 1.3):
#     cv2.rectangle(image, (x, y), (x + w, y + h), (36,255,12), 3)
#     ROI = original[y:y+h, x:x+w]
# if len(ROI)>0:
#   return ROI
# else:
#   return image