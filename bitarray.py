from numbers import Integral
from numpy.lib.stride_tricks import as_strided
import numpy as np

class BitArray():

    def __init__(self, buf, offset, shape, strides):
        self.buf = memoryview(buf)
        self.offset = int(offset)
        self.shape = tuple(shape)
        self.strides = tuple(strides)
        self.ndim = len(shape)

    def __repr__(self):
        return "%s(%s, %s, %s, %s)" % (
            self.__class__.__name__,
                repr(self.buf), self.offset, self.shape, self.strides)

    def __len__(self):
        return np.product(self.shape)

    def __getitem__(self, indices):

        if not isinstance(indices, tuple):
            indices = (indices,)

        idim = len(indices)

        if idim < self.ndim:
            indices = list(indices) + [slice(None)] * (self.ndim - idim)

        offset = self.offset
        shape = []
        strides = []

        for index, length, stride in zip(indices, self.shape, self.strides):
            if isinstance(index, Integral):
                # Simple index
                if index > length - 1 or index < -length:
                    raise IndexError("Index out of range: %d" % index)
                offset += (index % length) * stride
            elif isinstance(index, slice):
                start, stop, step = index.start, index.stop, index.step
                if start is None:
                    start = 0
                elif start < 0:
                    start %= length
                if stop is None or stop == 9223372036854775807:
                    stop = length
                elif stop < 0:
                    stop %= length
                if step is None:
                    step = 1
                offset += (start % length) * stride
                shape.append((stop - start) // step)
                strides.append(step * stride)
            else:
                raise IndexError("Invalid index: %s" % repr(index))

        byte_offset = offset // 8
        bit_offset = offset % 8

        if len(shape) == 0:
            # Retrieve individual bit value.
            return bool(self.buf[byte_offset] & (0x80 >> bit_offset))

        bit_size = sum((d - 1) * s for d, s in zip(shape, strides)) + 1
        byte_size = int(np.ceil(bit_size / 8))

        byte_limit = byte_offset + byte_size

        buf = self.buf[byte_offset:byte_limit]

        return BitArray(buf, bit_offset, shape, strides)

    def as_boolarray(self):
        bools = np.unpackbits(self.buf)[self.offset:]
        return as_strided(bools, shape=self.shape, strides=self.strides)

    def _as_type(self, dtype):
        dtype = '%s%d' % (dtype, self.shape[-1])
        shape = self.shape[:-1]
        bools = self.as_boolarray()
        return np.packbits(bools).view(dtype=dtype).reshape(shape)

    def as_unsigned(self):
        return self._as_type('uint')

    def as_signed(self):
        return self._as_type('int')

    def as_float(self):
        return self._as_type('float')

