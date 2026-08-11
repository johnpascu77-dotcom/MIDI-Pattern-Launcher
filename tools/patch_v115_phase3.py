from pathlib import Path

editor_h_path = Path("Source/PluginEditor.h")
editor_cpp_path = Path("Source/PluginEditor.cpp")

if not editor_h_path.exists():
    raise SystemExit("ERROR: Source/PluginEditor.h not found")

if not editor_cpp_path.exists():
    raise SystemExit("ERROR: Source/PluginEditor.cpp not found")

def read(path):
    return path.read_text(encoding="utf-8")

def write(path, text):
    path.write_text(text, encoding="utf-8")

def require(condition, message):
    if not condition:
        raise SystemExit("ERROR: " + message)

def replace_once(text, old, new, label):
    count = text.count(old)
    require(count == 1, f"Expected exactly one match for {label}, found {count}")
    return text.replace(old, new, 1)

# =============================================================================
# PluginEditor.h

text = read(editor_h_path)

if "getMelodyPaintCellAtPosition" not in text:
    old = '''    bool getPatternStepAtPosition(juce::Point<int> position, int& patternIndexOut, int& stepIndexOut) const;
    void updateSelectedStepFromMousePosition(juce::Point<int> position);
    void toggleStepAtMousePosition(juce::Point<int> position);
    void setStepAtMousePosition(juce::Point<int> position, bool shouldHaveNote);
    void setPatternStepValue(int patternIndex, int stepIndex, bool shouldHaveNote);
'''
    new = '''    bool getPatternStepAtPosition(juce::Point<int> position, int& patternIndexOut, int& stepIndexOut) const;
    bool getMelodyPaintCellAtPosition(juce::Point<int> position, int& stepIndexOut, int& midiNoteOut) const;

    void updateSelectedStepFromMousePosition(juce::Point<int> position);
    void toggleStepAtMousePosition(juce::Point<int> position);
    void setStepAtMousePosition(juce::Point<int> position, bool shouldHaveNote);
    void setPatternStepValue(int patternIndex, int stepIndex, bool shouldHaveNote);
    void setMelodyPaintCellValue(int stepIndex, int midiNote, bool shouldHaveNote);
    void setMelodyPaintCellAtMousePosition(juce::Point<int> position, bool shouldHaveNote);
'''
    text = replace_once(text, old, new, "PluginEditor.h melody paint declarations")
else:
    print("SKIP: Melody paint declarations already present in PluginEditor.h")

write(editor_h_path, text)

# =============================================================================
# PluginEditor.cpp

text = read(editor_cpp_path)

# -----------------------------------------------------------------------------
# Add helper functions after getPatternStepAtPosition.

if "MidiPatternLauncherAudioProcessorEditor::getMelodyPaintCellAtPosition" not in text:
    marker = '''bool MidiPatternLauncherAudioProcessorEditor::getPatternStepAtPosition(
    juce::Point<int> position,
    int& patternIndexOut,
    int& stepIndexOut) const
{
    const int gridStepCount = audioProcessor.getGridStepCount();

    for (int patternIndex = 0; patternIndex < 3; ++patternIndex)
    {
        for (int stepIndex = 0; stepIndex < gridStepCount; ++stepIndex)
        {
            if (getPatternStepBox(patternIndex, stepIndex).contains(position))
            {
                patternIndexOut = patternIndex;
                stepIndexOut = stepIndex;
                return true;
            }
        }
    }

    patternIndexOut = -1;
    stepIndexOut = -1;
    return false;
}

'''
    insertion = marker + '''bool MidiPatternLauncherAudioProcessorEditor::getMelodyPaintCellAtPosition(
    juce::Point<int> position,
    int& stepIndexOut,
    int& midiNoteOut) const
{
    static constexpr int melodyLowestMidiNote = 48;
    static constexpr int melodyHighestMidiNote = 71;
    static constexpr int melodyNoteCount = melodyHighestMidiNote - melodyLowestMidiNote + 1;

    const int gridStepCount = audioProcessor.getGridStepCount();

    auto melodyArea = getPatternMatrixArea();

    const int noteLabelWidth = 38;
    const int stepLabelHeight = 16;
    const int stepGap = 3;
    const int noteGap = 1;

    melodyArea.removeFromLeft(noteLabelWidth);
    melodyArea.removeFromTop(stepLabelHeight);

    auto gridArea = melodyArea;

    if (!gridArea.contains(position))
    {
        stepIndexOut = -1;
        midiNoteOut = -1;
        return false;
    }

    const int cellWidth = (gridArea.getWidth() - ((gridStepCount - 1) * stepGap)) / gridStepCount;
    const int cellHeight = (gridArea.getHeight() - ((melodyNoteCount - 1) * noteGap)) / melodyNoteCount;

    for (int stepIndex = 0; stepIndex < gridStepCount; ++stepIndex)
    {
        const int x = gridArea.getX() + stepIndex * (cellWidth + stepGap);

        for (int noteOffset = 0; noteOffset < melodyNoteCount; ++noteOffset)
        {
            const int y = gridArea.getY() + noteOffset * (cellHeight + noteGap);

            auto cellBox = juce::Rectangle<int>(
                x,
                y,
                cellWidth,
                cellHeight);

            if (cellBox.contains(position))
            {
                stepIndexOut = stepIndex;
                midiNoteOut = melodyHighestMidiNote - noteOffset;
                return true;
            }
        }
    }

    stepIndexOut = -1;
    midiNoteOut = -1;
    return false;
}

void MidiPatternLauncherAudioProcessorEditor::setMelodyPaintCellValue(
    int stepIndex,
    int midiNote,
    bool shouldHaveNote)
{
    static constexpr int melodyLowestMidiNote = 48;
    static constexpr int melodyHighestMidiNote = 71;

    const int gridStepCount = audioProcessor.getGridStepCount();

    if (stepIndex < 0 || stepIndex >= gridStepCount)
        return;

    if (midiNote < melodyLowestMidiNote || midiNote > melodyHighestMidiNote)
        return;

    const int patternIndex = getDisplayedPattern();

    if (lastEditedPattern == patternIndex && lastEditedStep == stepIndex && shouldHaveNote)
        return;

    selectedEditPattern = patternIndex;
    selectedStep = stepIndex;

    audioProcessor.setTargetPatternAndStep(selectedEditPattern, selectedStep);

    if (shouldHaveNote)
    {
        const int velocity = juce::jlimit(1, 127, audioProcessor.getTargetVelocity());
        const int duration = juce::jlimit(1, 16, audioProcessor.getTargetDurationSteps());

        audioProcessor.setStepValues(patternIndex, stepIndex, midiNote, velocity, duration);
    }
    else
    {
        audioProcessor.clearStep(patternIndex, stepIndex);
    }

    lastEditedPattern = patternIndex;
    lastEditedStep = stepIndex;

    updateEditPatternButtonHighlights();
    repaint();
}

void MidiPatternLauncherAudioProcessorEditor::setMelodyPaintCellAtMousePosition(
    juce::Point<int> position,
    bool shouldHaveNote)
{
    int stepIndex = -1;
    int midiNote = -1;

    if (!getMelodyPaintCellAtPosition(position, stepIndex, midiNote))
        return;

    setMelodyPaintCellValue(stepIndex, midiNote, shouldHaveNote);
}

'''
    text = replace_once(text, marker, insertion, "PluginEditor.cpp add melody paint helper functions")
