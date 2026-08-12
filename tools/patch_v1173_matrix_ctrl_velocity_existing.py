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
# 1. Extend MatrixEditDragMode enum in PluginEditor.h
# -----------------------------------------------------------------------------

old_enum = '''    enum class MatrixEditDragMode
    {
        None,
        PaintOrErase,
        PitchExistingOnly
    };
'''

new_enum = '''    enum class MatrixEditDragMode
    {
        None,
        PaintOrErase,
        PitchExistingOnly,
        VelocityExistingOnly
    };
'''

if old_enum not in header:
    if "VelocityExistingOnly" in header:
        print("MatrixEditDragMode already includes VelocityExistingOnly; continuing.")
    else:
        raise SystemExit("ERROR: Could not extend MatrixEditDragMode enum")
else:
    header = header.replace(old_enum, new_enum, 1)


# -----------------------------------------------------------------------------
# 2. Add helper declarations in PluginEditor.h
# -----------------------------------------------------------------------------

old_decls = '''    int getMatrixPitchForMousePosition(int patternIndex, int stepIndex, juce::Point<int> position) const;
    void setMatrixStepPitchAtMousePosition(juce::Point<int> position);
    void setMelodyPaintCellValue(int stepIndex, int midiNote, bool shouldHaveNote);
'''

new_decls = '''    int getMatrixPitchForMousePosition(int patternIndex, int stepIndex, juce::Point<int> position) const;
    void setMatrixStepPitchAtMousePosition(juce::Point<int> position);
    int getMatrixVelocityForMousePosition(int patternIndex, int stepIndex, juce::Point<int> position) const;
    void setMatrixStepVelocityAtMousePosition(juce::Point<int> position);
    void setMelodyPaintCellValue(int stepIndex, int midiNote, bool shouldHaveNote);
'''

if old_decls not in header:
    if "getMatrixVelocityForMousePosition" in header and "setMatrixStepVelocityAtMousePosition" in header:
        print("Matrix velocity helper declarations already appear present; continuing.")
    else:
        raise SystemExit("ERROR: Could not add Matrix velocity helper declarations")
else:
    header = header.replace(old_decls, new_decls, 1)

header_path.write_text(header, encoding="utf-8")


# -----------------------------------------------------------------------------
# 3. Add helper definitions in PluginEditor.cpp after setMatrixStepPitchAtMousePosition()
# -----------------------------------------------------------------------------

insert_after = '''void MidiPatternLauncherAudioProcessorEditor::setMatrixStepPitchAtMousePosition(
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

    const int midiNote = getMatrixPitchForMousePosition(patternIndex, stepIndex, position);
    const int velocity = juce::jlimit(1, 127, audioProcessor.getStepVelocity(patternIndex, stepIndex));
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

velocity_helpers = r'''int MidiPatternLauncherAudioProcessorEditor::getMatrixVelocityForMousePosition(
    int patternIndex,
    int stepIndex,
    juce::Point<int> position) const
{
    if (patternIndex < 0 || patternIndex >= 3)
        return 100;

    const int gridStepCount = audioProcessor.getGridStepCount();

    if (stepIndex < 0 || stepIndex >= gridStepCount)
        return 100;

    const auto stepBox = getPatternStepBox(patternIndex, stepIndex);

    if (stepBox.getHeight() <= 1)
        return 100;

    const int relativeY = juce::jlimit(
        0,
        stepBox.getHeight() - 1,
        position.y - stepBox.getY());

    const float normalisedFromTop = static_cast<float>(relativeY)
        / static_cast<float>(stepBox.getHeight() - 1);

    const int velocityOffsetFromTop = juce::roundToInt(normalisedFromTop * 126.0f);

    return juce::jlimit(1, 127, 127 - velocityOffsetFromTop);
}

void MidiPatternLauncherAudioProcessorEditor::setMatrixStepVelocityAtMousePosition(
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

if "int MidiPatternLauncherAudioProcessorEditor::getMatrixVelocityForMousePosition(" in cpp:
    print("Matrix velocity helper definitions already appear present; continuing.")
else:
    if insert_after not in cpp:
        raise SystemExit("ERROR: Could not find insertion point after setMatrixStepPitchAtMousePosition")

    cpp = cpp.replace(insert_after, insert_after + velocity_helpers, 1)


# -----------------------------------------------------------------------------
# 4. Patch Matrix mouseDown mode selection to support Ctrl velocity mode
# -----------------------------------------------------------------------------

old_mouse_down = '''        const bool rightClickErase = event.mods.isRightButtonDown();
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

new_mouse_down = '''        const bool rightClickErase = event.mods.isRightButtonDown();
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

if old_mouse_down not in cpp:
    if "MatrixEditDragMode::VelocityExistingOnly" in cpp and "setMatrixStepVelocityAtMousePosition(position)" in cpp:
        print("Matrix mouseDown Ctrl velocity mode already appears patched; continuing.")
    else:
        raise SystemExit("ERROR: Could not patch Matrix mouseDown for Ctrl velocity mode")
else:
    cpp = cpp.replace(old_mouse_down, new_mouse_down, 1)


# -----------------------------------------------------------------------------
# 5. Patch Matrix mouseDrag dispatch
# -----------------------------------------------------------------------------

old_mouse_drag_dispatch = '''    if (matrixEditDragMode == MatrixEditDragMode::PitchExistingOnly)
    {
        setMatrixStepPitchAtMousePosition(event.getPosition());
        return;
    }

    setStepAtMousePosition(event.getPosition(), dragPaintValue);
}
'''

new_mouse_drag_dispatch = '''    if (matrixEditDragMode == MatrixEditDragMode::PitchExistingOnly)
    {
        setMatrixStepPitchAtMousePosition(event.getPosition());
        return;
    }

    if (matrixEditDragMode == MatrixEditDragMode::VelocityExistingOnly)
    {
        setMatrixStepVelocityAtMousePosition(event.getPosition());
        return;
    }

    setStepAtMousePosition(event.getPosition(), dragPaintValue);
}
'''

if old_mouse_drag_dispatch not in cpp:
    if "matrixEditDragMode == MatrixEditDragMode::VelocityExistingOnly" in cpp:
        print("Matrix mouseDrag Ctrl velocity dispatch already appears patched; continuing.")
    else:
        raise SystemExit("ERROR: Could not patch Matrix mouseDrag for Ctrl velocity mode")
else:
    cpp = cpp.replace(old_mouse_drag_dispatch, new_mouse_drag_dispatch, 1)


# -----------------------------------------------------------------------------
# 6. Update version text
# -----------------------------------------------------------------------------

if '"v1.17.1 - Matrix Gesture Editing"' in cpp:
    cpp = cpp.replace('"v1.17.1 - Matrix Gesture Editing"', '"v1.17.3 - Matrix Velocity Paint"', 1)
elif '"v1.17.3 - Matrix Velocity Paint"' in cpp:
    print("Version text already appears updated to v1.17.3; continuing.")
else:
    print("WARNING: Could not find v1.17.1 version text; version label not updated.")


cpp_path.write_text(cpp, encoding="utf-8")

print("v1.17.3 applied: Matrix Ctrl-drag velocity-paints existing notes only.")
