#!/usr/bin/env python3

import struct
import sys

class Scores:
    def __init__(self):
        self.levels = {}

    def add_record(self, record):
        if record.level in self.levels:
            self.levels[record.level].add_record(record)
        else:
            self.levels[record.level] = Level(record)

    def __str__(self):
        s = ""
        for level in sorted(self.levels.values(), key=lambda x: int(x.id)):
            s += "\n" + str(level)
        return s

class Level:
    def __init__(self, record):
        self.id     = record.level
        self.scores = [ record ]
        self.name   = None
        if record.label == "name":
            self.name = record.value

    def add_record(self, record):
        self.scores.append(record)
        if record.label == "name":
            if self.name is not None:
                raise ValueError("tried to add multiple name records to Level")
            self.name = record.value

    def get_name(self):
        return self.name if self.name is not None else "???"

    def __str__(self):
        disp_name = self.get_name()
        s = f"{disp_name} [{self.id}]"
        for r in sorted(self.scores, key=lambda r: r.label):
            s += "\n\t" + str(r)
        return s

class ScoreRecord:
    def __init__(self, raw):
        self.raw = raw
        # { appears to be the record end marker
        stripped = raw.rstrip(b'{')
        if stripped == raw:
            raise ValueError("Found a record without the record end byte? " + str(raw))
        raw = stripped

        identifierLen = raw[0]
        identifier = raw[1:1+identifierLen].decode()

        for i, c in enumerate(identifier):
            if not c.isdecimal():
                break
        self.level = identifier[0:i]
        self.label = identifier[i:]
        self.rest  = raw[1+identifierLen:]

        # Numeric values appear to be at the end of records, strings are variable length.
        if self.label in ['seconds', 'minutes']:
            self.value = struct.unpack('<f', self.rest[-4:])[0]
        elif self.label in ['name']:
            # TODO: why do string values start at this position?
            lenValue = self.rest[9]
            self.value = self.rest[10:10+lenValue].decode("utf-8")
            if len(self.value) != lenValue:
                printerr(f"String length value {lenvalue} does not match extracted string '{self.value}'")
        else:
            self.value = int.from_bytes(self.rest[-4:], byteorder='little')
            if self.label == 'levelbeaten' and self.value != int(self.level):
                printerr(f"levelbeaten value {self.value} does not match expected value of the level tag {self.level}");

    def __str__(self):
        return "[" + str(self.level) + "] " + self.label + ": " + str(self.value) + " " + str(self.rest)
        

def printerr(msg):
    print(msg, file=sys.stderr)

def split_scores(path):
    with open(path, 'rb') as infile:
        saves = infile.read()
        return saves.split(b'\x7e')[1:]

if __name__ == '__main__':
    if len(sys.argv) < 2:
        sys.exit(1)
    records = split_scores(sys.argv[1])
    recordbuff = bytearray()
    scores = Scores()
    for raw in records:
        if len(recordbuff) > 0:
            raw = recordbuff + raw
        try:
            record = ScoreRecord(raw)
            recordbuff = bytearray()
            scores.add_record(record)
        except ValueError:
            # Splitting on the supposed record start marker isn't quite right because there's nothing stopping it appearing in values
            # If we fail, ensure the end marker is present (though of course this suffers the same problem, albeit less frequently)
            recordbuff.extend(raw)
            printerr("Got truncated record, trying to extend the buffer...")

    print(scores)
