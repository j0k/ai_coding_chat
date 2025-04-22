# AI Coding Chat - Changelog

In nearest future:
- Session Manager with Multiple Sessions
- AI Flow Promts

Big Milestone:
- Git connect
- AI Promting Diagrams


## [1.2.1] - 2025-04-23

### Fixed
- **Navigation Panel**:
  - Messages now properly appear after sending
  - Click navigation jumps to correct message positions
  - Execution time badges show consistently
- **Message Handling**:
  - Fixed parent-child message relationships
  - Proper UUID tracking for all messages
- **UI Controls**:
  - Send button state management (enable/disable)
  - Context menu persistence
- **Session Management**:
  - Saved sessions now maintain all message metadata
  - Fixed loading of execution times

## [1.2.0] - 2025-04-22

### Added
- **Command Execution Panel** in memo area:
  - Predefined commands (`tree -L 2`, `listfiles.py`)
  - Editable command input
  - Real-time output display
  - Threaded execution to prevent UI freezing
- **Enhanced Navigation**:
  - Click-to-jump message navigation
  - Temporary message highlighting
  - Precise scroll positioning
- **Improved Panel Toggling**:
  - Complete collapse of memo panel (shows only toggle button)
  - Smooth width transitions
  - Persistent content between toggles

### Changed
- **UI Architecture**:
  - Non-blocking message processing queue
  - Thread-safe API client improvements
  - Better state management
- **License Terms**:
  - Updated to MIT with Attribution
  - Added AI generation disclosure clause

### Fixed
- Copy-to-chat functionality reliability
- Panel toggle button persistence
- Command execution error handling
- Memory leaks in message navigation

# AI Coding Chat Client - Version 1.1

## Recent Improvements

### Enhanced User Interface
- **New Collapsible Memo Panel** 📝  
  - Right-side editor for prompt crafting and notes
  - Toggleable interface (300px ↔ 30px)
  - Direct "Copy to Chat" button integration
  - Persistent content storage during session

### Performance Upgrades
- **Non-blocking UI Architecture** ⚡
  - Background thread API processing
  - Message queue system for smooth UI updates
  - Responsive during long operations
  - Automatic request timeout handling (15s/30s)

### Improved Interaction
- **Smart Send Button States**  
  - Disables during processing
  - Visual progress indicators
  - Prevention of duplicate requests
  - Auto-focus on chat input after copy

### Technical Enhancements
- **Thread-safe API Client**  
  - Request locking mechanism
  - Better error differentiation
  - Structured response validation
  - Connection pooling support

## Updated Feature Highlights

### Core Functionality
- **Enhanced API Communication**  
  - Timeout controls (15s/30s toggle)
  - Automatic retry foundation
  - Request/Response logging
  - Adaptive payload construction

### Conversation Management
- **Real-time Context Updates**  
  - Instant UI feedback
  - Background saving
  - Versioned history tracking
  - Session integrity checks

## Technical Specifications Updates

### New Requirements
- Python 3.8+ with threading support
- Queue module integration
- Platform-independent locking

### Architecture Changes
- Added Message Queue System
- Thread Worker Pool
- UI State Machine
- Event-driven Updates

## Usage Recommendations
1. Use memo panel for:
   - Prompt drafting
   - Code snippets
   - API parameters
   - Error logs

2. During long operations:
   - Continue editing prompts
   - Browse history
   - Adjust settings
