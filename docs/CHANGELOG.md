# RHTools Changelog

## 2025-10-13

### Features

**USB2SNES Multi-Library Support**
- Added USB2SNES implementation library selector with 4 options:
  - usb2snes_a (Type A - Python port) - Primary implementation
  - usb2snes_b (Type B - 3rd party JS) - Alternative implementation
  - qusb2snes (Local server) - For QUsb2snes compatibility
  - node-usb (Direct hardware) - Direct USB hardware communication
- Added "Default usb2snes library" setting in Settings dialog (above USB2snes Websocket address)
- Enhanced USB2SNES Tools modal with:
  - Library implementation selector dropdown (disabled when connected)
  - Warning message when attempting to change library while connected
  - Connect/Disconnect button functionality (replaces Test Connection)
  - Expanded connection status display with firmware version, version string, and ROM running
  - Visual connection state indicator (connected/disconnected)
  - Proper connection state management (must disconnect before changing library)
- Library selection persists across sessions and initializes from settings default
- Unimplemented libraries show "not implemented" error when attempting to connect
- Files modified: `electron/renderer/src/App.vue`

**SNESWrapper Unified Interface Architecture**
- Created `SNESWrapper` module as unified interface for all USB2SNES implementations (Strategy Pattern)
- Created `BaseUsb2snes` abstract base class defining common interface for all implementations
- Implemented `usb2snesTypeA` (partial) - JavaScript port of py2snes Python library
  - Core connection methods: connect, disconnect, DeviceList, Attach, Info, Name
  - Console control: Boot, Menu, Reset
  - Memory operations: GetAddress (read), PutAddress (write - basic)
  - Pending: File operations (PutFile, List, MakeDir, Remove), SD2SNES special handling
- Added USB2SNES IPC handlers in `electron/ipc-handlers.js` using SNESWrapper singleton
- Exposed USB2SNES APIs in `electron/preload.js` for renderer process
- All application code now uses SNESWrapper exclusively - no direct implementation access
- Prevents implementation switching while connected for safety
- Comprehensive error handling and logging
- Files created:
  - `electron/main/usb2snes/BaseUsb2snes.js` - Abstract interface
  - `electron/main/usb2snes/SNESWrapper.js` - Unified wrapper
  - `electron/main/usb2snes/usb2snesTypeA.js` - Type A implementation
- Files modified:
  - `electron/ipc-handlers.js` - Added USB2SNES handlers
  - `electron/preload.js` - Added USB2SNES APIs
- See: `devdocs/SNESWRAPPER_ARCHITECTURE.md` for architecture documentation
- See: `devdocs/USB2SNES_IMPLEMENTATION_PLAN.md` for complete implementation roadmap

**UI Reorganization with Dropdown Menus**
- Reorganized toolbar buttons for cleaner, more organized interface
- Added "Select" dropdown button (with down arrow) containing:
  - Check all
  - Uncheck all
  - Check random
- Added "Ignore" dropdown button (with down arrow) containing:
  - Hide checked
  - Unhide checked
- Added conditional "USB2SNES Tools" button that appears next to "Open Settings" when USB2SNES is enabled
- Added USB2SNES Tools modal dialog with diagnostics and tools:
  - Connection status display (connected/disconnected indicator)
  - WebSocket address and device information
  - Upload settings display
  - Connection testing functionality
  - Diagnostic information (last connection attempt, error logs)
  - Quick actions (reset connection, open USB2SNES website)
- Dropdown menus close on Escape key or clicking outside
- Files modified: `electron/renderer/src/App.vue`

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

