import argparse
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.colors as colors
import matplotlib.image as mpimg


def dft_naive(x):
    N = len(x)  # number of samples
    X = np.zeros(N, dtype=complex)  # initialize empty array, one value for each sample

    for k in range(N):  # For each output frequency
        for n in range(N):  # For each input sample
            exponent = -2j * np.pi * k * n / N  # Compute exponent
            X[k] += x[n] * np.exp(exponent)  # Multiply and accumulate output value

    return X


# Algorithm implementation inspired by Carleton University implementation:
# https://people.scs.carleton.ca/~maheshwa/courses/5703COMP/16Fall/FFT_Report.pdf
def fft(x):
    N = len(x)

    # Base case for the recursion: if the input size is 1, return the input
    if N <= 1:
        return x

    # Split the input into even and odd indexed parts
    even = fft(x[::2])  # FFT on even-indexed elements
    odd = fft(x[1::2])  # FFT on odd-indexed elements

    # Combine the results from the even and odd FFTs
    T = np.exp(-2j * np.pi * np.arange(N // 2) / N) * odd
    return np.concatenate([even + T, even - T])  # Combine the results (even + T and even - T)


def fft2d(x):
    rows = np.apply_along_axis(fft, 1, x)
    result = np.apply_along_axis(fft, 0, rows)

    return result


def inv_fft(x):
    N = len(x)
    if N <= 1:
        return x
    even = inv_fft(x[::2])
    odd = inv_fft(x[1::2])
    T = np.exp(2j * np.pi * np.arange(N // 2) / N) * odd
    return np.concatenate([even + T, even - T])


def fft_inv2d(x):
    rows = np.apply_along_axis(inv_fft, 1, x)
    result = np.apply_along_axis(inv_fft, 0, rows)

    return result


# Convert image to FFT form and display.
def fast_mode(padded_image):
    fft_result = fft2d(padded_image)
    np_result = np.fft.fft2(padded_image)


def pad_image(image):
    h, w = image.shape[:2]  # Get height and width, ignoring color channels
    print(h)
    print(w)

    # Find the next power of 2 for height and width
    new_h = 2 ** np.ceil(np.log2(h)).astype(int)
    new_w = 2 ** np.ceil(np.log2(w)).astype(int)

    # Calculate padding needed
    pad_height = new_h - h
    pad_width = new_w - w
    print(pad_height)
    print(pad_width)

    # Pad the image with zeros
    if image.ndim == 2:  # Grayscale image
        padded_image = np.pad(image, ((0, pad_height), (0, pad_width)), mode='constant')
    elif image.ndim == 3:  # Color image
        padded_image = np.pad(image, ((0, pad_height), (0, pad_width), (0, 0)), mode='constant')

    return padded_image


def show_image(image):
    # If the image is complex, show its magnitude or real part
    if np.iscomplexobj(image):
        # Show the magnitude spectrum (log scale for better visibility)
        image = np.log(np.abs(image) + 1)  # Adding 1 to avoid log(0)

    plt.imshow(image, cmap='gray' if len(image.shape) == 2 else None)
    plt.axis('off')
    plt.show()


def main():
    # Define arguments
    parser = argparse.ArgumentParser()
    parser.add_argument("-m", "--mode", type=int, choices=[1, 2, 3, 4], default=1)
    parser.add_argument("-i", "--image", type=str, default="moonlanding.png")

    args = parser.parse_args()
    mode = args.mode
    image_path = args.image

    image = mpimg.imread(image_path)
    # padded_image = pad_image(image)
    padded_image = image

    show_image(padded_image)
    result = fft2d(padded_image)
    show_image(result)
    result = fft_inv2d(result)
    show_image(result)


if __name__ == "__main__":
    main()
