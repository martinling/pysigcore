from numbers import Integral
import numpy as np

class BitArray():

    def __init__(self, buf, offset, shape, strides):
        self.buf = np.frombuffer(buf, dtype=np.uint8)
        self.offset = offset
        self.shape = shape
        self.strides = strides
        self.ndim = len(shape)

    def __repr__(self):
        return "%s(%s, %s, %s, %s)" % (
            self.__class__.__name__,
                repr(self.buf), self.offset, self.shape, self.strides)

    def __getitem__(self, index):
        length = self.shape[0]
        stride = self.strides[0]
        if isinstance(index, Integral):
            # Simple index into first dimension.
            if index > length - 1 or index < -length:
                raise IndexError("Index out of range")
            offset = self.offset + (index % length) * stride
            if self.ndim == 1:
                # Retrieve individual bit value.
                byte_offset = offset / 8
                bit_offset = offset % 8
                return bool(self.buf[byte_offset] & (1 << bit_offset))
            else:
                return BitArray(self.buf, offset, self.shape[1:], self.strides[1:])
        elif isinstance(index, slice):
            # Slice into first dimension.
            start, stop, step = index.start, index.stop, index.step
            if start is None:
                start = 0
            elif start < 0:
                start %= length
            if stop is None:
                stop = length
            elif stop < 0:
                stop %= length
            if step is None:
                step = 1
            offset = self.offset + (start % length) * stride
            shape = tuple([(stop - start) // step] + list(self.shape[1:]))
            strides = tuple([step * stride] + list(self.strides[1:]))
            return BitArray(self.buf, offset, shape, strides)
        elif isinstance(index, tuple):
            # Multidimensional slice. Implement by recursion.
            if len(index) == 1:
                return self[index[0]]
            else:
                return self[index[0]][index[1:]]
        else:
            return IndexError("Index is not an integer, slice or tuple of slices.")
