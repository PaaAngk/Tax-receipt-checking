import cv2
from pyzbar import pyzbar
from pyzbar.pyzbar import ZBarSymbol
import numpy as np
import streamlit as st
import PyPDF2
import torch
import io
from PIL import Image, ImageEnhance, ImageSequence, ImageOps
from time import time

#TODO: parce two qr from yolo in loop 
torch.hub._validate_not_a_forked_repo=lambda a,b,c: True
model = torch.hub.load('ultralytics/yolov5', 'custom', path='./model/best_6.pt', force_reload=True )

detector = cv2.wechat_qrcode_WeChatQRCode(
  "./model/detect.prototxt",
  "./model/detect.caffemodel",
  "./model/sr.prototxt",
  "./model/sr.caffemodel")

def decode_qr_data(texts):

  print(texts)
  try:
    if hasattr(texts, 'data'):
      text_value = texts.data.decode('utf-8')
    else:
      text_value = texts
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
def plot_qr_image(texts, PILImg):
  img = cv2.cvtColor(np.array(PILImg), cv2.COLOR_RGB2BGR)
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
    return Image.fromarray(dst), None
  except Exception:
    return Image.fromarray(dst), "can not plot qr info"

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
  # return ImageOps.expand(image,border=int(scalar*20),fill='black')

def find_coeffs(pa, pb):
  matrix = []
  for p1, p2 in zip(pa, pb):
    matrix.append([p1[0], p1[1], 1, 0, 0, 0, -p2[0]*p1[0], -p2[0]*p1[1]])
    matrix.append([0, 0, 0, p1[0], p1[1], 1, -p2[1]*p1[0], -p2[1]*p1[1]])
  A = np.matrix(matrix, dtype=np.float64)
  B = np.array(pb).reshape(8)
  res = np.dot(np.linalg.inv(A.T * A) * A.T, B)
  return np.array(res).reshape(8)

def perspective(img, position = 'top'):
  width, height = img.size
  stock= [(0, 0), (width, 0), (width, height), (0, height)]
  if position == 'top':
    img = img.transform((width, height), Image.PERSPECTIVE, find_coeffs(stock, [(-20, -20), (width+20, -20), (width, height), (0, height)]),Image.BICUBIC)
  if position == 'bottom':
    img = img.transform((width, height), Image.PERSPECTIVE, find_coeffs(stock, [(0, 0), (width, 0), (width+20, height+20), (-20, height+20)]),Image.BICUBIC)
  if position == 'left':
    img = img.transform((width, height), Image.PERSPECTIVE, find_coeffs(stock, [(-20, -20), (width, 0), (width, height), (-20, height+20)]),Image.BICUBIC)
  if position == 'right':
    img = img.transform((width, height), Image.PERSPECTIVE, find_coeffs(stock, [(0, 0), (width+20, -20), (width+20, height+20), (0, height)]),Image.BICUBIC)
  return img

def modify_image_and_read_qr(img, print_result):
  formating_decode = None

  for rotate_val in [0, 90, 45]:
    for perspective_val in ['', 'top', 'bottom', 'left', 'right']:
      for sharpness in [1, 2, 0.5]:
        for scalar in [1, 3, 0.7]:

          
          if sharpness != 1:
            prep_image = perspective(sharpen(img, sharpness), perspective_val)
          else:
            prep_image = perspective(img, perspective_val)

          if scalar != 1:
            prep_image = scale_image(prep_image, scalar=scalar)
          prep_image = rotate(prep_image, rotate_val)

          scanned_qr = pyzbar.decode(prep_image, [ZBarSymbol.QRCODE])
          st.write(scanned_qr)
          formating_decode = formating_decode_qr_result(scanned_qr, img, print_result)
          
          st.write("sharpe ", sharpness, ' perspective ', perspective_val, ' scale ', scalar, ' rotate ', rotate_val)
          st.image(prep_image)
          if formating_decode["data"] is not None:
            st.write("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
            st.image(formating_decode["image"])
            break

        if formating_decode["data"] is not None:
          break
      if formating_decode["data"] is not None:
        break
    if formating_decode["data"] is not None:
      break

  return formating_decode

# Concate two image from qr detection else check exist two qr
def concat_image(img):
  images = [Image.fromarray(x) for x in img]
  min_shape = sorted( [(np.sum(i.size), i.size ) for i in images])[-1][-1]
  imgs_comb = np.hstack([i.resize(min_shape) for i in images])
  return imgs_comb

#Getting only croped image from yolo
def crop_qr(detection_qr):
  cropped_detection_qr = [x['im'] for x in detection_qr.crop(save=False)]
  # Concate image if check exist two qr
  if len(cropped_detection_qr)>1:
    img = concat_image(cropped_detection_qr)
  else:
    img = cropped_detection_qr[0]
  return img

def read_by_openCV(img, print_result):
  res, _ = detector.detectAndDecode(cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR))
  st.write(res)
  return formating_decode_qr_result([res[0]] if res else None, img, print_result)

