import os
import shutil

source_root = "downloads"
target_root = "markdown"

os.makedirs(target_root, exist_ok=True)

for folder in os.listdir(source_root):

    md_path = os.path.join(
        source_root,
        folder,
        "full.md"
    )

    if os.path.exists(md_path):

        target_path = os.path.join(
            target_root,
            f"{folder}.md"
        )

        shutil.copy(
            md_path,
            target_path
        )

        print(f"SUCCESS {folder}")

print("全部整理完成")