else:
    print("SKIP: Melody paint helper functions already present in PluginEditor.cpp")

# -----------------------------------------------------------------------------
# Replace mouseDown.

old_mouse_down = '''void MidiPatternLauncherAudioProcessorEditor::mouseDown(const juce::MouseEvent& event)
{
    const auto position = event.getPosition();

    int patternIndex = -1;
    int stepIndex = -1;

    lastEditedPattern = -1;
    lastEditedStep = -1;

    if (getPatternStepAtPosition(position, patternIndex, stepIndex))
    {
        const bool rightClickErase = event.mods.isRightButtonDown();
        const bool currentlyHasNote = audioProcessor.stepHasNote(patternIndex, stepIndex);

        dragPaintValue = rightClickErase ? false : !currentlyHasNote;
        isDraggingPatternStepEdit = true;

        setPatternStepValue(patternIndex, stepIndex, dragPaintValue);
        return;
    }

    isDraggingPatternStepEdit = false;
    updateSelectedStepFromMousePosition(position);
}
'''

new_mouse_down = '''void MidiPatternLauncherAudioProcessorEditor::mouseDown(const juce::MouseEvent& event)
{
    const auto position = event.getPosition();

    lastEditedPattern = -1;
    lastEditedStep = -1;

    if (audioProcessor.isMelodyPaintMode())
    {
        int melodyStepIndex = -1;
        int melodyMidiNote = -1;

        if (getMelodyPaintCellAtPosition(position, melodyStepIndex, melodyMidiNote))
        {
            const bool rightClickErase = event.mods.isRightButtonDown();

            dragPaintValue = !rightClickErase;
            isDraggingPatternStepEdit = true;

            setMelodyPaintCellValue(melodyStepIndex, melodyMidiNote, dragPaintValue);
            return;
        }

        isDraggingPatternStepEdit = false;
        return;
    }

    int patternIndex = -1;
    int stepIndex = -1;

    if (getPatternStepAtPosition(position, patternIndex, stepIndex))
    {
        const bool rightClickErase = event.mods.isRightButtonDown();
        const bool currentlyHasNote = audioProcessor.stepHasNote(patternIndex, stepIndex);

        dragPaintValue = rightClickErase ? false : !currentlyHasNote;
        isDraggingPatternStepEdit = true;

        setPatternStepValue(patternIndex, stepIndex, dragPaintValue);
        return;
    }

    isDraggingPatternStepEdit = false;
    updateSelectedStepFromMousePosition(position);
}
'''

if old_mouse_down in text:
    text = text.replace(old_mouse_down, new_mouse_down, 1)
else:
    require("if (audioProcessor.isMelodyPaintMode())" in text, "mouseDown block not found and melody branch not present")
    print("SKIP: mouseDown appears already patched")

# -----------------------------------------------------------------------------
# Replace mouseDrag.

old_mouse_drag = '''void MidiPatternLauncherAudioProcessorEditor::mouseDrag(const juce::MouseEvent& event)
{
    if (!isDraggingPatternStepEdit)
        return;

    setStepAtMousePosition(event.getPosition(), dragPaintValue);
}
'''

new_mouse_drag = '''void MidiPatternLauncherAudioProcessorEditor::mouseDrag(const juce::MouseEvent& event)
{
    if (!isDraggingPatternStepEdit)
        return;

    if (audioProcessor.isMelodyPaintMode())
    {
        setMelodyPaintCellAtMousePosition(event.getPosition(), dragPaintValue);
        return;
    }

    setStepAtMousePosition(event.getPosition(), dragPaintValue);
}
'''

if old_mouse_drag in text:
    text = text.replace(old_mouse_drag, new_mouse_drag, 1)
else:
    require("setMelodyPaintCellAtMousePosition(event.getPosition(), dragPaintValue);" in text, "mouseDrag block not found and melody branch not present")
    print("SKIP: mouseDrag appears already patched")

write(editor_cpp_path, text)

print("v1.15.0 Phase 3 patch applied successfully.")