def read_qr(img_row, print_result = True):
  detection_qr = nn_recognition_qrs(img_row)
  # st.write(detection_qr.pandas().xyxy[0].iloc[1])

  #Getting array of detected QRs by NN 
  scanned_QRs = [ImageOps.grayscale(Image.fromarray(x['im']))for x in detection_qr.crop(save=False)]
  
  formatingReadData = []

  for img in scanned_QRs:
    st.image(img)

    t1 = time()
    scanned_qr = pyzbar.decode(img, [ZBarSymbol.QRCODE])
    t2 = time()
    st.write('Time Taken : ', round(1000*(t2 - t1),1), ' ms')
    # st.write(scanned_qr)

    formating_decode = formating_decode_qr_result(scanned_qr, img, print_result)

    if formating_decode["status"] == "can not read":
      # formating_decode = modify_image_and_read_qr(img, print_result)
      formating_decode = read_by_openCV(img, print_result)
    
    formatingReadData.append(formating_decode)

  return formatingReadData

# Formate decoded qr data to output dict: success scan, is not check qr and is not read 
def formating_decode_qr_result(scanned_qr, image, print_result = True):
  st.write(scanned_qr)
  readed_image = {}
  if scanned_qr:
    for qrs in scanned_qr:
      qr_data = decode_qr_data(qrs)
      if qr_data:
        if print_result:
          # image_with_info, warn = plot_qr_image(qrs, image)
          # readed_image["image_with_info"] = image_with_info
          readed_image["image"] = image
          readed_image["status"] = "ok"
          readed_image["data"] = qr_data
          readed_image["raw_data"] = qrs
          readed_image["status"] = 1
        return readed_image
      else:
        readed_image["image"] = image
        readed_image["status"] = "qr is not correct"   
        readed_image["data"] = None
    return readed_image 
  else:
    readed_image["image"] = image
    readed_image["status"] = "can not read"
    readed_image["data"] = None
  return readed_image

def run_read_image(img):
  pil_image = Image.open(img)
  nn = nn_recognition_qrs(pil_image)
  return read_qr(nn.crop()[0]['im'])

def nn_recognition_qrs(img):
  start_time = time()
  model.conf = 0.7
  results = model(img)

  st.write("NN read time: ", (time() - start_time))
  return results

# ------------------ Document proccesing ---------------------#

# Return all photo from pdf document with its name
def get_images_from_pdf(document):
  pdfReader = PyPDF2.PdfReader(document)

  count = 0
  images = []
  for pageObj_images_number in range(len(pdfReader.pages)):
    for image_file_object in pdfReader.pages[pageObj_images_number].images:
      images.append({
        "image" : Image.open(io.BytesIO(image_file_object.data)),
        "name" : image_file_object.name
      }) 
      count += 1
  st.write(images)  
  return images

def get_images_from_tif(document):
  im = Image.open(document)

  images = []
  for image in ImageSequence.Iterator(im):
    img = Image.fromarray(np.array(image))
    if img.mode == 'RGBA':
      images.append({
        "image" : img
      }) 
  st.write(images)
  return images




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