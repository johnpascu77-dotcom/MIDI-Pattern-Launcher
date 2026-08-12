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
# 1. Extend MatrixEditDragMode enum
# -----------------------------------------------------------------------------

old_enum = '''    enum class MatrixEditDragMode
    {
        None,
        PaintOrErase,
        PitchExistingOnly,
        VelocityExistingOnly
    };
'''

new_enum = '''    enum class MatrixEditDragMode
    {
        None,
        PaintOrErase,
        PitchExistingOnly,
        VelocityExistingOnly,
        MoveExistingStep
    };
'''

if old_enum not in header:
    if "MoveExistingStep" in header:
        print("MatrixEditDragMode already includes MoveExistingStep; continuing.")
    else:
        raise SystemExit("ERROR: Could not extend MatrixEditDragMode enum")
else:
    header = header.replace(old_enum, new_enum, 1)


# -----------------------------------------------------------------------------
# 2. Add Matrix move drag state
# -----------------------------------------------------------------------------

old_state = '''    bool isDraggingPatternStepEdit = false;
    bool dragPaintValue = true;
    int lastEditedPattern = -1;
    int lastEditedStep = -1;
'''

new_state = '''    bool isDraggingPatternStepEdit = false;
    bool dragPaintValue = true;
    int lastEditedPattern = -1;
    int lastEditedStep = -1;

    int matrixMoveSourcePattern = -1;
    int matrixMoveSourceStep = -1;
    int matrixMoveNote = 60;
    int matrixMoveVelocity = 100;
    int matrixMoveDuration = 1;
'''

if old_state not in header:
    if "matrixMoveSourcePattern" in header and "matrixMoveDuration" in header:
        print("Matrix move state already appears present; continuing.")
    else:
        raise SystemExit("ERROR: Could not add Matrix move drag state")
else:
    header = header.replace(old_state, new_state, 1)


# -----------------------------------------------------------------------------
# 3. Add helper declarations
# -----------------------------------------------------------------------------

old_decls = '''    int getMatrixVelocityForMousePosition(int patternIndex, int stepIndex, juce::Point<int> position) const;
    void setMatrixStepVelocityAtMousePosition(juce::Point<int> position);
    void setMelodyPaintCellValue(int stepIndex, int midiNote, bool shouldHaveNote);
'''

new_decls = '''    int getMatrixVelocityForMousePosition(int patternIndex, int stepIndex, juce::Point<int> position) const;
    void setMatrixStepVelocityAtMousePosition(juce::Point<int> position);
    void moveMatrixStepAtMousePosition(juce::Point<int> position);
    void setMelodyPaintCellValue(int stepIndex, int midiNote, bool shouldHaveNote);
'''

if old_decls not in header:
    if "moveMatrixStepAtMousePosition" in header:
        print("Matrix move helper declaration already appears present; continuing.")
    else:
        raise SystemExit("ERROR: Could not add Matrix move helper declaration")
else:
    header = header.replace(old_decls, new_decls, 1)


header_path.write_text(header, encoding="utf-8")


# -----------------------------------------------------------------------------
# 4. Add move helper definition after setMatrixStepVelocityAtMousePosition()
# -----------------------------------------------------------------------------

insert_after = '''void MidiPatternLauncherAudioProcessorEditor::setMatrixStepVelocityAtMousePosition(
    juce::Point<int> position)
{
    int patternIndex = -1;
    int stepIndex = -1;

    if (!getPatternStepAtPosition(position, patternIndex, stepIndex))
        return;

    const int gridStepCount = audioProcessor.getGridStepCount();

    if (patternIndex < 0 || patternIndex >= 3 || stepIndex < 0 || stepIndex >= gridStepCount)
        return;

    if (!audioProcessor.stepHasNote(patternIndex, stepIndex))
        return;

    const int midiNote = audioProcessor.getStepNote(patternIndex, stepIndex);
    const int velocity = getMatrixVelocityForMousePosition(patternIndex, stepIndex, position);
    const int duration = juce::jlimit(
        1,
        gridStepCount - stepIndex,
        audioProcessor.getStepDurationSteps(patternIndex, stepIndex));

    audioProcessor.setStepValues(
        patternIndex,
        stepIndex,
        midiNote,
        velocity,
        duration);

    selectedEditPattern = patternIndex;
    selectedStep = stepIndex;

    audioProcessor.setTargetPatternAndStep(selectedEditPattern, selectedStep);
    audioProcessor.updateTargetParametersFromStep();

    lastEditedPattern = patternIndex;
    lastEditedStep = stepIndex;

    updateEditPatternButtonHighlights();
    repaint();
}

'''

