## 2024-05-18 - Path Traversal in Manager CLI Commands
**Vulnerability:** Path traversal in `create_project`, `refresh_project`, and `activate_project` via unvalidated `project_name` argument.
**Learning:** CLI arguments directly passed to `os.path.join(TAURWORKS_WORKSPACE, project_name)` can allow arbitrary filesystem manipulation outside the intended workspace directory if the input contains `../` or absolute paths.
**Prevention:** Validate all CLI-supplied paths or names to ensure they don't contain path traversal characters (`/`, `\`) or relative references (`.`, `..`) before appending them to base directories.
