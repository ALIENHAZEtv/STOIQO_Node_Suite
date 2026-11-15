## Description

Briefly describe the change and why it is needed. Link to relevant issues if applicable.

---

## Architectural Checklist

Please ensure your contribution satisfies the following requirements:

- [ ] **21 Sovereign Nodes Invariant**: Does this change respect the 21 sovereign node boundaries?
- [ ] **Backward Compatibility**: If modifying existing node inputs or signatures, have legacy aliases or default fallback arguments been maintained?
- [ ] **Sovereign Saver Invariant**: Do saver nodes maintain `sidecar_metadata: "None"` by default, embedding metadata directly into the media container?
- [ ] **Tests Pass**: Have you run the pytest suite (`pytest tests/ -v`) and confirmed 100% pass?
- [ ] **Frontend Synchronization**: If `src_js/` was modified, did you run `npm run build` and verify with `npm run check:bundle`?
- [ ] **No Local Clutter**: Confirm no temporary output images, `.pytest_cache`, `.ruff_cache`, or `node_modules` are included.

---

## Testing Performed

Describe the tests and manual verification steps performed in ComfyUI:
1. ...
2. ...