move_helper = r'''void MidiPatternLauncherAudioProcessorEditor::moveMatrixStepAtMousePosition(
    juce::Point<int> position)
{
    if (matrixMoveSourcePattern < 0 || matrixMoveSourcePattern >= 3)
        return;

    const int gridStepCount = audioProcessor.getGridStepCount();

    if (matrixMoveSourceStep < 0 || matrixMoveSourceStep >= gridStepCount)
        return;

    int targetPattern = -1;
    int targetStep = -1;

    if (!getPatternStepAtPosition(position, targetPattern, targetStep))
        return;

    if (targetPattern != matrixMoveSourcePattern)
        return;

    if (targetStep < 0 || targetStep >= gridStepCount)
        return;

    if (targetStep == matrixMoveSourceStep)
        return;

    if (targetPattern == lastEditedPattern && targetStep == lastEditedStep)
        return;

    if (audioProcessor.stepHasNote(targetPattern, targetStep))
        return;

    const int safeDuration = juce::jlimit(
        1,
        gridStepCount - targetStep,
        matrixMoveDuration);

    audioProcessor.setStepValues(
        targetPattern,
        targetStep,
        matrixMoveNote,
        matrixMoveVelocity,
        safeDuration);

    setPatternStepValue(matrixMoveSourcePattern, matrixMoveSourceStep, false);

    selectedEditPattern = targetPattern;
    selectedStep = targetStep;

    audioProcessor.setTargetPatternAndStep(selectedEditPattern, selectedStep);
    audioProcessor.updateTargetParametersFromStep();

    matrixMoveSourcePattern = targetPattern;
    matrixMoveSourceStep = targetStep;
    matrixMoveDuration = safeDuration;

    lastEditedPattern = targetPattern;
    lastEditedStep = targetStep;

    updateEditPatternButtonHighlights();
    repaint();
}

'''

if "void MidiPatternLauncherAudioProcessorEditor::moveMatrixStepAtMousePosition(" in cpp:
    print("Matrix move helper definition already appears present; continuing.")
else:
    if insert_after not in cpp:
        raise SystemExit("ERROR: Could not find insertion point after setMatrixStepVelocityAtMousePosition")

    cpp = cpp.replace(insert_after, insert_after + move_helper, 1)


# -----------------------------------------------------------------------------
# 5. Reset move state on mouseDown entry
# -----------------------------------------------------------------------------

old_mouse_down_reset = '''    lastEditedPattern = -1;
    lastEditedStep = -1;
    matrixEditDragMode = MatrixEditDragMode::None;

    if (audioProcessor.isMelodyPaintMode())
'''

new_mouse_down_reset = '''    lastEditedPattern = -1;
    lastEditedStep = -1;
    matrixEditDragMode = MatrixEditDragMode::None;
    matrixMoveSourcePattern = -1;
    matrixMoveSourceStep = -1;

    if (audioProcessor.isMelodyPaintMode())
'''

if old_mouse_down_reset not in cpp:
    if "matrixMoveSourcePattern = -1;" in cpp:
        print("mouseDown move state reset already appears present; continuing.")
    else:
        raise SystemExit("ERROR: Could not patch mouseDown move reset")
else:
    cpp = cpp.replace(old_mouse_down_reset, new_mouse_down_reset, 1)


# -----------------------------------------------------------------------------
# 6. Patch Matrix mouseDown mode selection
# -----------------------------------------------------------------------------

old_mouse_down_matrix = '''        const bool rightClickErase = event.mods.isRightButtonDown();
        const bool altDown = event.mods.isAltDown();
        const bool ctrlDown = event.mods.isCtrlDown();

        // Matrix mode is paint/edit oriented:
        // - Left click creates/keeps a note and applies pitch from mouse Y.
        // - Right click is the dedicated erase gesture.
        // - Alt click/drag pitch-paints existing notes only.
        // - Ctrl click/drag velocity-paints existing notes only.
        if (ctrlDown && !rightClickErase)
            matrixEditDragMode = MatrixEditDragMode::VelocityExistingOnly;
        else if (altDown && !rightClickErase)
            matrixEditDragMode = MatrixEditDragMode::PitchExistingOnly;
        else
            matrixEditDragMode = MatrixEditDragMode::PaintOrErase;

        dragPaintValue = !rightClickErase;
        isDraggingPatternStepEdit = true;

        if (matrixEditDragMode == MatrixEditDragMode::PitchExistingOnly)
        {
            setMatrixStepPitchAtMousePosition(position);
        }
        else if (matrixEditDragMode == MatrixEditDragMode::VelocityExistingOnly)
        {
            setMatrixStepVelocityAtMousePosition(position);
        }
        else
        {
            setPatternStepValue(patternIndex, stepIndex, dragPaintValue);

            if (dragPaintValue)
                setMatrixStepPitchAtMousePosition(position);
        }

        return;
'''

