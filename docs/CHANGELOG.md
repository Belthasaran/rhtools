# RHTools Changelog

## 2025-10-13

### Features

**Launch Program Browse and Drag-Drop Support**
- Added Browse button for Launch Program setting (matching FLIPS executable UI pattern)
- Added drag-and-drop zone for Launch Program setting
- Displays current path below controls when Launch Program is set
- Supports common executable extensions (.exe, .sh, .bat, .cmd)
- Files modified: `electron/renderer/src/App.vue`, `electron/GUI_README.md`

**attachblobs.js --newonly Option**
- Added `--newonly` command line option to skip patchblobs where file_name already exists in attachments table
- Significantly speeds up incremental processing (~20x faster for mostly-existing files)
- Added comprehensive test suite in `tests/test_attachblobs.js`
- Added `--help` option to display usage information
- Files modified: `attachblobs.js`
- See: `tests/README_ATTACHBLOBS_TESTS.md`

### Bug Fixes

**Settings File Paths Not Being Saved/Loaded**
- Fixed issue where `vanillaRomPath` in database wasn't being used when staging runs
- Added file path properties to settings object (vanillaRomPath, flipsPath, asarPath, uberAsmPath)
- Implemented Browse button functionality for all file settings with native file dialog
- Implemented drag/drop file handling for ROM, FLIPS, ASAR, and UberASM files
- Added file validation via IPC (SHA-224 hash check for ROM, executable check for tools)
- Settings dialog now displays currently configured file paths
- Fixed stageRunGames() to use correct property name (vanillaRomPath instead of romPath)
- Files modified: `electron/renderer/src/App.vue`, `electron/ipc-handlers.js`, `electron/preload.js`
- See: `docs/BUGFIX_settings_file_paths.md`

