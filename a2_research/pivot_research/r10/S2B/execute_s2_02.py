from __future__ import annotations

import json
from pathlib import Path

import numpy as np

from event_harness import END, START, evaluate
from run_s2b import clean_json

OUT = Path(__file__).resolve().parent


def main():
    prepared = json.load(open(OUT / "PREPARED_S2_02.json", encoding="utf-8"))
    if prepared.get("outcomes_computed"):
        raise RuntimeError("S2-02 outcome was already computed")
    events = json.load(open(OUT / "S2_02_EVENTS.json", encoding="utf-8"))
    with np.load(OUT / "dev_panel_prices.npz", allow_pickle=False) as z:
        dates = z["dates"].astype(str)
        assets, roster, sic2 = z["assets"], z["roster"], z["sic2"]
        op, cl = z["adjusted_open"], z["adjusted_close"]
    if dates[0] < START or dates[-1] > END:
        raise RuntimeError("refusing to score a price axis outside the development window")
    result = evaluate(events, dates, assets, roster, sic2, op, cl)
    payload = {"S2-02": result, "preparation": prepared}
    with (OUT / "DEV_RESULTS.json").open("w", encoding="utf-8") as f:
        json.dump(clean_json(payload), f, indent=2, allow_nan=False)
    print(json.dumps(clean_json({"n_event_records": len(events), "n_usable_months": result["n_months"],
                                 "mean_net_excess": result["mean_net_excess"],
                                 "nw_t_lag3": result["nw_t_lag3"],
                                 "haircut_pass_probability": result["haircut_pass_probability"]}), indent=2))


if __name__ == "__main__":
    main()
