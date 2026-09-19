"""Parse official Python values or CLI diagnostics without mistaking USB IDs for DoA."""
import math
import re

NUM = r'[-+]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][-+]?\d+)?|[-+]?(?:nan|inf)'

def values(payload, command, count):
    if isinstance(payload,str):
        lines=[line for line in payload.splitlines() if re.match(r'^\s*'+re.escape(command)+r'(?:\s|:)',line)]
        if len(lines)!=1: raise ValueError(f'Missing/duplicate {command} result')
        text=lines[0].strip()[len(command):]
        text=re.sub(r'\([^)]*deg\)', '', text, flags=re.I)
        # Reject unknown words rather than extracting a partial success out of an error.
        text=text.strip(' :[]')
        tokens=re.split(r'[\s,]+',text)
        if len(tokens)!=count or any(not re.fullmatch(NUM,t,re.I) for t in tokens):
            raise ValueError(f'Malformed {command}')
        result=[float(t) for t in tokens]
    else:
        result=[float(v) for v in payload]
    if len(result)!=count: raise ValueError(f'{command} expected {count} values')
    return result

def wrap(degrees): return (degrees+180)%360-180

def parse_doa(payload, offset=0, invert=False):
    if not math.isfinite(offset): raise ValueError('Invalid azimuth offset')
    # Both official Python and CLI primary values are radians; CLI parentheses are annotations.
    raw=values(payload,'AEC_AZIMUTH_VALUES',4)
    result=[]
    for rad in raw:
        if math.isnan(rad): result.append(None); continue
        if not math.isfinite(rad): raise ValueError('Invalid azimuth')
        result.append(wrap((-1 if invert else 1)*math.degrees(rad)+offset))
    return tuple(result)

def parse_energy(payload):
    result=values(payload,'AEC_SPENERGY_VALUES',4)
    if any(not math.isfinite(v) or v<0 for v in result): raise ValueError('Invalid speech energy')
    return tuple(result)
