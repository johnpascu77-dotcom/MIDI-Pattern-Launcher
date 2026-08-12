from pathlib import Path

cpp_path = Path("Source/PluginEditor.cpp")

if not cpp_path.exists():
    raise SystemExit("ERROR: Source/PluginEditor.cpp not found")

cpp = cpp_path.read_text(encoding="utf-8")


old_block = '''        if (shiftDown && !rightClickErase && audioProcessor.stepHasNote(patternIndex, stepIndex))
            matrixEditDragMode = MatrixEditDragMode::MoveExistingStep;
        else if (ctrlDown && !rightClickErase)
            matrixEditDragMode = MatrixEditDragMode::VelocityExistingOnly;
        else if (altDown && !rightClickErase)
            matrixEditDragMode = MatrixEditDragMode::PitchExistingOnly;
        else
            matrixEditDragMode = MatrixEditDragMode::PaintOrErase;

        dragPaintValue = !rightClickErase;
        isDraggingPatternStepEdit = true;

        if (matrixEditDragMode == MatrixEditDragMode::MoveExistingStep)
'''

new_block = '''        if (shiftDown && !rightClickErase && !audioProcessor.stepHasNote(patternIndex, stepIndex))
        {
            matrixEditDragMode = MatrixEditDragMode::None;
            isDraggingPatternStepEdit = false;
            return;
        }

        if (shiftDown && !rightClickErase && audioProcessor.stepHasNote(patternIndex, stepIndex))
            matrixEditDragMode = MatrixEditDragMode::MoveExistingStep;
        else if (ctrlDown && !rightClickErase)
            matrixEditDragMode = MatrixEditDragMode::VelocityExistingOnly;
        else if (altDown && !rightClickErase)
            matrixEditDragMode = MatrixEditDragMode::PitchExistingOnly;
        else
            matrixEditDragMode = MatrixEditDragMode::PaintOrErase;

        dragPaintValue = !rightClickErase;
        isDraggingPatternStepEdit = true;

        if (matrixEditDragMode == MatrixEditDragMode::MoveExistingStep)
'''

if old_block not in cpp:
    if "shiftDown && !rightClickErase && !audioProcessor.stepHasNote(patternIndex, stepIndex)" in cpp:
        print("Strict Shift-empty behavior already appears present; continuing.")
    else:
        raise SystemExit("ERROR: Could not find Matrix mode selection block")
else:
    cpp = cpp.replace(old_block, new_block, 1)


# Optional version suffix.
if '"v1.17.5 - Matrix Step Move"' in cpp:
    cpp = cpp.replace('"v1.17.5 - Matrix Step Move"', '"v1.17.5b - Matrix Step Move"', 1)
elif '"v1.17.5b - Matrix Step Move"' in cpp:
    print("Version text already appears updated to v1.17.5b; continuing.")
else:
    print("WARNING: Could not find v1.17.5 version text; version label not updated.")


cpp_path.write_text(cpp, encoding="utf-8")

print("v1.17.5b applied: Shift on empty Matrix cells now does nothing.")
