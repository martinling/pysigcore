from bitarray import BitArray
import numpy as np

buf = np.arange(10, dtype=np.uint8)
offset = 0
shape = (10,8)
strides = (8,1)

b = BitArray(buf, offset, shape, strides)

print(b[1,0])
print(b[0,8:16])
print(b[:])
