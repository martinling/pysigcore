from threading import Thread
import ipdb
import sys

class Context():

	def __init__(self):
		pass

class Flowgraph():

	def __init__(self, context):
		self.context = context
		self.blocks = []
		self.signals = []

class Block():

	def __init__(self, flowgraph):
		self.flowgraph = flowgraph
		self.flowgraph.blocks.append(self)
		self.inputs = {}
		self.outputs = {}

	def init(self):
		pass

	def process(self, input, signal, packet):
		pass

class Input():

	def __init__(self, block, signal_type, name):
		self.block = block
		self.signal_type = signal_type
		self.name = name
		self.block.inputs[name] = self
		self.source = None

	def connect(self, signal):
		if not isinstance(signal, self.signal_type):
			raise InvalidArgument("Input does not support this signal type.")
		self.source = signal
		signal.destinations.add(self)

	@property
	def connected(self):
		return (self.source is not None)

class Signal():

	def __init__(self, block, name):
		self.block = block
		self.name = name
		self.block.outputs[name] = self
		self.destinations = set()

	@property
	def connected(self):
		return len(self.destinations)

	def emit(self, packet):
		for input in self.destinations:
			input.block.process(input, self, packet)

class RawLogic(Signal):
	pass

class Analog(Signal):
	pass

class Packet():

	def __init__(self, signal):
		self.signal = signal

class StreamStartPacket(Packet):
	pass

class StreamEndPacket(Packet):
	pass

class RawLogicDataPacket(Packet):

	def __init__(self, signal, values):
		super().__init__(signal)
		self.values = values

class AnalogDataPacket(Packet):

	def __init__(self, signal, values):
		super().__init__(signal)
		self.values = values

class Data():

	def __init__(self, buf, unitsize):
		if buf.nbytes % unitsize != 0:
			raise InvalidArgument(
				"Buffer provided is not a multiple of unit size")
		self.buf = buf
		self.count = buf.nbytes / unitsize
		self.bits = Bits(self)

class Bits():

	def __init__(self, parent, slice=None):
		self.parent = parent
		self.slice = None

	def __getitem__(self, slice):
		return Bits(self, slice)

class Stream():
	
	def __init__(self, block):
		self.block = block
		self.mappings = []

	def add_mapping(self, mapping):
		self.mappings.append(mapping)

	def start(self):
		self.count = 0
		for mapping in self.mappings:
			signal = mapping.signal
			signal.emit(StreamStartPacket(signal))

	def emit(self, *args):
		for mapping in self.mappings:
			if mapping.signal.connected:
				mapping.emit(*args)

	def end(self):
		for mapping in self.mappings:
			signal = mapping.signal
			signal.emit(StreamEndPacket(signal))

class DataStream(Stream):

	def __init__(self, block, unitsize):
		super().__init__(block)
		self.unitsize = unitsize
		self.bits = BitStream(self)

	def emit(self, buf):
		data = Data(buf, self.unitsize)
		super().emit(data)
		self.count += data.count

class BitStream(Stream):

	def __init__(self, parent, slice=slice(0, None, None)):
		super().__init__(parent.block)
		self.parent = parent
		self.slice = slice

	def __getitem__(self, slice):
		return BitStream(self, slice)

class Mapping():

	def __init__(self, signal):
		self.signal = signal

class RawLogicMapping(Mapping):

	def __init__(self, signal, bitstream):
		super().__init__(signal)
		self.bitstream = bitstream

	def emit(self, data):
		signal = self.signal
		signal.emit(RawLogicDataPacket(signal, data.bits[self.bitstream.slice]))

class AnalogMapping(Mapping):

	def __init__(self, signal, bitstream):
		super().__init__(signal)
		self.bitstream = bitstream

	def emit(self, data):
		signal = self.signal
		signal.emit(AnalogDataPacket(signal, data.bits[self.bitstream.slice]))

class ThreadedBlock(Block):

	def __init__(self, flowgraph):
		super().__init__(flowgraph)
		self.thread = Thread(target=self._run)
		self.running = False

	def start(self):
		self.running = True
		self.thread.start()

	def _run(self):
		try:
			self.run()
		except Exception:
			e, m, tb = sys.exc_info()
			ipdb.post_mortem(tb)
		self.running = False

	def run(self):
		pass

	def stop(self):
		self.running = False
		self.thread.join()
