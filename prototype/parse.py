import pdfplumber, pandas as pd, sys
from multiprocessing import Pool
F = sys.argv[1]
def work(rng):
    out = []
    with pdfplumber.open(F) as p:
        for i in range(*rng):
            for r in p.pages[i].extract_table() or []:
                if not r or not (r[0] or "").strip().isdigit(): continue
                if len(r) == 17: del r[10]
                out.append([(c or "").replace("\n", " ").strip() for c in r])
    return out
if __name__ == "__main__":
    n = len(pdfplumber.open(F).pages); step = 50
    with Pool(8) as pool:
        rows = sum(pool.map(work, [(a, min(a + step, n)) for a in range(0, n, step)]), [])
    pd.DataFrame(rows).to_pickle(sys.argv[2]); print(F, len(rows), {len(r) for r in rows})
