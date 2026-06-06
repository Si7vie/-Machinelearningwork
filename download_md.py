import os
import pandas as pd
import requests
import zipfile

# 读取第二阶段结果
df = pd.read_csv("data/batch/result_mapping.csv")

# 保存目录
os.makedirs("downloads", exist_ok=True)
os.makedirs("markdown", exist_ok=True)

for _, row in df.iterrows():

    doc_id = str(row["doc_id"])
    zip_url = row["full_zip_url"]

    if pd.isna(zip_url) or zip_url == "":
        continue

    try:

        # 下载zip
        zip_path = f"downloads/{doc_id}.zip"

        r = requests.get(zip_url)

        with open(zip_path, "wb") as f:
            f.write(r.content)

        # 解压
        extract_dir = f"downloads/{doc_id}"

        with zipfile.ZipFile(zip_path, "r") as zip_ref:
            zip_ref.extractall(extract_dir)

        # 找 markdown.md
        md_source = os.path.join(
            extract_dir,
            "markdown.md"
        )

        md_target = os.path.join(
            "markdown",
            f"{doc_id}.md"
        )

        if os.path.exists(md_source):

            with open(
                md_source,
                "r",
                encoding="utf-8"
            ) as f:
                content = f.read()

            with open(
                md_target,
                "w",
                encoding="utf-8"
            ) as f:
                f.write(content)

            print(f"SUCCESS {doc_id}")

        else:

            print(f"NO_MD {doc_id}")

    except Exception as e:

        print(f"ERROR {doc_id}: {e}")

print("全部完成")