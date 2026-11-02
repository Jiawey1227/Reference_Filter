# Windows distribution layer

For end-user download, installation, launch and exit instructions, see the [main README in this branch](../README.md).

First verified Windows build: [Actions run 41381760136](https://github.com/Jiawey1227/Reference_Filter/actions/runs/41381760136). Download the artifact at the bottom of the run page while signed in to GitHub. Artifacts expire; formal Releases have not yet been published.

This branch adds packaging only. Application source matches main at c184e31.

Push to `distribution` to build on a Windows GitHub Actions runner. Download the
`AuthorScopeScreening-Windows-x64` artifact from the completed workflow. It contains
a portable ZIP and a per-user installer with desktop and Start menu shortcuts.

The build runs existing unit tests and launches the frozen executable in smoke-test
mode to verify its static UI, API, and credential-backend availability. It does not
use an API key or contact the model service.

Before public release, test on a clean Windows PC: first launch, browser UI, saving
and forgetting a key, real screening and continuation, green affiliation cells,
download, second launch, exit during a task, restart, installer upgrade/uninstall.
The installer leaves user data and Windows Credential Manager entries untouched.

The packages are unsigned test builds. Code signing and automatic updates are not
configured. Publish validated packages as GitHub Release assets; do not commit
executables to the source branch. Bump AppVersion in installer.iss for each release.

Local build on Windows with Python 3.12 and Node.js 24:

```powershell
powershell -ExecutionPolicy Bypass -File distribution/build.ps1
```

Install Inno Setup 6 and compile distribution/installer.iss for the installation
package. The application requires neither Python nor Node.js on the end user's PC.
