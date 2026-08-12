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
# 1. Add helper declarations to PluginEditor.h
# -----------------------------------------------------------------------------

old_header = '''    void toggleStepAtMousePosition(juce::Point<int> position);
    void setStepAtMousePosition(juce::Point<int> position, bool shouldHaveNote);
    void setPatternStepValue(int patternIndex, int stepIndex, bool shouldHaveNote);
    void setMelodyPaintCellValue(int stepIndex, int midiNote, bool shouldHaveNote);
'''

new_header = '''    void toggleStepAtMousePosition(juce::Point<int> position);
    void setStepAtMousePosition(juce::Point<int> position, bool shouldHaveNote);
    void setPatternStepValue(int patternIndex, int stepIndex, bool shouldHaveNote);
    int getMatrixPitchForMousePosition(int patternIndex, int stepIndex, juce::Point<int> position) const;
    void setMatrixStepPitchAtMousePosition(juce::Point<int> position);
    void setMelodyPaintCellValue(int stepIndex, int midiNote, bool shouldHaveNote);
'''

if old_header not in header:
    if "getMatrixPitchForMousePosition" in header and "setMatrixStepPitchAtMousePosition" in header:
        print("Header already appears patched; continuing.")
    else:
        raise SystemExit("ERROR: Could not patch PluginEditor.h Matrix pitch declarations")
else:
    header = header.replace(old_header, new_header, 1)
    header_path.write_text(header, encoding="utf-8")


# -----------------------------------------------------------------------------
# 2. Insert Matrix pitch helper functions before setStepAtMousePosition()
# -----------------------------------------------------------------------------

insert_marker = '''void MidiPatternLauncherAudioProcessorEditor::setStepAtMousePosition(
    juce::Point<int> position,
    bool shouldHaveNote)
'''

if insert_marker not in cpp:
    raise SystemExit("ERROR: Could not find setStepAtMousePosition insertion marker")

if "int MidiPatternLauncherAudioProcessorEditor::getMatrixPitchForMousePosition(" not in cpp:
    helper_functions = r'''int MidiPatternLauncherAudioProcessorEditor::getMatrixPitchForMousePosition(
    int patternIndex,
    int stepIndex,
    juce::Point<int> position) const
{
    static constexpr int matrixLowestMidiNote = 48;
    static constexpr int matrixHighestMidiNote = 71;
    static constexpr int matrixNoteRange = matrixHighestMidiNote - matrixLowestMidiNote;

    if (patternIndex < 0 || patternIndex >= 3)
        return matrixLowestMidiNote;

    const int gridStepCount = audioProcessor.getGridStepCount();

    if (stepIndex < 0 || stepIndex >= gridStepCount)
        return matrixLowestMidiNote;

    const auto stepBox = getPatternStepBox(patternIndex, stepIndex);

    if (stepBox.getHeight() <= 1)
        return matrixLowestMidiNote;

    const int relativeY = juce::jlimit(
        0,
        stepBox.getHeight() - 1,
        position.y - stepBox.getY());

    const float normalisedFromTop = static_cast<float>(relativeY)
        / static_cast<float>(stepBox.getHeight() - 1);

    const int noteOffsetFromTop = juce::roundToInt(normalisedFromTop * static_cast<float>(matrixNoteRange));

    return juce::jlimit(
        matrixLowestMidiNote,
        matrixHighestMidiNote,
        matrixHighestMidiNote - noteOffsetFromTop);
}

void MidiPatternLauncherAudioProcessorEditor::setMatrixStepPitchAtMousePosition(
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
    cpp = cpp.replace(insert_marker, helper_functions + insert_marker, 1)
else:
    print("Matrix pitch helpers already appear inserted; continuing.")


# -----------------------------------------------------------------------------
# 3. Patch setStepAtMousePosition() so drag-paint also applies pitch.
# -----------------------------------------------------------------------------

old_set_step_at_mouse = '''void MidiPatternLauncherAudioProcessorEditor::setStepAtMousePosition(
    juce::Point<int> position,
    bool shouldHaveNote)
{
    int patternIndex = -1;
    int stepIndex = -1;

    if (!getPatternStepAtPosition(position, patternIndex, stepIndex))
        return;

    setPatternStepValue(patternIndex, stepIndex, shouldHaveNote);
}
'''

new_set_step_at_mouse = '''void MidiPatternLauncherAudioProcessorEditor::setStepAtMousePosition(
    juce::Point<int> position,
    bool shouldHaveNote)
{
    int patternIndex = -1;
    int stepIndex = -1;

    if (!getPatternStepAtPosition(position, patternIndex, stepIndex))
        return;

    setPatternStepValue(patternIndex, stepIndex, shouldHaveNote);

    if (shouldHaveNote)
        setMatrixStepPitchAtMousePosition(position);
}
'''

if old_set_step_at_mouse not in cpp:
    if "if (shouldHaveNote)\n        setMatrixStepPitchAtMousePosition(position);" in cpp:
        print("setStepAtMousePosition already appears patched; continuing.")
    else:
        raise SystemExit("ERROR: Could not patch setStepAtMousePosition")
else:
    cpp = cpp.replace(old_set_step_at_mouse, new_set_step_at_mouse, 1)


# -----------------------------------------------------------------------------
# 4. Patch Matrix mouseDown branch so first click also sets pitch.
# -----------------------------------------------------------------------------

old_mouse_down_matrix = '''        setPatternStepValue(patternIndex, stepIndex, dragPaintValue);
        return;
'''

new_mouse_down_matrix = '''        setPatternStepValue(patternIndex, stepIndex, dragPaintValue);

        if (dragPaintValue)
            setMatrixStepPitchAtMousePosition(position);

        return;
'''

if old_mouse_down_matrix not in cpp:
    if "if (dragPaintValue)\n            setMatrixStepPitchAtMousePosition(position);" in cpp:
        print("mouseDown Matrix pitch already appears patched; continuing.")
    else:
        raise SystemExit("ERROR: Could not patch Matrix mouseDown branch")
else:
    cpp = cpp.replace(old_mouse_down_matrix, new_mouse_down_matrix, 1)


cpp_path.write_text(cpp, encoding="utf-8")

print("v1.17.0 Matrix Patch M1 applied: vertical pitch painting in Matrix cells.")
