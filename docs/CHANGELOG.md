# RHTools Changelog

## 2025-10-13

### Features

**Advanced Search/Filter System**
- Added "Search/Filters" dropdown button next to "Open Settings" with down arrow indicator
- Moved search textbox and Clear filters button into dropdown dialog for cleaner UI
- Added visual indicator on button when filters are active (blue highlight + dot indicator)
- Implemented keyboard shortcut: Press `/` key to instantly open filters and focus search
- Added clickable common filter tags below search box:
  - Game types: Kaizo, Standard, Puzzle, Troll, Vanilla
  - Time-based: Added: 2025, Added: 2024
  - Rating filters: Rating > 3, Rating: 5, Rating: 4
- Implemented advanced attribute search syntax: `<attribute>:<value>`
  - Examples: `added:2025`, `author:FuSoYa`, `name:Cave`
- Implemented comparison operators for ratings: `rating:5`, `rating:>3`, `rating:<4`, `rating:>=3`, `rating:<=4`
- Version filtering support: `version:1` (specific), `version:*` (all versions) - placeholder for future enhancement
- Searches JSON data attributes (added, difficulty, etc.) in addition to standard fields
- Dropdown closes on Escape key or clicking outside
- Built-in filter syntax help guide in collapsible section
- Files modified: `electron/renderer/src/App.vue`

**Theme and Text Size Customization**
- Added comprehensive theming system with 4 theme options:
  - Light Theme (default)
  - Dark (dark theme)
  - Onyx (Black & Gray with white text)
  - Ash (Mid-Gray with white text)
- Added Text Size control with 4 size options (Small, Medium, Large, Extra Large)
- Theme setting appears as first option in Settings panel for easy access
- Text Size setting with interactive slider appears below Theme setting
- Themes apply dynamically from Settings panel without requiring restart
- Created centralized theme configuration file (`themeConfig.ts`) with `DEFAULT_THEME` constant for easy default theme changes
- Implemented CSS custom properties (CSS variables) for dynamic theming
- Theme and text size preferences saved to database and persist across sessions
- Custom scrollbar styling that adapts to each theme (darker scrollbars for dark themes blend better with UI)
- Modal dialogs now have solid contrasting borders to clearly define dialog boundaries
- Files created: `electron/renderer/src/themeConfig.ts`
- Files modified: `electron/renderer/src/App.vue`

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

