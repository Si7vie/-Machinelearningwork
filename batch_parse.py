import pandas as pd
import requests
import time

# ====== 你的MinerU Key ======
TOKEN =  os.getenv("MINERU_API_KEY")
# ====== 读取metadata ======"

df = pd.read_csv("data/metadata/metadata.csv")

# ====== MinerU接口 ======
url = "https://mineru.net/api/v4/extract/task/batch"

headers = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {TOKEN}"
}

# ====== 保存结果 ======
batch_records = []

# ====== 遍历metadata ======
for _, row in df.iterrows():

    doc_id = str(row["doc_id"])
    pdf_url = row["pdf_url"]

    data = {
        "files": [
            {
                "url": pdf_url,
                "data_id": doc_id
            }
        ],
        "model_version": "vlm"
    }

    try:

        response = requests.post(
            url,
            headers=headers,
            json=data
        )

        result = response.json()

        if result["code"] == 0:

            batch_id = result["data"]["batch_id"]

            print(
                f"SUCCESS | doc_id={doc_id} | batch_id={batch_id}"
            )

            batch_records.append({
                "doc_id": doc_id,
                "batch_id": batch_id
            })

        else:

            print(
                f"FAILED | doc_id={doc_id}"
            )

    except Exception as e:

        print(
            f"ERROR | doc_id={doc_id} | {e}"
        )

    time.sleep(1)

# ====== 保存CSV ======
batch_df = pd.DataFrame(batch_records)

batch_df.to_csv(
    "batch_mapping.csv",
    index=False,
    encoding="utf-8-sig"
)

print("完成")