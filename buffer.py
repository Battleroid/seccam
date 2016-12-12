class RingBuffer:
    def __init__(self, size):
        self.data = []
        self.size = int(size)
        self.ptr = 0

    def append(self, elem):
        if len(self.data) == self.size:
            self.data[self.ptr] = elem
        else:
            self.data.append(elem)
        self.ptr = (self.ptr + 1) % self.size

    def get(self):
        return self.data[self.ptr:] + self.data[:self.ptr]
