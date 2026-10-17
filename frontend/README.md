# React + TypeScript + Vite

## Cost Sheet Windows desktop client

The Tauri client starts with a Cost Sheet activation screen. It checks and activates
licenses through the shared license API on port `9686`, using the `costsheet`
product code. After activation it loads the same Cost Sheet web application served
at `http://100.51.165.76:28080`.

To build `CostSheet.exe` on Windows, install Node.js, Rust, Visual Studio Build
Tools with the C++ workload, and the WebView2 Runtime, then run:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\build-costsheet-desktop.ps1
```

The executable is written to `frontend\dist-desktop\CostSheet.exe`.

This template provides a minimal setup to get React working in Vite with HMR and some Oxlint rules.

Currently, two official plugins are available:

- [@vitejs/plugin-react](https://github.com/vitejs/vite-plugin-react/blob/main/packages/plugin-react) uses [Oxc](https://oxc.rs)
- [@vitejs/plugin-react-swc](https://github.com/vitejs/vite-plugin-react/blob/main/packages/plugin-react-swc) uses [SWC](https://swc.rs/)

## React Compiler

The React Compiler is not enabled on this template because of its impact on dev & build performances. To add it, see [this documentation](https://react.dev/learn/react-compiler/installation).

## Expanding the Oxlint configuration

If you are developing a production application, we recommend enabling type-aware lint rules by installing `oxlint-tsgolint` and editing `.oxlintrc.json`:

```json
{
  "$schema": "./node_modules/oxlint/configuration_schema.json",
  "plugins": ["react", "typescript", "oxc"],
  "options": {
    "typeAware": true
  },
  "rules": {
    "react/rules-of-hooks": "error",
    "react/only-export-components": ["warn", { "allowConstantExport": true }]
  }
}
```

See the [Oxlint rules documentation](https://oxc.rs/docs/guide/usage/linter/rules) for the full list of rules and categories.
