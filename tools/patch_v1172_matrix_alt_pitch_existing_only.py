from pathlib import Path

header_path = Path("Source/PluginEditor.h")
cpp_path = Path("Source/PluginEditor.cpp")

if not header_path.exists():
    raise SystemExit("ERROR: Source/PluginEditor.h not found")

if not cpp_path.exists():
    raise SystemExit("ERROR: Source/PluginEditor.cpp not found")

header = header_path.read_text(encoding="utf-8")
cpp = cpp_path.read_text(encoding="utf-8")


# -----------------------------------------------------------------------------
# 1. Add MatrixEditDragMode enum/state to PluginEditor.h
# -----------------------------------------------------------------------------

old_header_state = '''    bool isDraggingPatternStepEdit = false;
    bool dragPaintValue = true;
    int lastEditedPattern = -1;
    int lastEditedStep = -1;
'''

new_header_state = '''    enum class MatrixEditDragMode
    {
        None,
        PaintOrErase,
        PitchExistingOnly
    };

    MatrixEditDragMode matrixEditDragMode = MatrixEditDragMode::None;

    bool isDraggingPatternStepEdit = false;
    bool dragPaintValue = true;
    int lastEditedPattern = -1;
    int lastEditedStep = -1;
'''

if old_header_state not in header:
    if "enum class MatrixEditDragMode" in header and "PitchExistingOnly" in header:
        print("MatrixEditDragMode already appears present in header; continuing.")
    else:
        raise SystemExit("ERROR: Could not patch PluginEditor.h Matrix drag mode state")
else:
    header = header.replace(old_header_state, new_header_state, 1)
    header_path.write_text(header, encoding="utf-8")


# -----------------------------------------------------------------------------
# 2. Patch Matrix mouseDown branch to select Alt pitch mode
# -----------------------------------------------------------------------------

old_mouse_down = '''        const bool rightClickErase = event.mods.isRightButtonDown();

        // Matrix mode is now paint/edit oriented:
        // - Left click always creates/keeps a note and applies pitch from mouse Y.
        // - Right click is the dedicated erase gesture.
        dragPaintValue = !rightClickErase;
        isDraggingPatternStepEdit = true;

        setPatternStepValue(patternIndex, stepIndex, dragPaintValue);

        if (dragPaintValue)
            setMatrixStepPitchAtMousePosition(position);

        return;
'''

new_mouse_down = '''        const bool rightClickErase = event.mods.isRightButtonDown();
        const bool altDown = event.mods.isAltDown();

        // Matrix mode is paint/edit oriented:
        // - Left click creates/keeps a note and applies pitch from mouse Y.
        // - Right click is the dedicated erase gesture.
        // - Alt click/drag pitch-paints existing notes only.
        matrixEditDragMode = altDown && !rightClickErase
            ? MatrixEditDragMode::PitchExistingOnly
            : MatrixEditDragMode::PaintOrErase;

        dragPaintValue = !rightClickErase;
        isDraggingPatternStepEdit = true;

        if (matrixEditDragMode == MatrixEditDragMode::PitchExistingOnly)
        {
            setMatrixStepPitchAtMousePosition(position);
        }
        else
        {
            setPatternStepValue(patternIndex, stepIndex, dragPaintValue);

            if (dragPaintValue)
                setMatrixStepPitchAtMousePosition(position);
        }

        return;
'''

if old_mouse_down not in cpp:
    if "MatrixEditDragMode::PitchExistingOnly" in cpp:
        print("Matrix mouseDown Alt mode already appears patched; continuing.")
    else:
        raise SystemExit("ERROR: Could not patch Matrix mouseDown for Alt pitch mode")
else:
    cpp = cpp.replace(old_mouse_down, new_mouse_down, 1)


# -----------------------------------------------------------------------------
# 3. Patch Matrix mouseDrag branch to dispatch by Matrix drag mode
# -----------------------------------------------------------------------------

old_mouse_drag = '''    if (!isDraggingPatternStepEdit)
        return;

    setStepAtMousePosition(event.getPosition(), dragPaintValue);
}
'''

new_mouse_drag = '''    if (!isDraggingPatternStepEdit)
        return;

    if (matrixEditDragMode == MatrixEditDragMode::PitchExistingOnly)
    {
        setMatrixStepPitchAtMousePosition(event.getPosition());
        return;
    }

    setStepAtMousePosition(event.getPosition(), dragPaintValue);
}
'''

if old_mouse_drag not in cpp:
    if "matrixEditDragMode == MatrixEditDragMode::PitchExistingOnly" in cpp:
        print("Matrix mouseDrag Alt dispatch already appears patched; continuing.")
    else:
        raise SystemExit("ERROR: Could not patch Matrix mouseDrag for Alt pitch mode")
else:
    cpp = cpp.replace(old_mouse_drag, new_mouse_drag, 1)


# -----------------------------------------------------------------------------
# 4. Reset Matrix drag mode on mouseDown entry and mouseUp
# -----------------------------------------------------------------------------

old_mouse_down_reset = '''    lastEditedPattern = -1;
    lastEditedStep = -1;

    if (audioProcessor.isMelodyPaintMode())
'''

new_mouse_down_reset = '''    lastEditedPattern = -1;
    lastEditedStep = -1;
    matrixEditDragMode = MatrixEditDragMode::None;

    if (audioProcessor.isMelodyPaintMode())
'''

if old_mouse_down_reset not in cpp:
    if "matrixEditDragMode = MatrixEditDragMode::None;" in cpp:
        print("mouseDown Matrix mode reset already appears present; continuing.")
    else:
        raise SystemExit("ERROR: Could not patch mouseDown Matrix drag mode reset")
else:
    cpp = cpp.replace(old_mouse_down_reset, new_mouse_down_reset, 1)


old_mouse_up_reset = '''    isDraggingPatternStepEdit = false;
    isDraggingMelodyDuration = false;
    melodyEditDragMode = MelodyEditDragMode::None;
'''

new_mouse_up_reset = '''    isDraggingPatternStepEdit = false;
    matrixEditDragMode = MatrixEditDragMode::None;
    isDraggingMelodyDuration = false;
    melodyEditDragMode = MelodyEditDragMode::None;
'''

if old_mouse_up_reset not in cpp:
    if "matrixEditDragMode = MatrixEditDragMode::None;" in cpp:
        print("mouseUp Matrix mode reset already appears present; continuing.")
    else:
        raise SystemExit("ERROR: Could not patch mouseUp Matrix drag mode reset")
else:
    cpp = cpp.replace(old_mouse_up_reset, new_mouse_up_reset, 1)


cpp_path.write_text(cpp, encoding="utf-8")

print("v1.17.2 applied: Matrix Alt-drag pitch-paints existing notes only.")
