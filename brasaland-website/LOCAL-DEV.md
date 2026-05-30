# Local Development (Codespaces & Local)

## Quick Start (Recommended)

You can run the Brasaland website locally using a simple command with [npx](https://www.npmjs.com/package/npx), which works in Codespaces and most local environments with Node.js installed.

### 1. Start a Local Server

From the project root, run:

```
npx serve brasaland-website -l 8080
```

- This uses the popular `serve` package to serve static files from the `brasaland-website` directory on port 8080.
- Open http://localhost:8080 in your browser to view the site.
- No global install required; `npx` will fetch the package if not present.

### 2. Alternative: Python (if Node.js is not available)

```
python3 -m http.server 8080 --directory brasaland-website
```

---

## Requirements
- Node.js (for npx) or Python 3 (for the alternative)
- No build step required; all files are static and ready to serve

## Codespaces Compatibility
- Both commands work in GitHub Codespaces out of the box.
- You can preview the running site using the Codespaces port forwarding feature.

---

For more details, see the main README or contact the project maintainer.
