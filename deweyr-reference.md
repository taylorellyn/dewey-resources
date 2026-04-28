# deweyr — R Package Reference

**Dewey Data · 2026**

The official R interface to the Dewey Data platform. Download, preview, filter, and read datasets directly from R — no manual file management required.

**Install**
```r
pak::pak("Dewey-Data/deweyr")
```

> **API Key** — All functions require a Dewey API key. Generate one at **deweydata.io → Connections → Add Connection → API Key**. Store it in your `~/.Renviron` file as `DEWEY_API_KEY=your-key` and load it with `Sys.getenv("DEWEY_API_KEY")` — never hardcode it in scripts you share.
>
> Open your `.Renviron` file with: `usethis::edit_r_environ()`

---

## Function Index

| Function | Description | Type |
|---|---|---|
| [`download_dewey()`](#download_dewey) | Download a folder via UV. Recommended for most users — no Python setup required. | Recommended |
| [`preview_dewey_duck()`](#preview_dewey_duck) | Fetch a small sample from a dataset without downloading. Explore schema before committing. | Preview |
| [`download_dewey_duck()`](#download_dewey_duck) | Download with DuckDB — supports column selection, row filtering, and partitioning before download. | DuckDB |
| [`read_dewey_duck()`](#read_dewey_duck) | Read a locally downloaded dataset into R as a tibble. Supports optional SQL filtering. | Read |
| [`download_dewey_py()`](#download_dewey_py) | Legacy download function using an existing Python installation. Use `download_dewey()` instead when possible. | Legacy |

---

## download_dewey() {#download_dewey}

**Recommended**

Downloads files from a Dewey folder to your local machine using UV — a fast Python environment manager that handles all Python dependencies automatically. No Python installation required. The recommended download method for most users.

> **First-time setup** — If UV isn't installed, deweyr installs it automatically on first run. You may see a prompt to restart your terminal — this only happens once. Do not set `python_version = "3.14"` or higher — not currently compatible with deweypy.

### Usage

```r
download_dewey(
  api_key,
  folder_id,
  download_path        = NULL,
  python_version       = "3.13",
  num_workers          = NULL,
  partition_key_before = NULL,
  partition_key_after  = NULL
)
```

### Arguments

| Argument | Type | Description |
|---|---|---|
| `api_key` ⚠️ required | character | Your Dewey API key. Generate at deweydata.io → Connections → Add Connection → API Key. Shown once — save immediately. |
| `folder_id` ⚠️ required | character | Your Dewey folder ID or full Dewey API URL. Found on your project page at deweydata.io. |
| `download_path` | character | Local folder for downloaded files. Defaults to `./dewey-downloads` in your working directory. Use an absolute path to be safe. |
| `python_version` | character | Python version used by UV. Default: `"3.13"`. Most users should leave this unchanged. **Do not set to `"3.14"` or higher** — not currently compatible with deweypy. |
| `num_workers` | integer | *[Advanced]* Parallel download threads. Default: `NULL` (deweypy uses 8). Only adjust if you have specific performance requirements. |
| `partition_key_after` | character | *[Advanced]* Download partitions dated on or after this date. Format: `"YYYY-MM-DD"`. Only relevant for date-partitioned datasets. Leave `NULL` to download all data. |
| `partition_key_before` | character | *[Advanced]* Download partitions dated on or before this date. Format: `"YYYY-MM-DD"`. Combine with `partition_key_after` to define a date window. |

### Examples

```r
api_key <- Sys.getenv("DEWEY_API_KEY")

# Basic download to default location
download_dewey(
  api_key   = api_key,
  folder_id = "folder123"
)

# Custom local path
download_dewey(
  api_key       = api_key,
  folder_id     = "folder123",
  download_path = "~/Documents/dewey-downloads/my-dataset"
)

# Date-partitioned download (recommended for monthly datasets)
download_dewey(
  api_key              = api_key,
  folder_id            = "folder123",
  download_path        = "~/Documents/dewey-downloads/my-dataset",
  partition_key_after  = "2024-01-01",
  partition_key_before = "2024-12-31"
)

# Download using a full Dewey URL instead of folder ID
download_dewey(
  api_key   = api_key,
  folder_id = "https://api.deweydata.io/api/v1/external/data/abc123"
)
```

---

## preview_dewey_duck() {#preview_dewey_duck}

**Preview**

Fetches a small sample from a Dewey dataset directly from the source — no download required. Use this to explore column names, data types, and values before deciding what to filter and select in a full download.

### Usage

```r
preview_dewey_duck(api_key, data_id, limit = 10, where = NULL)
```

### Arguments

| Argument | Type | Description |
|---|---|---|
| `api_key` ⚠️ required | character | Your Dewey API key. |
| `data_id` ⚠️ required | character | The Dewey dataset ID. Format: `"prj_xxx__fldr_yyy"`. |
| `limit` | integer | Number of rows to return. Default: `10`. Set to `0` to return no rows and retrieve only column names and types. |
| `where` | character | Optional SQL WHERE clause. Example: `"CARRIER_GROUP = 'Major'"`. |

**Returns:** A tibble of up to `limit` rows from the dataset.

### Examples

```r
api_key <- Sys.getenv("DEWEY_API_KEY")
data_id <- "prj_xxx__fldr_yyy"

# Preview first 10 rows
preview_dewey_duck(api_key, data_id)

# Get column names only — no data transferred
colnames(preview_dewey_duck(api_key, data_id, limit = 0))

# Filtered preview
preview_dewey_duck(api_key, data_id, where = "CARRIER_GROUP = 'Major'")
```

---

## download_dewey_duck() {#download_dewey_duck}

**DuckDB**

Downloads a Dewey dataset to local parquet files with optional pre-download filtering and column selection via DuckDB. Returns the download path invisibly, making it pipeable directly into `read_dewey_duck()`. Use when you need to filter rows or select columns before data lands on disk.

> **Tip** — `download_dewey_duck()` returns its output path invisibly, so you can chain it directly:
> ```r
> download_dewey_duck(...) |> read_dewey_duck()
> ```

### Usage

```r
download_dewey_duck(
  api_key,
  data_id,
  output_dir = get_download_dir(),
  partition,
  overwrite  = FALSE,
  file_name  = NULL,
  where      = NULL,
  select     = NULL
)
```

### Arguments

| Argument | Type | Description |
|---|---|---|
| `api_key` ⚠️ required | character | Your Dewey API key. |
| `data_id` ⚠️ required | character | The Dewey dataset ID. Format: `"prj_xxx__fldr_yyy"`. |
| `output_dir` | character | Local directory for downloaded files. Defaults to `get_download_dir()`. |
| `partition` | character | Column name to partition by. Omit to use Dewey's suggested partition column. Pass `NULL` explicitly to download as a single unpartitioned file. |
| `overwrite` | logical | If `FALSE` (default), errors if the output folder already exists. Set `TRUE` to delete and re-download. |
| `file_name` | character | Optional output file name override. |
| `where` | character | Optional SQL WHERE clause. No validation — errors are on you. Example: `"CARRIER_GROUP = 'Major'"`. |
| `select` | vector | Optional column indices, ranges, or names to download. Accepts mixed input: `c(1:3, 7, "CARRIER_NAME")`. The partition column is always included automatically. |

**Returns:** The path to the downloaded dataset folder, invisibly. Pipe into `read_dewey_duck()` to read immediately after downloading.

### Examples

```r
api_key <- Sys.getenv("DEWEY_API_KEY")
data_id <- "prj_xxx__fldr_yyy"

# Use Dewey's default partition column
download_dewey_duck(api_key, data_id)

# Specify your own partition column
download_dewey_duck(api_key, data_id, partition = "MONTH_DATE_PARSED")

# No partitioning — single output file
download_dewey_duck(api_key, data_id, partition = NULL)

# Filter rows and select columns before download
download_dewey_duck(
  api_key   = api_key,
  data_id   = data_id,
  partition = "MONTH_DATE_PARSED",
  where     = "CARRIER_GROUP = 'Major'",
  select    = c(1:3, "TOTAL")
)

# Download and read in one pipeline
df <- download_dewey_duck(
  api_key   = api_key,
  data_id   = data_id,
  partition = "MONTH_DATE_PARSED"
) |>
  read_dewey_duck()
```

---

## read_dewey_duck() {#read_dewey_duck}

**Read**

Reads a locally downloaded Dewey dataset into R as a tibble. Accepts the invisible return path from `download_dewey_duck()` for direct piping, or any path to a previously downloaded dataset. Supports optional SQL filtering on read.

> **Advanced DuckDB queries** — For window functions, aggregations, or complex SQL, use DuckDB directly. Connect with `DBI::dbConnect(duckdb::duckdb())` and query with `read_parquet('path/**/*.parquet', hive_partitioning=true)`. See `vignette("advanced-queries", package = "deweyr")`.

### Usage

```r
read_dewey_duck(path, where = NULL)
```

### Arguments

| Argument | Type | Description |
|---|---|---|
| `path` ⚠️ required | character | Path to the downloaded dataset folder. Also accepts the invisible return value of `download_dewey_duck()` for piping. |
| `where` | character | Optional SQL WHERE clause applied on read. Example: `"CARRIER_GROUP = 'Major'"`. |

**Returns:** A tibble of the dataset.

### Pipe Pattern

```
download_dewey_duck()  |>  read_dewey_duck()  →  tibble in R
```

### Examples

```r
# Read a previously downloaded dataset
df <- read_dewey_duck("~/dewey-downloads/my-dataset")

# Filter on read
df <- read_dewey_duck(
  "~/dewey-downloads/my-dataset",
  where = "CARRIER_GROUP = 'Major'"
)

# Full pipeline — download, filter, and read in one step
df <- download_dewey_duck(
  api_key   = Sys.getenv("DEWEY_API_KEY"),
  data_id   = "prj_xxx__fldr_yyy",
  partition = "MONTH_DATE_PARSED"
) |>
  read_dewey_duck(where = "CARRIER_GROUP = 'Major'")
```

---

## download_dewey_py() {#download_dewey_py}

**Legacy**

Downloads files from a Dewey folder using an existing local Python installation and the deweypy package. Functionally similar to `download_dewey()`, but requires Python to already be installed and configured on your system.

> ⚠️ **Prefer `download_dewey()` instead** — Unless you have a specific reason to manage your own Python environment, use `download_dewey()`. It handles all Python dependencies automatically via UV and requires no manual setup.

### Usage

```r
download_dewey_py(
  api_key,
  folder_id,
  download_path        = NULL,
  python_path          = NULL,
  num_workers          = NULL,
  partition_key_before = NULL,
  partition_key_after  = NULL
)
```

### Arguments

| Argument | Type | Description |
|---|---|---|
| `api_key` ⚠️ required | character | Your Dewey API key. |
| `folder_id` ⚠️ required | character | Dewey folder ID or full API URL. |
| `download_path` | character | Local directory for files. Defaults to `get_download_dir()`. |
| `python_path` | character | Path to your Python executable. If `NULL`, deweyr auto-detects Python on your system. |
| `num_workers` | integer | *[Advanced]* Parallel download threads. Default: `NULL` (deweypy uses 8). |
| `partition_key_after` | character | *[Advanced]* Download partitions on or after this date. Format: `"YYYY-MM-DD"`. |
| `partition_key_before` | character | *[Advanced]* Download partitions on or before this date. Format: `"YYYY-MM-DD"`. |

### Examples

```r
api_key <- Sys.getenv("DEWEY_API_KEY")

# Basic usage — auto-detects Python
download_dewey_py(
  api_key   = api_key,
  folder_id = "folder123"
)

# Specify Python path explicitly
download_dewey_py(
  api_key     = api_key,
  folder_id   = "folder123",
  python_path = "/usr/local/bin/python3"
)
```

---

## Resources

| Resource | Link |
|---|---|
| Working with R — Dewey official documentation | [docs.deweydata.io/docs/working-with-r-new](https://docs.deweydata.io/docs/working-with-r-new) |
| deweyr on GitHub | [github.com/Dewey-Data/deweyr](https://github.com/Dewey-Data/deweyr) |
| Dewey Data Platform | [deweydata.io](https://www.deweydata.io) |
