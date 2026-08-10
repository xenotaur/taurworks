## 2024-05-24 - File Traversal Performance
**Learning:** `pathlib.Path.iterdir()` incurs redundant `stat` system calls for properties like `is_dir()`, whereas `os.scandir` caches these properties directly from the OS directory traversal (e.g., from `readdir`), significantly speeding up directory listings.
**Action:** Always prefer `os.scandir` over `pathlib.Path.iterdir()` and `os.walk()` when scanning directories, especially when filtering by file type (like `is_dir()`).
