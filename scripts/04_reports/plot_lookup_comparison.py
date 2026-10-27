#!/usr/bin/env python3
"""Compare two GLC_FCS30D land-cover-to-NDVI lookup tables."""

import argparse
import csv
import hashlib
import json
import math
import textwrap
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_lookup(path, label_column):
    rows = {}
    with path.open(newline="", encoding="utf-8-sig") as source:
        for row in csv.DictReader(source):
            code = int(row["lc_code"])
            value = row.get("lc_ndvi", "").strip()
            if code in (0, 250) and not value:
                continue
            rows[code] = {
                "label": row[label_column].strip(),
                "ndvi": float(value) if value else None,
            }
    return rows


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("us_lookup", type=Path)
    parser.add_argument("varun_lookup", type=Path)
    parser.add_argument("output_csv", type=Path)
    parser.add_argument("output_png", type=Path)
    parser.add_argument("output_summary", type=Path)
    args = parser.parse_args()

    us = read_lookup(args.us_lookup, "lc_desc")
    varun = read_lookup(args.varun_lookup, "lc_label")
    codes = sorted(set(us) | set(varun))
    if set(us) != set(varun):
        raise ValueError(f"Class-code mismatch: US only={set(us)-set(varun)}; Varun only={set(varun)-set(us)}")

    rows = []
    for code in codes:
        if "".join(us[code]["label"].split()) != "".join(varun[code]["label"].split()):
            raise ValueError(f"Class-label mismatch for {code}")
        u = us[code]["ndvi"]
        v = varun[code]["ndvi"]
        rows.append({
            "lc_code": code,
            "lc_label": us[code]["label"],
            "us_derived_lc_ndvi": u,
            "varun_judgment_lc_ndvi": v,
            "varun_minus_us": None if u is None or v is None else v - u,
            "comparison_status": "matched" if u is not None and v is not None else "US 2019 NDVI unavailable",
        })

    args.output_csv.parent.mkdir(parents=True, exist_ok=True)
    with args.output_csv.open("w", newline="") as target:
        writer = csv.DictWriter(target, fieldnames=rows[0].keys(), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)

    matched = [r for r in rows if r["varun_minus_us"] is not None]
    differences = np.array([r["varun_minus_us"] for r in matched])
    summary = {
        "us_lookup": str(args.us_lookup),
        "us_lookup_sha256": sha256(args.us_lookup),
        "varun_lookup": str(args.varun_lookup),
        "varun_lookup_sha256": sha256(args.varun_lookup),
        "classes_total": len(rows),
        "classes_compared": len(matched),
        "classes_without_us_2019_ndvi": [r["lc_code"] for r in rows if r["us_derived_lc_ndvi"] is None],
        "excluded_fill_codes": [0, 250],
        "varun_lower_count": int((differences < 0).sum()),
        "varun_higher_count": int((differences > 0).sum()),
        "equal_count": int((differences == 0).sum()),
        "mean_signed_difference_varun_minus_us": float(differences.mean()),
        "mean_absolute_difference": float(np.abs(differences).mean()),
        "rmse": float(np.sqrt(np.mean(differences ** 2))),
        "interpretation": "Descriptive comparison of lookup assignments; it does not establish which lookup is more accurate.",
    }
    args.output_summary.write_text(json.dumps(summary, indent=2) + "\n")

    display_rows = list(reversed(rows))
    y = np.arange(len(display_rows))
    labels = [f"{r['lc_code']}  " + "\n".join(textwrap.wrap(r["lc_label"], 36)) for r in display_rows]
    us_values = np.array([np.nan if r["us_derived_lc_ndvi"] is None else r["us_derived_lc_ndvi"] for r in display_rows])
    varun_values = np.array([r["varun_judgment_lc_ndvi"] for r in display_rows])
    delta_values = np.array([np.nan if r["varun_minus_us"] is None else r["varun_minus_us"] for r in display_rows])

    fig, (ax_value, ax_delta) = plt.subplots(
        1, 2, figsize=(15.5, 14.5), sharey=True,
        gridspec_kw={"width_ratios": [1.45, 1]})
    fig.subplots_adjust(left=0.29, right=0.98, top=0.93, bottom=0.075, wspace=0.08)
    for yi, u, v in zip(y, us_values, varun_values):
        if math.isfinite(u):
            ax_value.plot([u, v], [yi, yi], color="#B7BCC5", linewidth=1.4, zorder=1)
    ax_value.scatter(us_values, y, s=38, color="#1F77B4", marker="o", label="US-derived 2019", zorder=3)
    ax_value.scatter(varun_values, y, s=43, facecolors="white", edgecolors="#D55E00", marker="^", linewidths=1.5,
                     label="Varun judgment-based", zorder=4)
    missing = np.isnan(us_values)
    ax_value.scatter(varun_values[missing], y[missing], s=90, facecolors="none", edgecolors="#6B7280", marker="s",
                     linewidths=1.2, label="US value unavailable", zorder=2)
    ax_value.axvline(0, color="#4B5563", linewidth=0.8)
    ax_value.set_xlim(-0.14, 0.86)
    ax_value.set_xlabel("Assigned land-cover NDVI")
    ax_value.set_yticks(y, labels)
    ax_value.legend(loc="lower right", frameon=False)
    ax_value.grid(axis="x", color="#E5E7EB", linewidth=0.8)
    ax_value.grid(axis="y", visible=False)

    colors = np.where(delta_values < 0, "#D55E00", "#0072B2")
    ax_delta.barh(y, np.nan_to_num(delta_values), color=colors, height=0.6)
    ax_delta.axvline(0, color="#111827", linewidth=0.9)
    for yi, delta, missing_value in zip(y, delta_values, missing):
        if missing_value:
            ax_delta.text(0.01, yi, "US unavailable", va="center", fontsize=8, color="#6B7280")
        elif abs(delta) >= 0.20:
            ax_delta.text(delta + (0.012 if delta >= 0 else -0.012), yi, f"{delta:+.2f}",
                          ha="left" if delta >= 0 else "right", va="center", fontsize=8, color="#374151")
    ax_delta.set_xlim(-0.52, 0.52)
    ax_delta.set_xlabel("Difference: Varun minus US-derived NDVI")
    ax_delta.grid(axis="x", color="#E5E7EB", linewidth=0.8)
    ax_delta.grid(axis="y", visible=False)

    for ax in (ax_value, ax_delta):
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
        ax.spines["left"].set_visible(False)
        ax.tick_params(axis="y", length=0, labelsize=8.5)

    fig.suptitle(
        f"Varun assigns lower NDVI to {summary['varun_lower_count']} of {summary['classes_compared']} matched land-cover classes",
        fontsize=16, fontweight="bold", y=0.982)
    fig.text(
        0.5, 0.958,
        "US table: area-weighted 2019 Landsat NDVI on the published Alaska-inclusive US urban calibration domain. "
        "Varun table: judgment-based values informed by typical NDVI ranges and internal class ordering.",
        ha="center", va="top", fontsize=9.5, color="#4B5563")
    fig.text(
        0.5, 0.005,
        f"Matched classes: {summary['classes_compared']} | Mean absolute difference: {summary['mean_absolute_difference']:.3f} | "
        f"Mean signed difference: {summary['mean_signed_difference_varun_minus_us']:+.3f} | RMSE: {summary['rmse']:.3f}. "
        "Seven US classes lacked valid 2019 calibration NDVI; comparisons are descriptive.",
        ha="center", va="bottom", fontsize=8.5, color="#4B5563")
    args.output_png.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(args.output_png, dpi=180, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
