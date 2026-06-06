import pandas as pd
import requests
import time

TOKEN = os.getenv("MINERU_API_KEY")
headers = {
    "Authorization": f"Bearer {TOKEN}"
}

# 读取第一阶段结果
df = pd.read_csv("data/batch/batch_mapping.csv")

results = []

for _, row in df.iterrows():

    doc_id = row["doc_id"]
    batch_id = row["batch_id"]

    url = f"https://mineru.net/api/v4/extract-results/batch/{batch_id}"

    try:

        response = requests.get(
            url,
            headers=headers
        )

        result = response.json()

        extract_result = result["data"]["extract_result"][0]

        state = extract_result["state"]

        full_zip_url = extract_result.get(
            "full_zip_url",
            ""
        )

        print(
            f"{doc_id} | {state}"
        )

        results.append({
            "doc_id": doc_id,
            "batch_id": batch_id,
            "state": state,
            "full_zip_url": full_zip_url
        })

    except Exception as e:

        print(
            f"ERROR {doc_id}: {e}"
        )

    time.sleep(0.2)

# 保存结果
pd.DataFrame(results).to_csv(
    "result_mapping.csv",
    index=False,
    encoding="utf-8-sig"
)

print("查询完成")