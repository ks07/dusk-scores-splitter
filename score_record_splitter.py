#!/usr/bin/env python3

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
    def __init__(self):
        self.levels = {}

    def add_record(self, record):
        if record.level in self.levels:
            self.levels[record.level].add_record(record)
        else:
            self.levels[record.level] = Level(record)

    def __sorted_levels(self):
        return sorted(self.levels.values(), key=lambda x: int(x.id));

    def get_level(self, level):
        return self.levels[level]

    def get_records_by_label(self, label):
        return filter(lambda r: r is not None, ( l.get_record(label) for l in self.__sorted_levels() ))

    def __str__(self):
        s = ""
        for level in self.__sorted_levels():
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
                printerr(f"levelbeaten value {self.value} does not match expected value of the level tag {self.level}");

    def detail_str(self):
        # [[readable, raw_len], ...] raw_len of -1 means calculate based on the readable value
        parsed_start = [['^', 1], ['s:', 1], [self.level, -1], [self.label, -1]]
        parsed_end   = []

        if self.val_type in ['float','int']:
            parsed_end.append([self.value, 4])
        else:
            parsed_end.extend([['s:', 1], [self.value, -1]])

        parsed_end.append(['$', 1])

        accounted_for = 0
        for x in parsed_start + parsed_end:
            if x[1] == -1:
                x[1] = len(x[0].encode('utf-8'))
            accounted_for += x[1]

        if accounted_for < len(self.raw):
            parsed_start.append(['?', len(self.raw) - accounted_for])

        detail = parsed_start + parsed_end
        output_labels = ['parsed', 'hex', 'dec'];
        output        = [[],       [],    []];
        i = 0
        for c, d in zip(itertools.cycle(colours), detail):
            j = i + d[1]
            raw_slice = self.raw[i:j]
            i = j
            out = [str(d[0]), format_bytes(raw_slice), format_decimals(raw_slice)]
            max_len = max([len(s) for s in out])

            output[0].append(colored(out[0].ljust(max_len), c))
            output[1].append(colored(out[1].ljust(max_len), c))
            output[2].append(colored(out[2].ljust(max_len), c))

        max_len = max([len(s) for s in output_labels]) + 1
        output_labels = [l.ljust(max_len, '-') + '> ' for l in output_labels]

        return '\n'.join([lab + ' | '.join(line) for lab, line in zip(output_labels, output)]) + '\n'


    def __str__(self):
        return "[" + str(self.level) + "] " + self.label + ": " + str(self.value) + " " + str(self.rest)
        

def split_scores(path):
    with open(path, 'rb') as infile:
        saves = infile.read()
        return saves.split(b'\x7e')[1:]

if __name__ == '__main__':
    if len(sys.argv) < 2:
        printerr(f"Usage: {sys.argv[0]} <path_to_scores>");
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

    # Display the details for all of the name records, to see if we can spot any patterns
    for r in scores.get_records_by_label('name'):
        print(r.detail_str())

    l = scores.get_level('3')
    for r in l.scores:
        print(r.detail_str())
