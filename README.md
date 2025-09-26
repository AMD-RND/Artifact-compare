# Artifact Compare

A tool for fetching and comparing artifacts from Artifactory builds across different platforms.

## Overview

This project provides utilities to download `latest_commits.txt` files from Artifactory build folders for specified builds and platforms, enabling comparison and analysis of artifacts across different environments.

## Features

- Download `latest_commits.txt` from multiple builds and platforms
- Support for authentication via Bearer token or Basic auth
- Automatic retry mechanism with exponential backoff
- Metadata tracking with timestamps and source URLs
- Error handling and reporting

## Prerequisites

- Python 3.x
- `requests` library

Install dependencies:
```bash
pip install requests
```

## Setup

### Authentication (Recommended)

Set your Artifactory token as an environment variable:

**Windows (PowerShell):**
```powershell
$env:ARTIFACTORY_TOKEN = "your-token-here"
```

**Linux/macOS:**
```bash
export ARTIFACTORY_TOKEN="your-token-here"
```

### Alternative: Basic Authentication

If you can't use a token, you can provide username and password directly via command line arguments (less secure).

## Usage

### Basic Usage

```bash
python3 scripts/fetch_latest_commits.py \
  --base-url "https://xcoartifactory.xilinx.com/native/vai-rt-ipu-prod-local/com/amd/onnx-rt/stx/cp_dev" \
  --builds 3025 3026 \
  --platforms windows linux arm \
  --out data
```

### Command Line Arguments

| Argument | Required | Description | Example |
|----------|----------|-------------|---------|
| `--base-url` | Yes | Base Artifactory URL | `https://xcoartifactory.xilinx.com/...` |
| `--builds` | Yes | Space-separated list of build IDs | `3025 3026 3027` |
| `--platforms` | Yes | Space-separated list of platforms | `windows linux arm` |
| `--out` | No | Output directory (default: `data/builds`) | `data` or `artifact-compare/data` |
| `--user` | No | Username for Basic auth | `myusername` |
| `--password` | No | Password for Basic auth | `mypassword` |
| `--retries` | No | Number of retry attempts (default: 3) | `5` |

### Examples

#### Download from multiple builds and platforms:
```bash
python3 scripts/fetch_latest_commits.py \
  --base-url "https://xcoartifactory.xilinx.com/native/vai-rt-ipu-prod-local/com/amd/onnx-rt/stx/cp_dev" \
  --builds 3025 3026 3027 \
  --platforms windows linux arm \
  --out artifact-compare/data
```

#### Using Basic authentication:
```bash
python3 scripts/fetch_latest_commits.py \
  --base-url "https://xcoartifactory.xilinx.com/native/vai-rt-ipu-prod-local/com/amd/onnx-rt/stx/cp_dev" \
  --builds 3025 3026 \
  --platforms windows linux \
  --user myuser \
  --password "mypassword" \
  --out data/builds
```

#### Single build, multiple platforms:
```bash
python3 scripts/fetch_latest_commits.py \
  --base-url "https://xcoartifactory.xilinx.com/native/vai-rt-ipu-prod-local/com/amd/onnx-rt/stx/cp_dev" \
  --builds 3025 \
  --platforms windows linux arm \
  --out data
```

## Output Structure

The script creates the following directory structure:

```
data/
├── 3025/
│   ├── windows/
│   │   ├── latest_commits.txt
│   │   └── meta.json
│   ├── linux/
│   │   ├── latest_commits.txt
│   │   └── meta.json
│   └── arm/
│       ├── latest_commits.txt
│       └── meta.json
├── 3026/
│   ├── windows/
│   │   ├── latest_commits.txt
│   │   └── meta.json
│   └── ...
└── fetch_errors.json (if any errors occurred)
```

### Metadata Files

Each successful download creates a `meta.json` file containing:
- Build ID
- Platform name
- Fetch timestamp (IST timezone)
- Source URL

Example `meta.json`:
```json
{
  "build": "3025",
  "platform": "windows",
  "fetched_at": "2025-09-26T14:30:45+05:30",
  "source_url": "https://xcoartifactory.xilinx.com/.../3025/windows/latest_commits.txt"
}
```

## Error Handling

- **Authentication Errors (401/403)**: Script exits immediately with clear error message
- **Network/Server Errors**: Automatic retry with exponential backoff
- **Partial Failures**: Continues processing other builds/platforms, saves errors to `fetch_errors.json`

## Exit Codes

- `0`: Success - all files downloaded successfully
- `2`: Partial or complete failure - check `fetch_errors.json` for details

## Project Structure

```
artifact-compare/
├── README.md
├── scripts/
│   └── fetch_latest_commits.py
├── config/
└── data/ (created by script)
```

## Troubleshooting

### Common Issues

1. **Missing requests library**
   ```bash
   pip install requests
   ```

2. **Authentication failures**
   - Verify your `ARTIFACTORY_TOKEN` is set correctly
   - Check token permissions for the specified repository
   - Ensure the base URL is accessible

3. **Network timeouts**
   - Increase retry attempts: `--retries 5`
   - Check network connectivity to Artifactory server

4. **File not found (404 errors)**
   - Verify build IDs exist in the repository
   - Check platform names are correct
   - Ensure the base URL path is accurate

### Debug Tips

- The script provides verbose output showing each fetch attempt
- Check `fetch_errors.json` for detailed error information
- Verify URLs manually in a browser when troubleshooting

## License

[Add your license information here]

## Contributing

[Add contribution guidelines here]
