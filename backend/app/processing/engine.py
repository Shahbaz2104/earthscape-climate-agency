"""MapReduce engine: parallel map/shuffle/reduce over worker processes."""
import multiprocessing as mp
import time
from ..config import MR_WORKERS
from ..storage.hdfs import hdfs

CTX = mp.get_context("spawn")  # fork is unsafe with the streaming thread running


class MapReduceJob:
    name = "job"
    description = ""

    def map(self, key, value):  # (k, v) -> iterable of (out_k, out_v)
        raise NotImplementedError

    def reduce(self, key, values):  # (k, [v]) -> out row dict
        raise NotImplementedError

    def partition(self, key):
        return key


def _map_worker(fn_source, chunk, key_idx):
    import importlib
    mod = importlib.import_module(fn_source[0])
    fn = getattr(mod, fn_source[1])
    out = []
    for header, line in chunk:
        key = line.split(",")[key_idx] if key_idx is not None else line.split(",")[0]
        out.extend(fn(key, (header, line)))
    return out


def _reduce_worker(fn_source, group):
    import importlib
    mod = importlib.import_module(fn_source[0])
    fn = getattr(mod, fn_source[1])
    key, values = group
    return fn(key, list(values))


def run_job(job, input_path: str, partition: str = "key", limit: int = None) -> dict:
    """Generic MapReduce runner. `partition` in {key, hash} for shuffle sorting."""
    t0 = time.time()
    text = hdfs.read_text(input_path)
    lines = text.splitlines()
    if len(lines) < 2:
        raise ValueError("Empty input file")
    header = lines[0]
    rows = lines[1:]
    hcols = [h.strip() for h in header.split(",")]
    for cand in ("station_id", "country", "region", "tile_id", "date"):
        if cand in hcols:
            key_idx = hcols.index(cand)
            break
    else:
        key_idx = 0
    chunks = [[(header, r) for r in rows[i::MR_WORKERS]] for i in range(MR_WORKERS)]  # split = input split per node
    if limit:
        chunks = [c[:limit // MR_WORKERS + 1] for c in chunks]

    mod_path = job.__module__
    fn_source = (mod_path, f"_{job.name}_map")

    with CTX.Pool(MR_WORKERS) as pool:
        mapped = pool.starmap(_map_worker, [(fn_source, chunk, key_idx) for chunk in chunks])

    pairs = [p for chunk in mapped for p in chunk]
    if partition == "key":
        pairs.sort(key=lambda x: x[0])
    groups = {}
    for k, v in pairs:
        groups.setdefault(k, []).append(v)

    fn_source = (mod_path, f"_{job.name}_reduce")
    with CTX.Pool(MR_WORKERS) as pool:
        reduced = pool.starmap(_reduce_worker, [(fn_source, (k, vs)) for k, vs in groups.items()])

    dt = (time.time() - t0) * 1000
    return {"job": job.name, "input": input_path, "split_count": MR_WORKERS,
            "map_output": len(pairs), "reduce_groups": len(groups),
            "results": reduced, "duration_ms": round(dt, 1)}