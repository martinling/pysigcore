from numbers import Integral
import numpy as np

class BitArray():

    def __init__(self, buf, offset, shape, strides):
        self.buf = buf
        self.offset = offset
        self.shape = shape
        self.strides = strides
        self.ndim = len(shape)

    def __repr__(self):
        return "%s(%s, %s, %s, %s)" % (
            self.__class__.__name__,
                repr(self.buf), self.offset, self.shape, self.strides)

    def __getitem__(self, index):
        if self.ndim == 1:
            # Single dimension.
            length = self.shape[0]
            stride = self.strides[0]
            if isinstance(index, Integral):
                # Retrieve individual bit value.
                if index > length - 1 or index < -length:
                    raise IndexError("Index out of range")
                offset = self.offset + (index % length) * stride
                byte_offset = offset / 8
                bit_offset = offset % 8
                return bool(self.buf[byte_offset] & (1 << bit_offset))
            elif isinstance(index, slice):
                start, stop, step = index.start, index.stop, index.step
                if start is None:
                    start = 0
                if stop is None:
                    stop = length
                if step is None:
                    step = 1
                start %= length
                stop %= length
                offset = self.offset + (start % length) * stride
                shape = ((stop - start) // step,)
                strides = (step * stride,)
                return BitArray(self.buf, offset, shape, strides)
        raise NotImplemented
