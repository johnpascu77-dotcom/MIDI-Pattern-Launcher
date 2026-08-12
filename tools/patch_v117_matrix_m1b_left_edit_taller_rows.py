from pathlib import Path

cpp_path = Path("Source/PluginEditor.cpp")

if not cpp_path.exists():
    raise SystemExit("ERROR: Source/PluginEditor.cpp not found")

cpp = cpp_path.read_text(encoding="utf-8")


# -----------------------------------------------------------------------------
# 1. Matrix left-click behavior:
#
# Old:
#   left-click inactive = add
#   left-click active   = delete
#   right-click         = delete
#
# New:
#   left-click inactive = add/pitch
#   left-click active   = select/pitch, keep note
#   right-click         = delete
# -----------------------------------------------------------------------------

old_mouse_down_matrix = '''        const bool rightClickErase = event.mods.isRightButtonDown();
        const bool currentlyHasNote = audioProcessor.stepHasNote(patternIndex, stepIndex);

        dragPaintValue = rightClickErase ? false : !currentlyHasNote;
        isDraggingPatternStepEdit = true;

        setPatternStepValue(patternIndex, stepIndex, dragPaintValue);

        if (dragPaintValue)
            setMatrixStepPitchAtMousePosition(position);

        return;
'''

new_mouse_down_matrix = '''        const bool rightClickErase = event.mods.isRightButtonDown();

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

if old_mouse_down_matrix not in cpp:
    if "dragPaintValue = !rightClickErase;" in cpp:
        print("Matrix mouseDown behavior already appears patched; continuing.")
    else:
        raise SystemExit("ERROR: Could not patch Matrix mouseDown left/right behavior")
else:
    cpp = cpp.replace(old_mouse_down_matrix, new_mouse_down_matrix, 1)


# -----------------------------------------------------------------------------
# 2. Increase Matrix row/cell height from 42 to 64.
#
# These three locations are:
# - getPatternStepBox()
# - updateSelectedStepFromMousePosition()
# - Matrix paint branch
# -----------------------------------------------------------------------------

old_row_height = "    const int rowHeight = 42;\n"
new_row_height = "    const int rowHeight = 64;\n"

count = cpp.count(old_row_height)

if count == 0:
    if "    const int rowHeight = 64;\n" in cpp:
        print("Matrix row height already appears patched to 64; continuing.")
    else:
        raise SystemExit("ERROR: Could not find any Matrix rowHeight = 42 declarations")
else:
    cpp = cpp.replace(old_row_height, new_row_height)
    print(f"Updated {count} rowHeight declaration(s) from 42 to 64.")


cpp_path.write_text(cpp, encoding="utf-8")

print("v1.17.0 Matrix Patch M1b applied: left-click edits/paints, right-click erases, taller Matrix rows.")
