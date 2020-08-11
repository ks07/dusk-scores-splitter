# Dusk: Scores File Explainer

This repo acts as a companion to my blog article [Dusk: An Investigation Into Soap](https://cucurbit.dev/posts/dusk-an-investigation-into-soap/). It contains the Python script I used whilst trying to find where the game stored the progress towards the final achievement. I tracked changes with git whilst working through my experiments to help me explain the process retrospectively, and let readers have a look at the process in a more hands-on manner.

**Note that the code in this repo is unpolished and not designed with any kind of "production" usage in mind.**

## Usage:

If you do want to try running the tool against your own Dusk scores file, then the only required dependency is python3.

Optionally, you may install [termcolor](https://pypi.org/project/termcolor/), for some minor colour coding support in terminal output.

```
./score_record_splitter.py <path/to/scores>
```

Example output on a simple scores file (as of 52b54fc27 - note that once I'd learnt enough to finish my investigation, I did not then add my final discoveries of the purpose of the "middle chunk"):

```
$ ./score_record_splitter.py scores


parsed> ^  |s:|3 |ninja                                                     |?                           |1                                         |$  |
hex---> 7E |06|33|6E 69 6E 6A 61                                            |0A 00 00 00 FF 56 08 A8 E2  |01 00 00 00                               |7B |
dec---> 126|6 |51|110 105 110 106 97                                        |10 0 0 0 255 86 8 168 226   |1 0 0 0                                   |123|


parsed> ^  |s:|3 |startingenemies                                           |?                           |26                                        |$  |
hex---> 7E |10|33|73 74 61 72 74 69 6E 67 65 6E 65 6D 69 65 73              |0A 00 00 00 FF 56 08 A8 E2  |1A 00 00 00                               |7B |
dec---> 126|16|51|115 116 97 114 116 105 110 103 101 110 101 109 105 101 115|10 0 0 0 255 86 8 168 226   |26 0 0 0                                  |123|


parsed> ^  |s:|3 |startingsecrets                                           |?                           |6                                         |$  |
hex---> 7E |10|33|73 74 61 72 74 69 6E 67 73 65 63 72 65 74 73              |0A 00 00 00 FF 56 08 A8 E2  |06 00 00 00                               |7B |
dec---> 126|16|51|115 116 97 114 116 105 110 103 115 101 99 114 101 116 115 |10 0 0 0 255 86 8 168 226   |6 0 0 0                                   |123|


parsed> ^  |s:|3 |kills                                                     |?                           |11                                        |$  |
hex---> 7E |06|33|6B 69 6C 6C 73                                            |0A 00 00 00 FF 56 08 A8 E2  |0B 00 00 00                               |7B |
dec---> 126|6 |51|107 105 108 108 115                                       |10 0 0 0 255 86 8 168 226   |11 0 0 0                                  |123|


parsed> ^  |s:|3 |levelbeaten                                               |?                           |3                                         |$  |
hex---> 7E |0C|33|6C 65 76 65 6C 62 65 61 74 65 6E                          |0A 00 00 00 FF 56 08 A8 E2  |03 00 00 00                               |7B |
dec---> 126|12|51|108 101 118 101 108 98 101 97 116 101 110                 |10 0 0 0 255 86 8 168 226   |3 0 0 0                                   |123|


parsed> ^  |s:|3 |seconds                                                   |?                           |20.61699104309082                         |$  |
hex---> 7E |08|33|73 65 63 6F 6E 64 73                                      |0A 00 00 00 FF 6B D7 3E 6E  |99 EF A4 41                               |7B |
dec---> 126|8 |51|115 101 99 111 110 100 115                                |10 0 0 0 255 107 215 62 110 |153 239 164 65                            |123|


parsed> ^  |s:|3 |minutes                                                   |?                           |1.0                                       |$  |
hex---> 7E |08|33|6D 69 6E 75 74 65 73                                      |0A 00 00 00 FF 6B D7 3E 6E  |00 00 80 3F                               |7B |
dec---> 126|8 |51|109 105 110 117 116 101 115                               |10 0 0 0 255 107 215 62 110 |0 0 128 63                                |123|


parsed> ^  |s:|3 |name                                                      |?                           |s[11]{Head cheese}                        |$  |
hex---> 7E |05|33|6E 61 6D 65                                               |12 00 00 00 FF EE F1 E9 FD  |0B 48 65 61 64 20 63 68 65 65 73 65       |7B |
dec---> 126|5 |51|110 97 109 101                                            |18 0 0 0 255 238 241 233 253|11 72 101 97 100 32 99 104 101 101 115 101|123|


parsed> ^  |s:|3 |secrets                                                   |?                           |0                                         |$  |
hex---> 7E |08|33|73 65 63 72 65 74 73                                      |0A 00 00 00 FF 56 08 A8 E2  |00 00 00 00                               |7B |
dec---> 126|8 |51|115 101 99 114 101 116 115                                |10 0 0 0 255 86 8 168 226   |0 0 0 0                                   |123|


parsed> ^  |s:|4 |levelbeaten                                               |?                           |4                                         |$  |
hex---> 7E |0C|34|6C 65 76 65 6C 62 65 61 74 65 6E                          |0A 00 00 00 FF 56 08 A8 E2  |04 00 00 00                               |7B |
dec---> 126|12|52|108 101 118 101 108 98 101 97 116 101 110                 |10 0 0 0 255 86 8 168 226   |4 0 0 0                                   |123|

----- middle chunk breakdown -----

Processed 1 records:
18: 11 7
```
