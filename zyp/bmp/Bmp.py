import sys
import binascii
import math


class BmpFileHeader:
    def __init__(self):
        self.bfType = i_to_bytes(0, 2)  # 0x4d42 对应BM
        self.bfSize = i_to_bytes(0, 4)  # file size
        self.bfReserved1 = i_to_bytes(0, 2)
        self.bfReserved2 = i_to_bytes(0, 2)
        self.bfOffBits = i_to_bytes(0, 4)  # header info offset


class BmpStructHeader:
    def __init__(self):
        self.biSize = i_to_bytes(0, 4)  # bmpheader size
        self.biWidth = i_to_bytes(0, 4)
        self.biHeight = i_to_bytes(0, 4)
        self.biPlanes = i_to_bytes(0, 2)  # default 1
        self.biBitCount = i_to_bytes(0, 2)  # one pixel occupy how many bits
        self.biCompression = i_to_bytes(0, 4)
        self.biSizeImage = i_to_bytes(0, 4)
        self.biXPelsPerMeter = i_to_bytes(0, 4)
        self.biYPelsPerMeter = i_to_bytes(0, 4)
        self.biClrUsed = i_to_bytes(0, 4)
        self.biClrImportant = i_to_bytes(0, 4)


class Bmp(BmpFileHeader, BmpStructHeader):
    def __init__(self):
        BmpFileHeader.__init__(self)
        BmpStructHeader.__init__(self)
        self.__bitSize = 0  # pixels size
        self.bits = []  # pixel array

    @property
    def width(self):
        return bytes_to_i(self.biWidth)

    @property
    def height(self):
        return bytes_to_i(self.biHeight)

    # unit is byte
    @property
    def bit_count(self):
        return bytes_to_i(self.biBitCount) // 8

    @property
    def width_step(self):
        return self.bit_count * self.width

    # resolve a bmp file
    def parse(self, file_name):
        file = open(file_name, 'rb')
        # BmpFileHeader
        self.bfType = file.read(2)
        self.bfSize = file.read(4)
        self.bfReserved1 = file.read(2)
        self.bfReserved2 = file.read(2)
        self.bfOffBits = file.read(4)
        # BmpStructHeader
        self.biSize = file.read(4)
        self.biWidth = file.read(4)
        self.biHeight = file.read(4)
        self.biPlanes = file.read(2)
        self.biBitCount = file.read(2)
        # pixel size
        self.__bitSize = self.width * self.height * self.bit_count
        self.biCompression = file.read(4)
        self.biSizeImage = file.read(4)
        self.biXPelsPerMeter = file.read(4)
        self.biYPelsPerMeter = file.read(4)
        self.biClrUsed = file.read(4)
        self.biClrImportant = file.read(4)
        #  load pixel info
        count = 0
        while count < self.__bitSize:
            bit_count = 0
            while bit_count < (int.from_bytes(self.biBitCount, 'little') // 8):
                self.bits.append(file.read(1))
                bit_count += 1
            count += 1
        file.close()

    def generate(self, file_name):
        file = open(file_name, 'wb+')
        # reconstruct File Header
        file.write(self.bfType)
        file.write(self.bfSize)
        file.write(self.bfReserved1)
        file.write(self.bfReserved2)
        file.write(self.bfOffBits)
        # reconstruct bmp header
        file.write(self.biSize)
        file.write(self.biWidth)
        file.write(self.biHeight)
        file.write(self.biPlanes)
        file.write(self.biBitCount)
        file.write(self.biCompression)
        file.write(self.biSizeImage)
        file.write(self.biXPelsPerMeter)
        file.write(self.biYPelsPerMeter)
        file.write(self.biClrUsed)
        file.write(self.biClrImportant)
        # reconstruct pixels
        for bit in self.bits:
            file.write(bit)
        file.close()

    def resize(self, width, height):
        self.__nni(width, height)

    # nearest_neighbor Interpolation
    def __nni(self, width, height):
        # width must be Multiple of four
        if width % 4 != 0:
            width -= width % 4
        w_ratio = (self.height / height)
        h_ratio = (self.width / height)
        # new pixels array
        new_bits = [b''] * height * width * self.bit_count
        for row in range(0, height):
            for col in range(0, width):
                for channel in range(0, self.bit_count):
                    old_r = round((row + 0.5) * w_ratio - 0.5)
                    old_c = round((col + 0.5) * h_ratio - 0.5)
                    new_index = row * width * self.bit_count + col * self.bit_count + channel
                    old_index = old_r * self.width_step + old_c * self.bit_count + channel
                    new_bits[new_index] = self.bits[old_index]
        self.bits = new_bits
        # reset header info
        self.bfSize = i_to_bytes(height * width * self.bit_count + 54, 4)
        self.biSizeImage = i_to_bytes(len(new_bits), 4)
        self.biWidth = i_to_bytes(width, 4)
        self.biHeight = i_to_bytes(height, 4)

    # put bmp graying
    def graying(self):
        new_bits = [b''] * self.width * self.height * self.bit_count
        for i in range(0, self.height):
            for j in range(0, self.width):
                s_index = i * self.width_step + j * self.bit_count
                target_index = i * self.width_step + j * self.bit_count
                r = int.from_bytes(self.bits[s_index + 2], 'little')
                g = int.from_bytes(self.bits[s_index + 1], 'little')
                b = int.from_bytes(self.bits[s_index], 'little')
                gray = (r * 30 + g * 59 + b * 11) / 100
                new_bits[target_index] = int(gray).to_bytes(1, 'little')
                new_bits[target_index + 1] = int(gray).to_bytes(1, 'little')
                new_bits[target_index + 2] = int(gray).to_bytes(1, 'little')
        self.bits = new_bits

    def rotate(self):
        self.__rotate(90)

    """
    reference: http://blog.csdn.net/liyuan02/article/details/6750828
    attention: in the loop, the x in real bmp is represent y, the y same too.
    """
    def __rotate(self, degree):
        cos_degree = math.cos(math.radians(degree))
        sin_degree = math.sin(math.radians(degree))
        h = math.ceil(self.height * cos_degree
                      + self.width * sin_degree)
        w = math.ceil(self.height * sin_degree
                      + self.width * cos_degree)
        h = abs(h)
        w = abs(w)
        if w % 4 != 0:
            w -= w % 4
        dx = -0.5 * w * cos_degree - 0.5 * h * sin_degree + 0.5 * self.width
        dy = 0.5 * w * sin_degree - 0.5 * h * cos_degree + 0.5 * self.height
        new_bits = [b''] * w * h * 3
        for x in range(0, h):
            for y in range(0, w):
                x0 = y * cos_degree + x * sin_degree + dx
                y0 = -y * sin_degree + x * cos_degree + dy
                src_index = round(y0) * self.width_step + round(x0) * self.bit_count
                dst_index = x * w * self.bit_count + y * self.bit_count
                if len(self.bits) - self.bit_count > src_index >= 0:
                    new_bits[dst_index + 2] = self.bits[src_index + 2]
                    new_bits[dst_index + 1] = self.bits[src_index + 1]
                    new_bits[dst_index] = self.bits[src_index]
                else:
                    new_bits[dst_index + 2] = i_to_bytes(255, 1)
                    new_bits[dst_index + 1] = i_to_bytes(255, 1)
                    new_bits[dst_index] = i_to_bytes(255, 1)
        self.bits = new_bits
        self.biWidth = i_to_bytes(w, 4)
        self.biHeight = i_to_bytes(h, 4)


def i_to_bytes(number, length, byteorder='little'):
    return number.to_bytes(length, byteorder)


def bytes_to_i(mbytes, byteorder='little'):
    return int.from_bytes(mbytes, byteorder)


if __name__ == "__main__":
    bmp = Bmp()
    print(i_to_bytes(1,4))
    bmp.parse('../res/test.bmp')
    # bmp.resize(8,8)
    # bmp.graying()
    bmp.rotate()
    bmp.generate('../res/result.bmp')
