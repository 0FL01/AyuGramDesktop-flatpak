# AyuGramDesktop - Flatpak Fork

Fork of AyuGramDesktop for building Flatpak packages. Based on Telegram Desktop.

Tech stack: C++17, Qt 6, CMake 3.25+, MTProto

## Branch
Default branch: `dev`

## Workspace Overview

```
Telegram/SourceFiles/    - Main application code
Telegram/lib_*/           - Core libraries (base, ui, tl, storage, etc.)
Telegram/SourceFiles/ayu/ - AyuGram-specific modifications
Telegram/cmake/           - CMake build helpers
cmake/                    - Root CMake configuration
lib/                      - External libs (xdg)
docs/                     - Build guides
```

## Key Subsystems

### AyuGram Core (`SourceFiles/ayu/`)
- **ayu_settings.h** - All AyuGram preferences (ghost mode, streamer mode, UI tweaks)
- **ayu_worker.h** - Background tasks and URL handlers
- **ayu_infra.h** - Cross-cutting AyuGram utilities
- `data/` - SQLite storage for deleted messages, message history
- `features/` - Feature implementations:
  - `streamer_mode/` - Streamer mode ( hides "seen by" indicators)
  - `messageshot/` - Message screenshot notifications
  - `forward/` - Enhanced forwarding with sync
- `ui/` - AyuGram UI components:
  - `boxes/` - Dialog boxes (font selector, theme selector, mark editor)
  - `settings/` - Settings page integration
  - `components/` - Custom UI components
  - `context_menu/` - Extended context menus

### Telegram Core (`SourceFiles/`)
- **main.cpp** - Entry point
- **api/** - Telegram API wrappers (100+ files)
- **mtproto/** - MTProto protocol implementation
- **core/** - Application lifecycle, settings, crash handling
- **data/** - Data models (users, chats, messages, etc.)
- **history/** - Message history rendering and management
- **dialogs/** - Chat list/dialogs
- **boxes/** - UI dialog boxes
- **ui/** - Base UI components and styles
- **platform/** - Platform-specific code (linux/, mac/, win/)
- **chat_helpers/** - Compose field, emoji, stickers

### Libraries (`Telegram/lib_*/`)
- **lib_base** - Core utilities, threading, serialization
- **lib_ui** - UI framework, widgets, painting
- **lib_tl** - TL schema and type definitions
- **lib_storage** - Local SQLite database
- **lib_lottie** - Lottie animation support
- **lib_rpl** - Reactive programming library
- **lib_crl** - Coroutine library
- **lib_webview** - WebView integration
- **lib_webrtc** - WebRTC calls

## AyuGram Settings Structure

All settings in `ayu_settings.h` use JSON serialization via nlohmann/json:

- **Ghost Mode**: `sendReadMessages`, `sendReadStories`, `sendOnlinePackets`
- **UI Customization**: `wideMultiplier`, `appIcon`, `monoFont`, `showPeerId`
- **Content Filtering**: `disableAds`, `disableStories`, `hideSimilarChannels`
- **Message Actions**: `saveDeletedMessages`, `saveMessagesHistory`
- **Context Menu**: `showReactionsPanelInContextMenu`, `showHideMessageInContextMenu`
- **Premium Features**: `localPremium`, `spoofWebviewAsAndroid`

Settings access via `AyuSettings::getInstance()` with reactive producers.

## Where To Look

| Need to... | Look in |
|------------|---------|
| Modify settings UI | `ayu/ui/settings/settings_ayu.cpp` |
| Add new setting | `ayu/ayu_settings.h` + `ayu/ayu_settings.cpp` |
| Ghost mode logic | `ayu/ayu_worker.cpp`, `ayu/ayu_infra.cpp` |
| Message history hooks | `ayu/data/messages_storage.cpp` |
| Streamer mode | `ayu/features/streamer_mode/streamer_mode.h` |
| Build flatpak | `docs/building-flatpak.md` |
| Windows build | `docs/building-win-x64.md` |
| Linux build | `docs/building-linux.md` |

## Development Workflow

### Build (Linux/Docker)
```bash
./Telegram/build/prepare/linux.sh
docker run --rm -it \
    -u $(id -u) \
    -v "$PWD:/usr/src/tdesktop" \
    ghcr.io/telegramdesktop/tdesktop/centos_env:latest \
    /usr/src/tdesktop/Telegram/build/docker/centos_env/build.sh
```

### Build Flatpak
```bash
flatpak-builder --user --install --force-clean build-dir com.ayugram.desktop.yml
```

### Build (Windows)
Requires VS Build Tools with C++ MFC, ATL, Windows 11 SDK. See `docs/building-win-x64.md`.

### CMake Structure
- Root: `CMakeLists.txt` (3.25+)
- Telegram: `Telegram/CMakeLists.txt`
- AyuGram files listed explicitly in `ayugram_files` variable (lines 97-178)
- When adding new AyuGram source files, add to this variable

## Architectural Invariants

1. **Threading**: Use `rpl::producer` for reactive updates (see `ayu_settings.h`)
2. **Settings Persistence**: JSON-based, loaded via `AyuSettings::load()`
3. **Database**: SQLite via sqlite_orm in `ayu/data/ayu_database.cpp`
4. **MTProto**: All server communication via `SourceFiles/api/` or `SourceFiles/mtproto/`
5. **UI Style**: Qt stylesheet-based, AyuGram styles in `ayu/ui/ayu_styles.style`
6. **Platform Code**: Separate implementations in `SourceFiles/platform/{linux,mac,win}/`

## Key Files Reference

| File | Purpose |
|------|---------|
| `ayu/ayu_settings.h` | AyuGram settings class definition |
| `ayu/ayu_worker.h` | Main AyuGram worker thread |
| `ayu/ui/settings/settings_ayu.h` | Settings page widget |
| `ayu/data/ayu_database.h` | Local SQLite storage |
| `SourceFiles/history/view/history_view_message.h` | Message rendering (often hooked) |
| `SourceFiles/api/api_views.h` | View counts API |
| `SourceFiles/data/data_session.h` | Session data manager |
