# RHTools Changelog

## 2025-10-13

### Features

**Quick Launch Feature (Start Button)**
- Implemented "Start" button functionality to stage and launch games directly without creating a run
- Allows selection of 1-21 games at a time for quick launching
- Added Quick Launch staging process that creates `smw<GAMEID>_<VERSION>.sfc` and `md<GAMEID>_<VERSION>.json` files
- Files staged in `<temp_base>/RHTools-QuickLaunch/` directory
- Added progress modal showing real-time staging progress
- Added success modal with folder path, launch instructions, and "Open Folder" button
- Added temporary directory override setting in Settings dialog (optional custom base path for temp directories)
- Added path validation for temporary directory override
- Files modified: `electron/renderer/src/App.vue`, `electron/game-stager.js`, `electron/ipc-handlers.js`, `electron/preload.js`
- See: `docs/QUICK_LAUNCH_FEATURE.md`

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

