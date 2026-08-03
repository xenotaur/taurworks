## 2024-07-06 - Optimizing Directory Size Calculation
**Learning:** Using `os.walk` in conjunction with `os.path.isfile` and `os.path.getsize` results in multiple redundant `stat` system calls for each file. This creates a significant performance bottleneck when computing total sizes for large project directories. `os.scandir` caches these attributes and speeds up the traversal and size calculation significantly.
**Action:** Always prefer `os.scandir` over `os.walk` when calculating directory sizes or iterating through files where file types and attributes are needed.
## 2024-07-28 - Optimizing Project Discovery Scanning
**Learning:** `pathlib.Path.iterdir()` coupled with `is_dir()` forces an extra `stat` system call for every item in a directory, which creates a noticeable performance bottleneck during project and workspace discovery.
**Action:** Replace `iterdir()` with `os.scandir()` for directory scanning when checking file types. `os.scandir()` caches file attributes, eliminating redundant `stat` calls and speeding up the traversal significantly.
