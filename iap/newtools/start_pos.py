def start_pos(csvobj, get_counter=False):
    """Go to first line of csv file, skip any text before a newline"""

    csvobj.seek(0)
    pos = 0
    empty = True
    start = pos
    for line in csvobj:
        line = line.strip()
        if line == "":
            empty = True
        elif empty:
            start = pos
            empty = False
        pos += 1
    csvobj.seek(0)
    if get_counter:
        return start
    else:
        for _counter in range(start):
            next(csvobj)
