import argparse
import numpy as np
import matplotlib.pyplot as plt
from matplotlib import image as mpimg
from matplotlib.colors import LogNorm
import matplotlib.image as mpim
import time


# Pad image with 0s such that the dimensions of the image are powers of 2
def pad_image(image):
    h, w = image.shape[:2]

    # Find the next power of 2 for height and width
    new_h = 2 ** np.ceil(np.log2(h)).astype(int)
    new_w = 2 ** np.ceil(np.log2(w)).astype(int)

    # Calculate padding needed
    pad_height = new_h - h
    pad_width = new_w - w

    # Pad the image with zeros
    if image.ndim == 2:  # Grayscale image
        padded_image = np.pad(image, ((0, pad_height), (0, pad_width)), mode='constant')
    elif image.ndim == 3:  # Color image
        padded_image = np.pad(image, ((0, pad_height), (0, pad_width), (0, 0)), mode='constant')

    return padded_image


# Naive implementation of DFT
def dft_naive(x):
    N = len(x)  # number of samples
    X = np.zeros(N, dtype=complex)  # initialize empty array, one value for each sample

    for k in range(N):  # For each output frequency
        for n in range(N):  # For each input sample
            exponent = -2j * np.pi * k * n / N  # Compute exponent
            X[k] += x[n] * np.exp(exponent)  # Multiply and accumulate output value

    return X


# FFT
# Algorithm implementation inspired by Carleton University:
# https://people.scs.carleton.ca/~maheshwa/courses/5703COMP/16Fall/FFT_Report.pdf
def fft(x):
    n = len(x)

    if n <= 1:
        return x

    w_n = np.exp(-2j * np.pi / n)
    w = 1

    y_even = fft(x[::2])  # recursively call fft on even-index elements
    y_odd = fft(x[1::2])  # on odd-index elements

    y = np.zeros(n, dtype=complex)  # initialize values
    for j in range(n // 2):
        y[j] = y_even[j] + w * y_odd[j]
        y[j + n // 2] = y_even[j] - w * y_odd[j]
        w = w * w_n

    return y


def fft_inv(x):
    n = len(x)

    # Base case for the recursion: if the input size is 1, return the input
    if n <= 1:
        return x

    w_n = np.exp(2j * np.pi / n)
    w = 1

    y_even = fft_inv(x[::2])
    y_odd = fft_inv(x[1::2])

    y = np.zeros(n, dtype=complex)
    for j in range(n // 2):
        y[j] = y_even[j] + w * y_odd[j]
        y[j + n // 2] = y_even[j] - w * y_odd[j]
        w = w * w_n

    return y / n


# Get the fft of 2d image
def fft2d(image):
    transformed_rows = np.array([fft(row) for row in image])
    transformed_cols = np.array([fft(col) for col in transformed_rows.T]).T

    return transformed_cols


# Get the inverse fft of a 2d image
def fft2d_inv(image):
    transformed_rows = np.array([fft_inv(row) for row in image])
    transformed_cols = np.array([fft_inv(col) for col in transformed_rows.T]).T
    return transformed_cols


def fast_mode(padded_image):
    # One by two subplot of original image
    plt.subplot(1, 2, 1)
    plt.title("Original")
    plt.imshow(padded_image, cmap="gray")
    plt.axis("off")

    # One by two subplot of 2d fft
    plt.subplot(1, 2, 2)
    plt.title("fft")

    # My fft on original image
    fft2d_result = fft2d(padded_image)
    magnitude = np.abs(fft2d_result)
    plt.imshow(magnitude, norm=LogNorm(), cmap="gray")
    plt.axis("off")

    plt.show()


def denoise(padded_image):
    return


def main():
    # Define arguments
    parser = argparse.ArgumentParser()
    parser.add_argument("-m", "--mode", type=int, choices=[1, 2, 3, 4], default=1)
    parser.add_argument("-i", "--image", type=str, default="moonlanding.png")

    args = parser.parse_args()
    mode = args.mode
    image_path = args.image

    original_image = mpimg.imread(image_path)
    padded_image = pad_image(original_image)

    denoise(padded_image)
    #fast_mode(padded_image)


if __name__ == "__main__":
    main()
