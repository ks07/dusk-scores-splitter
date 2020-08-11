#!/usr/bin/env python3

"""Parses and helps explains Dusk scores files.

Please see https://cucurbit.dev/posts/dusk-an-investigation-into-soap/ for an explanation.
"""

from collections import defaultdict
from functools import partial
import itertools
import struct
import sys

def printerr(msg):
    print(msg, file=sys.stderr)

try:
    from termcolor import colored
except:
    printerr("termcolor not found, output will not be coloured")
    def colored(s, *args, **kwargs):
        # *args and **kwargs are ignored, as these are just to give a compatible signature with termcolor.colored
        return s

# Possible colour names to use for detail output
colours = ['red', 'green', 'cyan', 'magenta', 'blue']

class Scores:
    """Top level scores data structure, stores Level objects."""
    def __init__(self):
        self.__levels = {}

    def add_record(self, record):
        if record.level in self.__levels:
            self.__levels[record.level].add_record(record)
        else:
            self.__levels[record.level] = Level(record)

    def __sorted_levels(self):
        return sorted(self.__levels.values(), key=lambda x: int(x.id))

    def get_levels(self):
        return self.__sorted_levels()

    def get_level(self, level):
        return self.__levels[level]

    def get_records_by_label(self, label):
        return filter(lambda r: r is not None, ( l.get_record(label) for l in self.__sorted_levels() ))

    def __str__(self):
        s = ""
        for level in self.__sorted_levels():
            s += "\n" + str(level)
        return s

class Level:
    """Stores all of the ScoreRecord instances for a given game level."""
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

    def get_records(self):
        return self.scores

    def get_record(self, label):
        for r in self.scores:
            if r.label == label:
                return r
        return None

    def get_name(self):
        return self.name if self.name is not None else "???"

    def __str__(self):
        disp_name = self.get_name()
        s = f"{disp_name} [{self.id}]"
        for r in sorted(self.scores, key=lambda r: r.label):
            s += "\n\t" + str(r)
        return s

def format_bytes(bs):
    return ' '.join(['{:02X}'.format(b) for b in bs])
def format_decimals(bs):
    return ' '.join([str(b) for b in bs])

class ScoreRecord:
    """Represents an individual records in the scores file. The constructor expects a raw bytes instance of a single record, which will be parsed."""
    def __init__(self, raw):
        # Need to prepend the start marker that gets stripped by the split
        self.raw = b'\x7e' + raw
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
            self.val_type = 'float'
            self.value = struct.unpack('<f', self.rest[-4:])[0]
        elif self.label in ['name']:
            self.val_type = 'string'
            # TODO: why do string values start at this position?
            lenValue = self.rest[9]
            self.value = self.rest[10:10+lenValue].decode("utf-8")
            if len(self.value) != lenValue:
                printerr(f"String length value {lenvalue} does not match extracted string '{self.value}'")
        else:
            self.val_type = 'int'
            self.value = int.from_bytes(self.rest[-4:], byteorder='little')
            if self.label == 'levelbeaten' and self.value != int(self.level):
                printerr(f"levelbeaten value {self.value} does not match expected value of the level tag {self.level}")

        self.mid_chunk = bytes(self.rest[0:9])

    def detail_breakdown(self):
        # [[readable, raw_len], ...] raw_len of -1 means calculate based on the readable value
        parsed_start = [['^', 1], ['s:', 1], [self.level, -1], [self.label, -1]]
        parsed_end   = []

        if self.val_type in ['float','int']:
            parsed_end.append([self.value, 4])
        else:
            detail_display = f"s[{len(self.value)}]{{{self.value}}}"
            parsed_end.append([detail_display, len(self.value.encode('utf-8')) + 1])

        parsed_end.append(['$', 1])

        accounted_for = 0
        for x in parsed_start + parsed_end:
            if x[1] == -1:
                x[1] = len(x[0].encode('utf-8'))
            accounted_for += x[1]

        if accounted_for < len(self.raw):
            parsed_start.append(['?', len(self.raw) - accounted_for])

        detail = parsed_start + parsed_end
        cols = []
        i = 0
        for c_i, d in enumerate(detail):
            j = i + d[1]
            raw_slice = self.raw[i:j]
            i = j

            if len(cols) == c_i:
                cols.append([])

            cols[c_i].extend([str(d[0]), format_bytes(raw_slice), format_decimals(raw_slice)])

        return cols


    def __str__(self):
        return "[" + str(self.level) + "] " + self.label + ": " + str(self.value) + " " + str(self.rest)

def print_detail(batched_cols):
    '''Takes an iterable of ScoreRecord.detail_breakdown() outputs, and pretty prints them to stdout.'''
    output_labels = ['parsed', 'hex', 'dec']
    max_len = max([len(l) for l in output_labels])
    output_labels = [l.ljust(max_len, '-') + '> ' for l in output_labels]

    lines = []
    max_cols = max([len(l) for l in batched_cols])
    widths = [0] * max_cols
    for cols in batched_cols:
        lines.append([])
        batch_lines = []
        for c_i, col in enumerate(cols):
            widths[c_i] = max([widths[c_i]] + [len(s) for s in col])
            for l_i, v in enumerate(col):
                if len(batch_lines) == l_i:
                    batch_lines.append([])
                batch_lines[l_i].append(v)
        lines.extend(batch_lines) # TODO: should this be append instead, and then we don't need the empty array append above?

    label_i = 0
    for l in lines:
        if len(l) == 0:
            # Batch separator
            print('\n')
            label_i = 0
            continue
        if label_i < len(output_labels):
            print(output_labels[label_i], end='')
            label_i += 1
        for w, c, v in zip(widths, itertools.cycle(colours), l):
            print(colored(v.ljust(w), c), end='|')
        print('')

def split_scores(path):
    with open(path, 'rb') as infile:
        saves = infile.read()
        return saves.split(b'\x7e')[1:]

if __name__ == '__main__':
    if len(sys.argv) < 2:
        printerr(f"Usage: {sys.argv[0]} <path_to_scores>")
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

    batched_cols = [r.detail_breakdown() for l in scores.get_levels() for r in l.get_records()]
    print_detail(batched_cols)

    print('\n----- middle chunk breakdown -----\n')

    # Bin records by the first mystery byte
    chunk_buckets = {}
    rec_count = 0
    for r in scores.get_records_by_label('name'):
        rec_count += 1
        mid = r.mid_chunk[0]
        chunk_buckets[mid] = len(r.value)
    print(f"Processed {rec_count} records:")
    for mid, length in sorted(chunk_buckets.items(), key=lambda vals: vals[1]):
        print(f"{mid}: {length} {mid - length}")
