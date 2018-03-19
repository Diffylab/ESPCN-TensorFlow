from __future__ import division
import numpy as np
import os
import os.path
import time
from glob import glob
import tensorflow as tf
import scipy.misc
from scipy.misc import imresize
from subpixel import PS

from random import shuffle
import imageio
import cv2

def save_ycbcr_img(Y, Cb, Cr, scale, path):
    # upscale Cb and Cr
    Cb = Cb.repeat(scale, axis = 0).repeat(scale, axis = 1)
    Cr = Cr.repeat(scale, axis = 0).repeat(scale, axis = 1)
    # stack and save
    img_ycbcr = np.dstack((Y, Cr, Cb))
    #print("shape:",Y.shape,Cb.shape,Cr.shape,img_ycbcr.shape)
    img_rgb = cv2.cvtColor(img_ycbcr, cv2.COLOR_YCrCb2RGB)
    imageio.imwrite(path, img_rgb)
    return 0

def doresize(x, shape):
    x = np.copy(x).astype(np.uint8)
    y = imresize(x, shape, interp='bicubic')
    return y

def calc_PSNR(img1, img2):
    mse = np.mean( (img1 - img2) ** 2 )
    if mse == 0:
        return 100
    return 20 * np.log10(255.0 / np.sqrt(mse))

def load_image(image_path, mode = "RGB"):
    if mode == "RGB":
        return scipy.misc.imread(image_path, mode = "RGB")
    else: 
        return scipy.misc.imread(image_path, mode = "YCbCr")
    
def PS_1dim(I, r):
    r = int(r)
    O = np.zeros((I.shape[0]*r, I.shape[1]*r, int(I.shape[2]/(r*r))))
    for x in range(O.shape[0]):
        for y in range(O.shape[1]):
            for c in range(O.shape[2]):
                c += 1
                a = np.floor(x/r).astype("int")
                b = np.floor(y/r).astype("int")
                d = c*r*(y%r) + c*(x%r)
                #print a, b, d
                O[x, y, c-1] = I[a, b, d]
    return O

def create_imdb(config):
    path = os.path.join(config.train.hr_path, config.dataset)
    img_list = sorted(glob(os.path.join(config.train.hr_path, config.dataset, "*.png")))
    print("loading from..",path, "num images:", len(img_list))
    start_time = time.time()
    imdb = [scipy.misc.imread(filename, mode = config.mode) for filename in img_list]
    print("%d images loaded! setting took: %4.4fs" % (len(imdb), time.time() - start_time))
    shuffle(imdb)
    return imdb

def get_batch(imdb, start, batch_size, patch_size, scale, augmentation = False):
    img_batch = np.zeros([batch_size, patch_size, patch_size, 3])
    img_batch_LR = np.zeros([batch_size, int(patch_size/scale), int(patch_size/scale), 3])
    for i in range(batch_size):
        img_index = 0
        H = 0
        W = 0
        img_index = (start+i)%len(imdb)
        H = np.random.randint(imdb[img_index].shape[0]-patch_size)
        W = np.random.randint(imdb[img_index].shape[1]-patch_size)
        #print("img index:",img_index,", img shape:",imdb[img_index].shape[0],'',imdb[img_index].shape[1],"H,W:",[H,W])
        #print("img index:",img_index,", img shape:",imdb[img_index].shape,"H,W:",[H,W])
        img_batch[i,:,:,:] = imdb[img_index][H:H+patch_size, W:W+patch_size,:]
        img_batch_LR[i,:,:,:] = imresize(imdb[img_index][H:H+patch_size, W:W+patch_size,:], [int(patch_size/scale), int(patch_size/scale)])
    return img_batch, img_batch_LR