#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Aug 14 2019

@author: Quinn Torres & Marcus Wong
"""
## **This script is used to take an MRI image (test), performs an alias + blur mask, 
## and then reconstructs the image using a same convolutional neural network  (CNN)
from PIL import Image
from keras.layers import Input,Conv2D
from keras.layers.normalization import BatchNormalization
from keras.models import Model
import numpy as np
#Import imshow command to see images
from matplotlib.pyplot import imshow
from matplotlib import pyplot as plt
#from keras.models import model_from_json
# Source: https://www.datacamp.com/community/tutorials/reconstructing-brain-images-deep-learning



# uploadingMRIDataV2.py
# In this file we upload 1000 64x64 images from an MRI data set.
# This set was generated by taking the inverse Fourier transform
# of a sampled data set use for the SPIE 2018 Medical Imaging Paper.
# The 64x64 images are subimages of a subsampled 256x256 version of the
# original data set.  If needed, I could go back and get more 
# subimages from the original 512x512 data.

# Reference for input/output:
# https://docs.scipy.org/doc/scipy/reference/tutorial/io.html

# Change from Version 1, we upload the raw mri images and check that images
# are not repeated.

# Import a library for input/output in Python
import scipy.io as sio
# Import axis command to remove axis from images
from matplotlib.pyplot import axis
# import shuffle from random
from random import shuffle, seed
 
# Load MATLAB data into Python size: (1000,64,64)
# Note: make sure that mir_data.mat is in the Python working directory
mri_images_dictionary = sio.loadmat('mri_images.mat')
# We look at the structure of the Python Dictionary
mri_images_dictionary # run in command line to see output or click on the 
# values in the variable explorer

# we extract the MRI data from the dictionary
mri_images = mri_images_dictionary['mri_images']
# this creates a 1000x64x64 numpy array of training data, I would suggest
# that you use 800 for training and 200 for testing to start.

# we look at a sample image containing a part of an MRI
imshow(mri_images[950], cmap = "gray")
# We remove the ticks from the images
# Note that you need to have imported the command or package at the
# beginning
axis("off")


# we randomly suhffle the images to generate the data harcoded for
# 1000 images
seed(23)
ind_list = [i for i in range(1000)]
shuffle(ind_list)
mri_images  = mri_images[ind_list, :,:]
mri_images = mri_images/(mri_images.max())

# Here we are creating a function that has a dataset as an imput and in the loop
# it gathers the specific regions of image data and then takes the inverse fourier transform. 
# This is an alias plus blurring section and takes half the data, which is 2048 pixels

def fourier_operation(user_Images): 
    inverse_Fourier_Image = np.zeros(user_Images.shape[0:3]) # Create an array of zeros to be filled in
    for j in range(0,user_Images.shape[0]): # for loop going from 0 to number of images in dataset
        Fourier = np.fft.fft2(user_Images[j,:,:]) #Apply fourier transform
        Fourier_shift = np.fft.fftshift(Fourier) #shifting the zero and low frequency to center of image
        
        # Masking the middle and every other line
        matrix_of_ones = np.zeros((64,64),dtype = np.float64) #creating a matrix of zeros
        matrix_of_ones[:,28:35] = 1 # This sets the middle 7 columns to zero
        
        # Two loops, first loop converts first half of every other to 1, second loop seconf half
        for k in range(0, 24, 2):
            matrix_of_ones[:,k] = 1
            
        for l in range(40,62, 2):
            matrix_of_ones[:,l] = 1
       
       
        # This converts our mask matrix into an image
        masking_image = Image.fromarray(matrix_of_ones) 
        # This displays the image so we can see it 
        imshow(masking_image, cmap = "gray")
        # Set title of thee image
        plt.title('Aliased + Blur Mask')

    
        
        
        # Taking the element wise matrix multiplication of our fourier image and our mask matrix
        accelerated_data = np.multiply(Fourier_shift,matrix_of_ones) 
        
        inverse_Fourier = np.fft.ifftshift(accelerated_data) #Applying the inverse fourier on the mask
        inverse_Fourier = np.fft.ifft2(inverse_Fourier) #Reshifting the zero frequency back to corner of image
        inverse_Fourier = abs(inverse_Fourier) # Taking the absolute value of the fourier
        inverse_Fourier_Image[j,:,:] = Image.fromarray(inverse_Fourier) #Recovered image from the array
        
    one_check = np.count_nonzero(matrix_of_ones == 1) # Check how many pixels of value one are there
    print("The number of pixels of value one are", one_check )   #Print the number of pixels = 1         
    return inverse_Fourier_Image

blurred_MRI_Image = fourier_operation(mri_images) # Calls our function on the mri dataset
blurred_MRI_Image = blurred_MRI_Image/(blurred_MRI_Image.max()) #Normalizes the new dataset

original_image_MRI = mri_images[950,:,:] # Calls the 950th image of the original dataset and assigns it to a variable
blurred_version_image_MRI = blurred_MRI_Image[950,:,:] # Calls the 950th image of the new datset after the mask is applied and assigns it to a variable


# This is to plot our original image and our new masked image side by side
fig = plt.figure()   
ax1 = fig.add_subplot(121)
ax2 = fig.add_subplot(122)  
ax1.imshow(original_image_MRI, cmap = "gray") #makes colormap greyscale
ax2.imshow(blurred_version_image_MRI, cmap = "gray")
ax1.title.set_text("Original Image")
ax2.title.set_text("Aliased + Blur Image")

# Here we are taking the root mean squared error of the original image and the new masked image
err = np.sum((original_image_MRI.astype("float") - blurred_version_image_MRI.astype("float")) ** 2)
err /= float(original_image_MRI.shape[0] * original_image_MRI.shape[1])
rmse = np.sqrt(err) 
print("The RMSE of the new image vs the original image is ", rmse)
# This section we are seperating our data into training and testing sets
X_train = blurred_MRI_Image[0:800, :,:] # Takes the first 800 images and assigns it to train set
X_train = X_train.reshape(800,64,64,1) # Reshapes the train set to be used in our network

X_test =  blurred_MRI_Image[800:1000, :,:] # Takes the last 200 images and puts it into test set 
X_test = X_test.reshape(200,64,64,1) # Reshapes the test set to be used in our network

Y_train = mri_images[0:800,:,:] # Takes the first 800 images and assigns it to y train set
Y_train = Y_train.reshape(800,64,64,1) # Reshapes the train set to be used in our network

Y_test = mri_images[800:1000,:,:] # Takes the last 200 images and puts it into y test set 
Y_test = Y_test.reshape(200,64,64,1) # Reshapes the test set to be used in our network

# Belwo prints the number of train and test examples and the shape of each x,y train/test set
print("------------------------------")
print ("number of training examples = " + str(X_train.shape[0]))
print ("number of test examples = " + str(X_test.shape[0]))
print ("X_train shape: " + str(X_train.shape))
print ("Y_train shape: " + str(Y_train.shape))
print ("X_test shape: " + str(X_test.shape))
print ("Y_test shape: " + str(Y_test.shape))
print("------------------------------")


# A same convolutional neural network is established here. We have a total of 2 same convolutional layers
# that maintain a feature map of 64 features. 
# Batch Normalization is applied as a regularization method to prevent overfitting and to normalize the mapping 
# in between the input and output features.

def sameCNN(input_img = Input(shape = (64,64,1))):

    conv_One_Block_Down = Conv2D(64, (3, 3), strides = (1,1), activation='relu', padding='same')(input_img)
    conv_One_Block_Down = BatchNormalization()(conv_One_Block_Down)
    
    conv_One_Block_Down = Conv2D(64, (3, 3), strides = (1,1),activation='relu', padding='same')(conv_One_Block_Down)
    conv_One_Block_Down = BatchNormalization()(conv_One_Block_Down)
    
    last_Layer = Conv2D(1, (3, 3), activation='sigmoid', padding='same')( conv_One_Block_Down) 
 
    
    return last_Layer 

#

# After the creation of our model, we compile the model along with an Adam optimizer and using the 
# mean squared error as our loss function measurement.
input_img = Input(shape = (64,64,1))
sameCNN = Model(input_img, sameCNN(input_img))


sameCNN.compile(optimizer = "adam", loss = "mean_squared_error")
    
sameCNN.summary() # Displays a nice breakdwon of our model


# We train the model with the training set of 800 images that was established earlier in the code with
# 50 epochs and a batch size of 16.

sameCNN_train = sameCNN.fit(X_train, Y_train, epochs=50, batch_size=16)

# This evaluates our test set based on the model trained by our training set and prints out the loss value

preds = sameCNN.evaluate(x = X_test, y = Y_test) # Evaluate CNN Model on test set

#Prints loss value
print()
print ("Loss = " + str(preds))

# We are plotting the loss value after every epoch. Y is the loss value in log scale and X is the number of epochs
loss = sameCNN_train.history['loss'] #Extracts the loss values of the CNN model and assigns it to loss
loss = np.sqrt(loss) #Taking the root mean squared error loss and we will plot this on a graph
epochs = range(50) # assigns spochs to an arrray of numbers from 0-49
plt.figure() # Creates a figure to be used
plt.plot(epochs, loss, 'ro--', label='Mean Squared Error Loss')
# This code is used to plot our figue with the appropiate axes labels, title, legend
plt.title('Training Performance (Same CNN C)')
plt.xlabel('Number of Epochs')
plt.ylabel('Root Mean Squared Error Loss')
plt.yscale('log')
plt.legend()
plt.show()


# Here we are Displaying all three images side by side. The Original, aliased & blurred, and reconstructed image
pred = sameCNN.predict(X_test) # Evaluates the model on test set and assigns to pred
pred = pred/(pred.max()) # Normalizes the pred array by dividing by its max

# This code creates our plot for the images
fig = plt.figure(figsize=(10,10)) # Creates a figure size
ax1 = fig.add_subplot(1,3,1) # Assign position of first figure
ax1.imshow(mri_images[950], cmap='gray') # Displaying the 950th original image
plt.axis('off')
ax2 = fig.add_subplot(1,3,2)
ax2.imshow(X_test[150, ..., 0], cmap = "gray") # Diplaying the 150th image from the X_test set
plt.axis('off')
ax3 = fig.add_subplot(1,3,3)
ax3.imshow(pred[150, ..., 0], cmap='gray') # Displaying our reconstructed image of the 150th image
plt.axis('off')  
ax1.title.set_text('Original Image')
ax2.title.set_text('Aliased + Blur Image')
ax3.title.set_text('Reconstructed Image')

# This finds the mean squared error between the original image and the reconstructed image
err = np.sum((mri_images[950].astype("float") - pred[150, ..., 0].astype("float")) ** 2) #
err /= float(mri_images.shape[1] * mri_images.shape[1]) # Divide error by number of pixels
err = np.sqrt(err) # Take square root or error 
print("The RMSE of the new image vs the original image is ", err)



