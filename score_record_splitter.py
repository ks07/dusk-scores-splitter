#!/usr/bin/env python3

import struct
import sys



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

        # apparently the last 4 bytes are the business end???
        if self.label in ['seconds', 'minutes']:
            self.value = struct.unpack('<f', self.rest[-4:])[0]
        elif self.label in ['name']:
            # 9th byte is potentially the string length... though not really necessary with the end record marker
            self.lenValue = self.rest[9]
            self.value = self.rest[10:10+self.lenValue].decode("utf-8")
            if len(self.value) != self.lenValue:
                printerr("Length indicator assumption turned out to not be true at all...")
        else:
            self.value = int.from_bytes(self.rest[-4:], byteorder='little')

    def __str__(self):
        return "[" + str(self.level) + "] " + self.label + ": " + str(self.value) + " " + str(self.rest)
        

def printerr(msg):
    print(msg, file=sys.stderr)

def split_scores(path):
    with open(path, 'rb') as infile:
        saves = infile.read()
        return saves.split(b'\x7e')[1:]

def format_byte(b):
    c = chr(b)
    if c.isalpha():
        return c
    else:
        return '%0.2x' % b

def display_records(records):
    for r in records:
        stripped = r.rstrip(b'{')
        if stripped == r:
            printerr("Found a record without the record end byte?")
        print(r)
        for b in r:
            print(format_byte(b), end="\t")
        print()

def print_levels(levels):
    for l, records in sorted(levels.items(), key=lambda x: int(x[1][0].level)):
        print(l)
        for r in sorted(records, key=lambda x: x.label):
            print("\t" + str(r))

if __name__ == '__main__':
    if len(sys.argv) < 2:
        sys.exit(1)
    records = split_scores(sys.argv[1])
    recordbuff = bytearray()
    parsedRecords = []
    for raw in records:
        if len(recordbuff) > 0:
            raw = recordbuff + raw
        print(raw)
        try:
            record = ScoreRecord(raw)
            recordbuff = bytearray()
            print(record)
            parsedRecords.append(record)
        except ValueError:
            # Splitting on the supposed record start marker isn't quite right because there's nothing stopping it appearing in values
            # If we fail, ensure the end marker is present (though of course this suffers the same problem, albeit less frequently)
            recordbuff.extend(raw)
            print("Trying to extend the buffer")

    levels = {r.level: [] for r in parsedRecords}
    for r in parsedRecords:
        levels[r.level].append(r)

    print_levels(levels)
