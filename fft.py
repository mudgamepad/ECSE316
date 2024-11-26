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

# Algorithm implementation inspired by Carleton University implementation: https://people.scs.carleton.ca/~maheshwa/courses/5703COMP/16Fall/FFT_Report.pdf
def fft(x, threshold=16):
    N = len(x)  # number of samples

    if N <= threshold:
        return dft_naive(x)  # TODO experiment with threshold for performance

    if N % 2 != 0:
        raise ValueError("The input size must be a power of 2.")

    Wn = np.exp(2j * np.pi / N)
    X_even = fft(x[::2])  # recursively compute fft for even-index elements
    X_odd = fft(x[1::2])  # for odd-index elements

    X = np.zeros(N, dtype=complex)
    w = 1

    for i in range (N // 2):
        X[i] = X_even[i] + w * X_odd[i]  # compute first half of fft result
        X[i + N // 2] = X_even[i] - w * X_odd[i]  # compute second half of fft result
        w *= Wn

    return X

def fft2d(x):
    rows = np.apply_along_axis(fft, 1, x)
    result = np.apply_along_axis(fft, 0, rows)

    return result

def fft2d_(x):
    rows = np.apply_along_axis(np.fft.fft2(), 1, x)
    result = np.apply_along_axis(np.fft.fft2(), 0, rows)

    return result

# Convert image to FFT form and display.
def fast_mode(padded_image):
    fft_result = fft2d_(padded_image)

    # Shift the zero frequency component to the center of the spectrum
    fft_shifted = np.fft.fftshift(fft_result)

    # Calculate the magnitude and apply log scaling
    magnitude = np.abs(fft_shifted)
    log_magnitude = np.log1p(magnitude)  # Use log1p for better handling of zero values

    # Plot original image and FFT result (log-scaled)
    fig, axs = plt.subplots(1, 2, figsize=(12, 6))

    axs[0].imshow(padded_image, cmap='gray')
    axs[0].set_title('Original Image')
    axs[0].axis('off')

    im = axs[1].imshow(log_magnitude, cmap='gray', norm=colors.LogNorm())
    axs[1].set_title('FFT (Log Scale)')
    axs[1].axis('off')

    plt.colorbar(im, ax=axs[1])
    plt.show()


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
    plt.figure(figsize=(6, 6))
    plt.imshow(image, cmap='gray' if len(image.shape) == 2 else None)
    plt.title('Padded Image')
    plt.axis('off')  # Hide axis
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
    padded_image = pad_image(image)

    fast_mode(padded_image)

if __name__ == "__main__":
    main()