new_mouse_down_matrix = '''        const bool rightClickErase = event.mods.isRightButtonDown();
        const bool altDown = event.mods.isAltDown();
        const bool ctrlDown = event.mods.isCtrlDown();
        const bool shiftDown = event.mods.isShiftDown();

        // Matrix mode is paint/edit oriented:
        // - Left click creates/keeps a note and applies pitch from mouse Y.
        // - Right click is the dedicated erase gesture.
        // - Alt click/drag pitch-paints existing notes only.
        // - Ctrl click/drag velocity-paints existing notes only.
        // - Shift drag moves an existing note horizontally within the same row.
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
        {
            const int gridStepCount = audioProcessor.getGridStepCount();

            matrixMoveSourcePattern = patternIndex;
            matrixMoveSourceStep = stepIndex;
            matrixMoveNote = audioProcessor.getStepNote(patternIndex, stepIndex);
            matrixMoveVelocity = juce::jlimit(1, 127, audioProcessor.getStepVelocity(patternIndex, stepIndex));
            matrixMoveDuration = juce::jlimit(
                1,
                gridStepCount - stepIndex,
                audioProcessor.getStepDurationSteps(patternIndex, stepIndex));

            selectedEditPattern = patternIndex;
            selectedStep = stepIndex;

            audioProcessor.setTargetPatternAndStep(selectedEditPattern, selectedStep);
            audioProcessor.updateTargetParametersFromStep();

            updateEditPatternButtonHighlights();
            repaint();
        }
        else if (matrixEditDragMode == MatrixEditDragMode::PitchExistingOnly)
        {
            setMatrixStepPitchAtMousePosition(position);
        }
        else if (matrixEditDragMode == MatrixEditDragMode::VelocityExistingOnly)
        {
            setMatrixStepVelocityAtMousePosition(position);
        }
        else
        {
            setPatternStepValue(patternIndex, stepIndex, dragPaintValue);

            if (dragPaintValue)
                setMatrixStepPitchAtMousePosition(position);
        }

        return;
'''

if old_mouse_down_matrix not in cpp:
    if "MatrixEditDragMode::MoveExistingStep" in cpp and "matrixMoveSourcePattern = patternIndex;" in cpp:
        print("Matrix mouseDown move mode already appears patched; continuing.")
    else:
        raise SystemExit("ERROR: Could not patch Matrix mouseDown move mode")
else:
    cpp = cpp.replace(old_mouse_down_matrix, new_mouse_down_matrix, 1)


# -----------------------------------------------------------------------------
# 7. Patch mouseDrag dispatch
# -----------------------------------------------------------------------------

old_drag_dispatch = '''    if (matrixEditDragMode == MatrixEditDragMode::VelocityExistingOnly)
    {
        setMatrixStepVelocityAtMousePosition(event.getPosition());
        return;
    }

    setStepAtMousePosition(event.getPosition(), dragPaintValue);
}
'''

new_drag_dispatch = '''    if (matrixEditDragMode == MatrixEditDragMode::VelocityExistingOnly)
    {
        setMatrixStepVelocityAtMousePosition(event.getPosition());
        return;
    }

    if (matrixEditDragMode == MatrixEditDragMode::MoveExistingStep)
    {
        moveMatrixStepAtMousePosition(event.getPosition());
        return;
    }

    setStepAtMousePosition(event.getPosition(), dragPaintValue);
}
'''

if old_drag_dispatch not in cpp:
    if "moveMatrixStepAtMousePosition(event.getPosition())" in cpp:
        print("Matrix mouseDrag move dispatch already appears patched; continuing.")
    else:
        raise SystemExit("ERROR: Could not patch Matrix mouseDrag move dispatch")
else:
    cpp = cpp.replace(old_drag_dispatch, new_drag_dispatch, 1)


# -----------------------------------------------------------------------------
# 8. Reset move state on mouseUp
# -----------------------------------------------------------------------------

old_mouse_up = '''    isDraggingPatternStepEdit = false;
    matrixEditDragMode = MatrixEditDragMode::None;
    isDraggingMelodyDuration = false;
'''

new_mouse_up = '''    isDraggingPatternStepEdit = false;
    matrixEditDragMode = MatrixEditDragMode::None;
    matrixMoveSourcePattern = -1;
    matrixMoveSourceStep = -1;
    isDraggingMelodyDuration = false;
'''

if old_mouse_up not in cpp:
    if "matrixMoveSourceStep = -1;" in cpp:
        print("mouseUp move state reset already appears present; continuing.")
    else:
        raise SystemExit("ERROR: Could not patch mouseUp move reset")
else:
    cpp = cpp.replace(old_mouse_up, new_mouse_up, 1)


# -----------------------------------------------------------------------------
# 9. Update version text
# -----------------------------------------------------------------------------

if '"v1.17.4 - Matrix Velocity Display"' in cpp:
    cpp = cpp.replace('"v1.17.4 - Matrix Velocity Display"', '"v1.17.5 - Matrix Step Move"', 1)
elif '"v1.17.5 - Matrix Step Move"' in cpp:
    print("Version text already appears updated to v1.17.5; continuing.")
else:
    print("WARNING: Could not find v1.17.4 version text; version label not updated.")


cpp_path.write_text(cpp, encoding="utf-8")

print("v1.17.5 applied: Matrix Shift-drag moves existing steps within the same row.")
