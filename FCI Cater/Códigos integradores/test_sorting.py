import re

def get_sort_key(fname):
    nums = re.findall(r'\d+', fname)
    if len(nums) == 2:
        y = int(nums[0])
        m = int(nums[1])
        if y < 100: y += 2000
        return y * 100 + m
    if len(nums) == 3:
        d = int(nums[0]) # Assuming D M Y
        m = int(nums[1])
        y = int(nums[2])
        if y < 100: y += 2000
        return y * 100 + m
    return 0

filenames = [
    "FONDO COMUN DE INVERSION 24 10.pdf",
    "FONDO COMUN DE INVERSION 25 01.pdf",
    "FONDO COMUN DE INVERSION 25 11.pdf", # Nov 2025
    "FONDO COMUN DE INVERSION 26 03.pdf", # Mar 2026
    "FONDO COMUN DE INVERSION 01-11-24.pdf" # Legacy format
]

print("--- Testing Filename Sorting Logic ---")
sorted_files = sorted(filenames, key=get_sort_key)
for f in sorted_files:
    print(f"{f} -> Key: {get_sort_key(f)}")

# Check correctness
assert get_sort_key("FONDO COMUN DE INVERSION 25 11.pdf") == 202511
assert get_sort_key("FONDO COMUN DE INVERSION 26 03.pdf") == 202603
print("\nLogic Verified: Future dates sort correctly.")
