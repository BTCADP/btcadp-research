import os
import glob

repo = r"C:\Users\mrjun\OneDrive\Documents\BTCC (Bitcoin Currency)\Website\btcadp-research"

files = glob.glob(os.path.join(repo, "*.html"))

for filepath in files:
    with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
        content = f.read()
    if "`n" in content:
        fixed = content.replace("`n", "")
        with open(filepath, "w", encoding="utf-8", newline="\n") as f:
            f.write(fixed)
        print(f"Fixed: {os.path.basename(filepath)}")
    else:
        print(f"Clean:  {os.path.basename(filepath)}")

print("\nDone.")
