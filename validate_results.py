from __future__ import annotations

import argparse

from common import read_jsonl, read_yaml, write_csv, write_jsonl
from schemas import EquityIncentiveExtract


def validate_results(config_path: str):
    config = read_yaml(config_path)

    rows = read_jsonl(
        config["paths"]["extract_results"]
    )

    valid = []
    errors = []

    for row in rows:
        try:
            model = EquityIncentiveExtract.model_validate(row)
            valid.append(
                model.model_dump(mode="json")
            )
        except Exception as e:
            errors.append(
                {
                    "doc_id": row.get("doc_id"),
                    "error": str(e),
                    "raw": row,
                }
            )

    write_jsonl(
        config["paths"]["validation_errors"],
        errors,
    )

    flat_rows = []

    for row in valid:
        flat_rows.append(
            {
                "doc_id": row["doc_id"],
                "company_name": row["company_name"],
                "stock_code": row["stock_code"],

                "grant_amount": row["grant_amount"],
                "grant_ratio": row["grant_ratio"],
                "participant_count": row["participant_count"],
                "exercise_price": row["exercise_price"],
                "discount_rate": row["discount_rate"],
                "waiting_period": row["waiting_period"],
                "validity_period": row["validity_period"],
            }
        )

    write_csv(
        config["paths"]["validated_results"],
        flat_rows,
    )

    print(
        f"Valid={len(valid)} Error={len(errors)}"
    )

    return valid, errors


def main():
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--config",
        default="configs/workflow.yaml",
    )

    args = parser.parse_args()

    validate_results(args.config)


if __name__ == "__main__":
    main()
