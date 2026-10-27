import math

def number(v):
    if isinstance(v,bool) or v is None: return None
    try:
        n=float(v)
        return n if math.isfinite(n) else None
    except (ValueError,TypeError): return None

def fmt(v, digits=2):
    if digits==0 and isinstance(v,int) and not isinstance(v,bool):return f'{v:,d}'
    n=number(v)
    if n is None: return "not available"
    return f"{n:,.{digits}f}"

def rows(v):
    if isinstance(v,dict) and "data" in v: return rows(v["data"])
    if isinstance(v,list): return v
    raise ValueError("Expected a JSON array or a data envelope.")

def cell(v):
    return str(v if v is not None else "not available").replace("|","/").replace("\n"," ")

def table(headers, data):
    return "\n".join(["| "+" | ".join(headers)+" |","| "+" | ".join("---" for _ in headers)+" |"]+
                     ["| "+" | ".join(cell(x) for x in r)+" |" for r in data])
