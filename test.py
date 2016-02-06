from classes import *
from time import sleep
import numpy as np

class TestSource(ThreadedBlock):
    """
    Test source that generates 8 logic and 2 analog signals, packed in 32 bit
    units as follows:

        Bits 0-7: logic channels D0-D7
        Bits 8-15: analog channel A0 (8-bit)
        Bits 16-31: analog channel A1 (16-bit)
    """

    def __init__(self, flowgraph):
        ThreadedBlock.__init__(self, flowgraph)

        # Set up outputs: 8 logic, 2 analog.
        self.logic_outputs = [
            RawLogic(self, "D%d" % i) for i in range(8)]
        self.analog_outputs = [
            Analog(self, "A%d" % i) for i in range(2)]

    def run(self):

        # Create a data stream.
        stream = DataStream(self, unitsize=4)

        # Add mappings for individual channels.
        for i, output in enumerate(self.logic_outputs):
            stream.add_mapping(
                RawLogicMapping(output, stream.bits[i]))
        stream.add_mapping(
            AnalogMapping(self.outputs["A0"], stream.bits[8:16],
                AnalogEncoding(8, 1/128)))
        stream.add_mapping(
            AnalogMapping(self.outputs["A1"], stream.bits[16:32],
                AnalogEncoding(16, 1/32768)))

        # Number of samples to be sent at a time.
        block_samples = 100000

        # Numpy record dtype used to pack sample data.
        dtype = [('Logic', 'u1'), ('A0', 'i1'), ('A1', 'i2')]

        # Start the stream.
        stream.start()

        while self.running:
            # Allocate space for sample data.
            samples = np.recarray((block_samples,), dtype)

            # Populate sample data.
            samplenumbers = np.arange(stream.count, stream.count + block_samples,
                dtype=np.uint)
            samples['Logic'] = samplenumbers & 0xFF
            samples['A0'] = np.sin(samplenumbers/1000.0) * 128.0
            samples['A1'] = np.cos(samplenumbers/500.0) * 32768.0

            # Emit packed sample data to stream.
            print("Source sending samples %d - %d" % (stream.count,
                stream.count + block_samples))
            stream.emit(samples)

        # End the stream.
        stream.end()

class Threshold(Block):
    """
    Simple analog->digital threshold block.

    Output is 1 when input is positive.
    """

    def __init__(self, flowgraph):
        Block.__init__(self, flowgraph)
        self.input = Input(self, Analog, "In")
        self.output = RawLogic(self, "Out")

    def process(self, input, signal, packet):

        print("threshold packet")

        # Do nothing if output is not connected.
        if not self.output.connected:
            return

        if isinstance(packet, AnalogDataPacket):
            logic_samples = packet.values > 0
            logic_packet = RawLogic(logic_samples)
            print("Threshold sending data")
            self.output.emit(logic_packet)

class PrintSink(Block):

    def __init__(self, flowgraph):
        Block.__init__(self, flowgraph)
        Input(self, Signal, "In")

    def process(self, input, signal, packet):
        print(input, signal, packet)

# Set up flowgraph.
context = Context()
flowgraph = Flowgraph(context)
source = TestSource(flowgraph)
threshold = Threshold(flowgraph)
sink = PrintSink(flowgraph)
threshold.inputs["In"].connect(source.outputs["A1"])
sink.inputs["In"].connect(threshold.outputs["Out"])
#sink.inputs["In"].connect(source.outputs["A1"])

# Run for 1s.
source.start()
sleep(1)
source.stop()
