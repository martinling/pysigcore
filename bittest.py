from bitarray import BitArray
import numpy as np

buf = np.arange(10, dtype=np.uint8)
offset = 0
shape = (80,)
strides = (1,)

b = BitArray(buf, offset, shape, strides)

print(b[8])
print(b[8:16])
print(b[:])
