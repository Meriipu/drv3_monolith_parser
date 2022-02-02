import sys
import os
#import ctypes
import subprocess
import numpy as np
import cv2 as cv
from PIL import Image
from io import BytesIO

game_x0, game_y0 = 640,0
game_xn, game_yn = 1919,799

game_w,game_h = (game_xn-game_x0)+1, (game_yn-game_y0)+1
mode = cv.COLOR_RGB2BGR

def load_templates():
  def load(path):
    image = Image.open(path).convert("RGB")
    arr = np.asarray(image)
    arr = cv.cvtColor(arr, mode)
    return arr
  pink = load('templates/pink.png')
  gold = load('templates/gold.png')
  plat = load('templates/plat.png')
  silver = load('templates/silver.png')
  empty1 = load('templates/empty1.png')
  empty2 = load('templates/empty2.png')
  empty3 = load('templates/empty3.png')
  return silver, pink, gold, plat, empty1, empty2, empty3

def get_screenshot(example=False):
  if example:
    image = Image.open("example.png").convert("RGB")
    arr = np.asarray(image)
    arr = cv.cvtColor(arr, mode)
    return arr
  elif len(sys.argv) > 1:
    path = sys.argv[1]
    assert os.path.exists(path)
    assert os.path.isfile(path)
    assert path.lower().endswith(".png")
    image = Image.open(path).convert("RGB")
    arr = np.asarray(image)
    arr = cv.cvtColor(arr, mode)
    return arr


  assert type(game_x0) == int
  assert type(game_y0) == int
  assert type(game_w) == int
  assert type(game_h) == int
  coords = f"{game_x0},{game_y0},{game_w},{game_h}"
  # the mouse cursor might still be captured despite the request not to, so moving
  # it to the side of the screen before requesting the screenshot is a good idea.
  cmd = ['scrot', '-a', coords, '-']
  bytes = subprocess.check_output(cmd)

  stream = BytesIO(bytes)
  image = Image.open(stream).convert("RGB")
  stream.close()
  arr = np.asarray(image)
  arr = cv.cvtColor(arr, mode)

  return arr

def find(arr):
  def _find(template, colour, id, thresh = 0.95):
    res = cv.matchTemplate(arr, template, cv.TM_CCOEFF_NORMED)
    loc = np.where(res >= thresh)
    w,h = template.shape[1], template.shape[0]

    # write the image with bounding boxes purely for reference if debugging
    for pt in zip(*loc[::-1]):
      cv.rectangle(copy, (pt[0]+2, pt[1]+2), (pt[0] + w-2, pt[1] + h-2), colour, 2)
      # store the point for later - in the order x,y,id
      points.append((pt[0], pt[1], id))
    cv.imwrite("output/dangan_mindmine_puzzle_res.png", copy)

  silver,pink,gold,plat,empty1,empty2,empty3 = load_templates()
  points = []
  copy = arr.copy()
  # The colour order is GBR
  # the empty cells look a bit varied and also have an issue with the grass on top
  # therefore skip the edges of the template (they should still be detected correctly,
  # but the (correctness-validation/reference-purpose) output image will have those
  # boxes drawn a bit smaller.
  _find(empty1[15:-10, 10:-10,:], (127, 127, 127), 0, thresh=0.75)
  #_find(empty2, (127, 127, 127), 0, thresh=0.85)
  #_find(empty3, (127, 127, 127), 0, thresh=0.85)
  _find(silver, (0, 0, 255), 1)
  _find(pink, (255, 0, 255), 2)
  _find(gold, (0, 255, 255), 3)
  _find(plat, (255, 255, 0), 4)

  startx = min(points, key=lambda x: x[0])[0]
  starty = min(points, key=lambda x: x[1])[1]
  stopx = max(points, key=lambda x: x[0])[0] + silver.shape[1]
  stopy = max(points, key=lambda x: x[1])[1] + silver.shape[0]

  # this should probably be correct but if there is padding not exactly
  w,h = (stopx-startx)+1, (stopy-starty)+1
  num_x = w//silver.shape[1]
  num_y = h//silver.shape[0]

  map = np.zeros((num_y, num_x), dtype=np.uint8)
  block_or_empty = np.ones((num_y, num_x), dtype=np.uint8)
  for ptx,pty,id in points:
    ptx = ptx-startx
    pty = pty-starty
    i = ptx//silver.shape[1]
    j = pty//silver.shape[0]
    map[j,i] = id
    block_or_empty[j,i] = 0

  # Spaces not detected as blocks or empty most likely are correctly identified
  # treasures. Around each such treasure space reserve a 3x3 area that has high
  # priority for clearing (because empty-detection is not perfect, and this
  # reserved space might be obscured by blocks).
  kernel = np.ones((3,3), dtype=np.uint8)
  neighbourhood = cv.dilate(block_or_empty, kernel=kernel)
  # Remove empty spaces from the reserved area for clarity (but it should not
  # have any impact on the implementation).
  block_or_empty = np.where(
    np.logical_or(
      np.logical_and(neighbourhood == 1, map > 0),
      block_or_empty==1
    ),
    1,
    0
  )

  return map, block_or_empty, num_x, num_y, 4 # <-- assume 4 colours

def get_and_perform_action(cat, num_y):
  action = input("next: ") + "\n"
  print(action, file=cat.stdin, flush=True)
  for i in range(num_y):
    print(cat.stdout.readline(), end='')

def main():
  arr = get_screenshot()
  map, mask, num_x, num_y, colours = find(arr)
  s1 = f"{num_x} {num_y} {colours}\n"
  for row in map:
    s1 += "".join(str(x) for x in row) + "\n"
  s1 = s1 + "\n"

  s2 = ""
  for row in mask:
    s2 += "".join(str(x) for x in row) + "\n"
  s2 = s2.replace("1", "T")
  s2 = s2.replace("0", "F")

  s1 = s1 + s2
  print(s1)
  cmd = ["./mindmine.out"]
  PIPE = subprocess.PIPE
  with subprocess.Popen(cmd, stdout=PIPE, stdin=PIPE, universal_newlines=True, bufsize=1) as cat:
    print(s1, file=cat.stdin, flush=True)
    for i in range(1+num_y+1):
      print(cat.stdout.readline(), end='')
    while True:
      should_quit = get_and_perform_action(cat, num_y)
      if should_quit:
        exit()

#  p.stdin.write("poop".encode("utf8"))

if __name__ == '__main__':
  main()