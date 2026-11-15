# Security Policy

## Supported Versions

Only the latest major release of **STOIQO Node Suite** receives active security updates and vulnerability patches.

| Version | Supported          |
| ------- | ------------------ |
| 2.x     | :white_check_mark: |
| 1.x     | :x:                |
| < 1.0   | :x:                |

---

## Reporting a Vulnerability

The STOIQO engineering team takes the security of AI pipelines and local runtime environments seriously.

If you discover a security vulnerability (such as arbitrary code execution, path traversal in image/model loading, or network injection via API endpoints):

1. **Do not create a public GitHub issue**: Disclosing vulnerabilities publicly puts users at risk before a fix is available.
2. **Submit a Private Security Advisory**: Use the [GitHub Security Advisory](https://github.com/ALIENHAZEtv/STOIQO_Node_Suite/security/advisories/new) feature on the repository.
3. **Include Detailed Steps**:
   * A clear description of the vulnerability.
   * Reproduction steps or a minimal workflow JSON proof of concept.
   * Affected operating systems, ComfyUI versions, or node configurations.
   * Potential impact on the host system.

---

## Security Best Practices for Users

* **Model File Paths**: Always verify that custom model paths loaded via `Universal Model Loader` point to trusted local directories or valid HuggingFace cache snapshots.
* **Network Endpoints**: When using remote API endpoints (e.g. Ollama, LM Studio, vLLM) in `Universal Model Loader` or `Prompt Generator`, ensure your firewall restricts access to trusted origins.
* **Safe Tensors**: Prefer `.safetensors` model weights over pickled `.ckpt` or `.pt` files to avoid arbitrary Python code execution during weight deserialization.
