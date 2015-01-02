#!/usr/bin/env python3

"""
# get file info
    avprobe -of json -show_format -show_streams test.avi
# show pixel formats
    avconv -pix_fmts
"""

from __future__ import division
import subprocess as sp
import os
import json
import numpy as np
import matplotlib.pyplot as plt

CONV_BIN   = "avconv"
PROBE_BIN  = "avprobe"
CONFIDENCE = 0.5

class FrameConfig(object):
    def __init__(self, color, width, height):
        self.color  = color
        self.width  = width
        self.height = height

class Frame(object):
    def __init__(self, data, index, frame_config):
        self.data  = data
        self.index = index
        self.frame_config = frame_config
        self.hash = None

    def __str__(self):
        return "Frame #{}".format(self.index)

    def compare(self, other_frame):
        raise NotImplementedError("Please Implement this method")

    def display(self):
        frame = np.array(list(self.data), dtype=np.uint8)
        # TODO: reshape only if color != 1 byte
        #frame = np.reshape(frame, (-1, 1))
        frame = np.split(frame, self.frame_config.height)
        plt.imshow(frame, interpolation='nearest')
        plt.show()

class FrameSimpleComp(Frame):
    def get_hash(self):
        if not self.hash:
            self.hash = sum(self.data)
        return self.hash

    def compare(self, other_frame):
        diff_sum = 0
        for i in range(len(self.data)):
            diff_sum = diff_sum + abs(self.data[i] - other_frame.data[i])
        # TODO: this should not be a "if else"!
        if diff_sum > 1000:
            return 0.0
        else:
            return 1.0

class FrameStream(object):
    def __init__(self, file_path, frame_config, frame_class):
        self.frame_config = frame_config
        self.frame_class = frame_class
        command = [CONV_BIN,
                   '-i', file_path,
                   '-f', 'rawvideo',
                   '-pix_fmt', frame_config.color,
                   '-s', '{}x{}'.format(self.frame_config.width, self.frame_config.height),
                   '-'
                  ]
        self.stream = sp.Popen(command, stdout = sp.PIPE, stderr = sp.DEVNULL, bufsize = 10**8)
        self.frame_index = 0

    def __del__(self):
        self.stream.terminate()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        pass

    def __iter__(self):
        return self

    def __next__(self):
        frame = self.stream.stdout.read(self.frame_config.width * self.frame_config.height * 1)
        if len(frame):
            frame = self.frame_class(frame, self.frame_index, self.frame_config)
            self.frame_index = self.frame_index + 1            
            return frame
        else:
            raise StopIteration

class Shortcut(object):
    def __init__(self, frame_config, frame_class):
        self.frame_config = frame_config
        self.frame_class = frame_class

    def analyze(self, file_path):
        stream = FrameStream(file_path, self.frame_config, self.frame_class)
        frame_old = stream.__next__()
        for frame in stream:
            similarity = frame_old.compare(frame)
            if similarity < CONFIDENCE:
                # TODO: get fps from file
                yield frame.index / (24000 / 1001)
            frame_old = frame

if __name__ == '__main__':
    sc = Shortcut(FrameConfig('gray', 10, 10), FrameSimpleComp)
    cut_list = sc.analyze('test.avi')
    for c in cut_list:
        print(c)
    print("Done...")

