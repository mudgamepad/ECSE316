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


def remove_padding(padded_image, original_shape):
    return padded_image[:original_shape[0], :original_shape[1]]


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


def ifft(x):
    n = len(x)

    # Base case for the recursion: if the input size is 1, return the input
    if n <= 1:
        return x

    w_n = np.exp(2j * np.pi / n)
    w = 1

    y_even = ifft(x[::2])
    y_odd = ifft(x[1::2])

    y = np.zeros(n, dtype=complex)
    for j in range(n // 2):
        y[j] = y_even[j] + w * y_odd[j]
        y[j + n // 2] = y_even[j] - w * y_odd[j]
        w = w * w_n

    return y / n


# Get the fft of 2d image
def fft2(image):
    transformed_rows = np.array([fft(row) for row in image])
    transformed_cols = np.array([fft(col) for col in transformed_rows.T]).T
    return transformed_cols


# Get the inverse fft of a 2d image
def ifft2(image):
    transformed_rows = np.array([ifft(row) for row in image])
    transformed_cols = np.array([ifft(col) for col in transformed_rows.T]).T
    return transformed_cols / image.size


def fast_mode(padded_image):
    # One by two subplot of original image
    plt.subplot(1, 3, 1)
    plt.title("Original")
    plt.imshow(padded_image, cmap="gray")
    plt.axis("off")

    # One by two subplot of 2d fft
    plt.subplot(1, 3, 2)
    plt.title("fft2d")

    # My fft on original image
    fft2d_result = fft2(padded_image)
    magnitude = np.abs(fft2d_result)
    plt.imshow(magnitude, norm=LogNorm(), cmap="gray")
    plt.axis("off")

    plt.subplot(1, 3, 3)
    plt.title("np.fft.fft2")
    np_result = np.fft.fft2(padded_image)
    np_magnitude = np.abs(np_result)
    plt.imshow(np_magnitude, norm=LogNorm(), cmap="gray")
    plt.axis("off")

    plt.show()


def denoise(padded_image, frequency_cutoff=390):
    # Take fft of image
    fft_result = fft2(padded_image)
    fft_result = np.fft.fftshift(fft_result)

    width, height = padded_image.shape
    center_x, center_y = width // 2, height // 2
    y, x = np.ogrid[:width, :height]
    distance_from_center = np.sqrt((x - center_x) ** 2 + (y - center_y) ** 2)
    mask = distance_from_center <= frequency_cutoff

    denoised_fft = fft_result * mask
    denoised_fft = np.fft.fftshift(denoised_fft)

    # Take inverse fft
    denoised_image = ifft2(denoised_fft)

    # Plot the original and denoised images
    plt.subplot(1, 2, 1)
    plt.title("Original Image")
    plt.imshow(padded_image, cmap="gray")
    plt.axis("off")

    plt.subplot(1, 2, 2)
    plt.title(f"De-noised Image {frequency_cutoff}")
    magnitude = np.abs(denoised_image)
    plt.imshow(magnitude, cmap="gray")
    plt.axis("off")

    plt.show()
    # TODO print ratio of cut/total frequencies


def compress():
    # Take fft of image
    # Set some fourier coefficients to 0

    # 1) threshold the coefficients’ magnitude and take only the largest percentile of them
    # 2) keep all the coefficients of very low frequencies as well as a fraction of
    # the largest coefficients from higher frequencies to also filter the image at the same time
    # 3) Any other schemes?

    # take inverse fft
    # 2 by 3 subplot: 6 compression levels (including original image)
    # Print number of non zeros that are in each of the 6 images
    return


def plot():
    # Produce plots that summarize the runtime complexity of your algorithms. Your code should print in the
    # command line the means and variances of the runtime of your algorithms versus
    # the problem size

    # From report: Create 2D arrays of random elements of various
    # sizes (sizes must be square and powers of 2). Start from 25 and move
    # up to 210 or up to the size that your computer can handle. Gather
    # data for the plot by re-running the experiment at least 10 times
    # to obtain an average runtime for each problem size and a standard
    # deviation. On your plot you must have problem size on the x-axis
    # and runtime in seconds on the y-axis. You can plot two lines; one
    # for the naive method and one for the FFT. Plot your mean runtimes
    # for each method and include error bars proportional to the standard
    # deviation that represent a confidence interval defined by you.
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
    

if __name__ == "__main__":
    main()
