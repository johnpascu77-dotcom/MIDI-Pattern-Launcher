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
# Source/PluginEditor.h

text = read(editor_h_path)

if "isDraggingMelodyDuration" not in text:
    old = '''    bool isDraggingPatternStepEdit = false;
    bool dragPaintValue = true;
    int lastEditedPattern = -1;
    int lastEditedStep = -1;
'''
    new = '''    bool isDraggingPatternStepEdit = false;
    bool dragPaintValue = true;
    int lastEditedPattern = -1;
    int lastEditedStep = -1;

    bool isDraggingMelodyDuration = false;
    int melodyDragPattern = -1;
    int melodyDragStartStep = -1;
    int melodyDragStartNote = -1;
'''
    text = replace_once(text, old, new, "PluginEditor.h melody duration drag state")
else:
    print("SKIP: melody duration drag state already present")

if "updateMelodyDragDurationAtMousePosition" not in text:
    old = '''    void setMelodyPaintCellValue(int stepIndex, int midiNote, bool shouldHaveNote);
    void setMelodyPaintCellAtMousePosition(juce::Point<int> position, bool shouldHaveNote);
'''
    new = '''    void setMelodyPaintCellValue(int stepIndex, int midiNote, bool shouldHaveNote);
    void setMelodyPaintCellAtMousePosition(juce::Point<int> position, bool shouldHaveNote);
    void startMelodyDurationDrag(int stepIndex, int midiNote);
    void updateMelodyDragDurationAtMousePosition(juce::Point<int> position);
'''
    text = replace_once(text, old, new, "PluginEditor.h melody duration helper declarations")
else:
    print("SKIP: melody duration helper declarations already present")

write(editor_h_path, text)

# =============================================================================
# Source/PluginEditor.cpp

text = read(editor_cpp_path)

# -----------------------------------------------------------------------------
# Add duration drag helper functions after setMelodyPaintCellAtMousePosition.

if "MidiPatternLauncherAudioProcessorEditor::startMelodyDurationDrag" not in text:
    marker = '''void MidiPatternLauncherAudioProcessorEditor::setMelodyPaintCellAtMousePosition(
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
    insertion = marker + '''void MidiPatternLauncherAudioProcessorEditor::startMelodyDurationDrag(
    int stepIndex,
    int midiNote)
{
    const int gridStepCount = audioProcessor.getGridStepCount();

    if (stepIndex < 0 || stepIndex >= gridStepCount)
        return;

    if (midiNote < 0 || midiNote > 127)
        return;

    melodyDragPattern = getDisplayedPattern();
    melodyDragStartStep = stepIndex;
    melodyDragStartNote = midiNote;
    isDraggingMelodyDuration = true;

    selectedEditPattern = melodyDragPattern;
    selectedStep = melodyDragStartStep;

    audioProcessor.setTargetPatternAndStep(selectedEditPattern, selectedStep);

    const int velocity = juce::jlimit(1, 127, audioProcessor.getTargetVelocity());

    audioProcessor.setStepValues(
        melodyDragPattern,
        melodyDragStartStep,
        melodyDragStartNote,
        velocity,
        1);

    audioProcessor.updateTargetParametersFromStep();

    lastEditedPattern = melodyDragPattern;
    lastEditedStep = melodyDragStartStep;

    updateEditPatternButtonHighlights();
    repaint();
}

void MidiPatternLauncherAudioProcessorEditor::updateMelodyDragDurationAtMousePosition(
    juce::Point<int> position)
{
    if (!isDraggingMelodyDuration)
        return;

    const int gridStepCount = audioProcessor.getGridStepCount();

    if (melodyDragPattern < 0 || melodyDragPattern >= 3)
        return;

    if (melodyDragStartStep < 0 || melodyDragStartStep >= gridStepCount)
        return;

    int hoverStepIndex = -1;
    int hoverMidiNote = -1;

    if (!getMelodyPaintCellAtPosition(position, hoverStepIndex, hoverMidiNote))
        return;

    juce::ignoreUnused(hoverMidiNote);

    const int endStep = juce::jlimit(melodyDragStartStep, gridStepCount - 1, hoverStepIndex);
    const int duration = juce::jlimit(1, gridStepCount, endStep - melodyDragStartStep + 1);

    const int velocity = juce::jlimit(1, 127, audioProcessor.getStepVelocity(melodyDragPattern, melodyDragStartStep));

    audioProcessor.setStepValues(
        melodyDragPattern,
        melodyDragStartStep,
        melodyDragStartNote,
        velocity,
        duration);

    selectedEditPattern = melodyDragPattern;
    selectedStep = melodyDragStartStep;

    audioProcessor.setTargetPatternAndStep(selectedEditPattern, selectedStep);
    audioProcessor.updateTargetParametersFromStep();

    repaint();
}

'''
    text = replace_once(text, marker, insertion, "PluginEditor.cpp add melody duration helper functions")
else:
    print("SKIP: melody duration helper functions already present")

# -----------------------------------------------------------------------------
# Update setMelodyPaintCellValue so normal painting syncs target controls.

old_sync_block = '''    if (shouldHaveNote)
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
'''

new_sync_block = '''    if (shouldHaveNote)
    {
        const int velocity = juce::jlimit(1, 127, audioProcessor.getTargetVelocity());
        const int duration = juce::jlimit(1, gridStepCount, audioProcessor.getTargetDurationSteps());

        audioProcessor.setStepValues(patternIndex, stepIndex, midiNote, velocity, duration);
    }
    else
    {
        audioProcessor.clearStep(patternIndex, stepIndex);
    }

    audioProcessor.updateTargetParametersFromStep();

    lastEditedPattern = patternIndex;
    lastEditedStep = stepIndex;

    updateEditPatternButtonHighlights();
    repaint();
}
'''

if old_sync_block in text:
    text = text.replace(old_sync_block, new_sync_block, 1)
else:
    print("SKIP: setMelodyPaintCellValue target sync block not replaced; it may already be updated")

# -----------------------------------------------------------------------------
# Replace Melody branch inside mouseDown.

old_mouse_down_melody_branch = '''    if (audioProcessor.isMelodyPaintMode())
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
'''

new_mouse_down_melody_branch = '''    if (audioProcessor.isMelodyPaintMode())
    {
        int melodyStepIndex = -1;
        int melodyMidiNote = -1;

        isDraggingMelodyDuration = false;
        melodyDragPattern = -1;
        melodyDragStartStep = -1;
        melodyDragStartNote = -1;

        if (getMelodyPaintCellAtPosition(position, melodyStepIndex, melodyMidiNote))
        {
            const bool rightClickErase = event.mods.isRightButtonDown();

            if (rightClickErase)
            {
                dragPaintValue = false;
                isDraggingPatternStepEdit = true;
                setMelodyPaintCellValue(melodyStepIndex, melodyMidiNote, false);
            }
            else
            {
                dragPaintValue = true;
                isDraggingPatternStepEdit = false;
                startMelodyDurationDrag(melodyStepIndex, melodyMidiNote);
            }

            return;
        }

        isDraggingPatternStepEdit = false;
        return;
    }
'''

if old_mouse_down_melody_branch in text:
    text = text.replace(old_mouse_down_melody_branch, new_mouse_down_melody_branch, 1)
else:
    require("startMelodyDurationDrag" in text, "mouseDown melody branch not found and not already patched")
    print("SKIP: mouseDown melody branch appears already patched")

# -----------------------------------------------------------------------------
# Replace mouseDrag.

old_mouse_drag = '''void MidiPatternLauncherAudioProcessorEditor::mouseDrag(const juce::MouseEvent& event)
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

new_mouse_drag = '''void MidiPatternLauncherAudioProcessorEditor::mouseDrag(const juce::MouseEvent& event)
{
    if (audioProcessor.isMelodyPaintMode())
    {
        if (isDraggingMelodyDuration)
        {
            updateMelodyDragDurationAtMousePosition(event.getPosition());
            return;
        }

        if (isDraggingPatternStepEdit)
        {
            setMelodyPaintCellAtMousePosition(event.getPosition(), dragPaintValue);
            return;
        }

        return;
    }

    if (!isDraggingPatternStepEdit)
        return;

    setStepAtMousePosition(event.getPosition(), dragPaintValue);
}
'''

if old_mouse_drag in text:
    text = text.replace(old_mouse_drag, new_mouse_drag, 1)
else:
    require("updateMelodyDragDurationAtMousePosition(event.getPosition())" in text, "mouseDrag block not found and not already patched")
    print("SKIP: mouseDrag appears already patched")

# -----------------------------------------------------------------------------
# Update mouseUp to clear melody duration drag state.

old_mouse_up_tail = '''    isDraggingPatternStepEdit = false;
    lastEditedPattern = -1;
    lastEditedStep = -1;
}
'''

new_mouse_up_tail = '''    isDraggingPatternStepEdit = false;
    isDraggingMelodyDuration = false;

    melodyDragPattern = -1;
    melodyDragStartStep = -1;
    melodyDragStartNote = -1;

    lastEditedPattern = -1;
    lastEditedStep = -1;
}
'''

if old_mouse_up_tail in text:
    text = text.replace(old_mouse_up_tail, new_mouse_up_tail, 1)
else:
    print("SKIP: mouseUp tail not replaced; it may already be updated")

# -----------------------------------------------------------------------------
# Replace Melody grid drawing inner logic with duration-bar drawing.
#
# This patch keeps the existing cell background grid, but suppresses one-cell
# note drawing and then draws duration bars over the grid.

if "Draw duration bars after the background grid has been drawn." not in text:
    old_inner_note_logic = '''                if (isCurrentStep && isNoteCell)
                    g.setColour(juce::Colour(0xfff5c542));
                else if (isNoteCell)
                    g.setColour(isInsideLoop ? juce::Colour(0xff5aa6b8) : juce::Colour(0xff35545c));
                else if (isCurrentStep)
                    g.setColour(juce::Colour(0xff5a5124));
                else if (isReferenceOctaveNote)
                    g.setColour(isInsideLoop ? juce::Colour(0xff263f45) : juce::Colour(0xff1c292d));
                else
                    g.setColour(isInsideLoop ? juce::Colour(0xff26363b) : juce::Colour(0xff1c292d));

                g.fillRoundedRectangle(cellBox.toFloat(), 2.0f);

                if (isNoteCell)
                {
                    g.setColour(isCurrentStep ? juce::Colours::black : juce::Colours::white);
                    g.drawRoundedRectangle(cellBox.toFloat().reduced(1.0f), 2.0f, 1.0f);
                }
                else
                {
                    g.setColour(juce::Colour(0xff3b5056));
                    g.drawRoundedRectangle(cellBox.toFloat(), 2.0f, 0.5f);
                }

                if (isSelectedColumn && isNoteCell)
                {
                    g.setColour(juce::Colours::white);
                    g.drawRoundedRectangle(cellBox.toFloat().reduced(1.0f), 2.0f, 2.0f);
                }
'''
    new_inner_note_logic = '''                if (isCurrentStep)
                    g.setColour(juce::Colour(0xff5a5124));
                else if (isReferenceOctaveNote)
                    g.setColour(isInsideLoop ? juce::Colour(0xff263f45) : juce::Colour(0xff1c292d));
                else
                    g.setColour(isInsideLoop ? juce::Colour(0xff26363b) : juce::Colour(0xff1c292d));

                g.fillRoundedRectangle(cellBox.toFloat(), 2.0f);

                g.setColour(juce::Colour(0xff3b5056));
                g.drawRoundedRectangle(cellBox.toFloat(), 2.0f, 0.5f);

                if (isSelectedColumn)
                {
                    g.setColour(juce::Colour(0x66ffffff));
                    g.drawRoundedRectangle(cellBox.toFloat().reduced(1.0f), 2.0f, 1.0f);
                }
'''
    text = replace_once(text, old_inner_note_logic, new_inner_note_logic, "PluginEditor.cpp melody cell note drawing replaced by background drawing")

    insert_after = '''        }

        g.setColour(juce::Colour(0xffcfe8ef));
'''
    duration_bar_code = '''        }

        // Draw duration bars after the background grid has been drawn.
        for (int stepIndex = 0; stepIndex < gridStepCount; ++stepIndex)
        {
            if (!audioProcessor.stepHasNote(displayedPattern, stepIndex))
                continue;

            const int midiNote = audioProcessor.getStepNote(displayedPattern, stepIndex);

            if (midiNote < melodyLowestMidiNote || midiNote > melodyHighestMidiNote)
                continue;

            const int duration = juce::jlimit(1,
                gridStepCount,
                audioProcessor.getStepDurationSteps(displayedPattern, stepIndex));

            const int endStep = juce::jlimit(stepIndex,
                gridStepCount - 1,
                stepIndex + duration - 1);

            const int noteOffset = melodyHighestMidiNote - midiNote;

            const int x = gridArea.getX() + stepIndex * (cellWidth + stepGap);
            const int endX = gridArea.getX() + endStep * (cellWidth + stepGap) + cellWidth;
            const int y = gridArea.getY() + noteOffset * (cellHeight + noteGap);

            auto noteBar = juce::Rectangle<int>(
                x,
                y,
                endX - x,
                cellHeight).reduced(1, 1);

            const bool isCurrentStep = activePattern == displayedPattern
                && currentStep >= (stepIndex + 1)
                && currentStep <= (endStep + 1);

            const bool isSelectedNote = selectedEditPattern == displayedPattern
                && selectedStep == stepIndex;

            g.setColour(isCurrentStep
                ? juce::Colour(0xfff5c542)
                : juce::Colour(0xff5aa6b8));

            g.fillRoundedRectangle(noteBar.toFloat(), 3.0f);

            g.setColour(isCurrentStep ? juce::Colours::black : juce::Colours::white);
            g.drawRoundedRectangle(noteBar.toFloat(), 3.0f, 1.0f);

            g.setFont(10.0f);
            g.drawFittedText(juce::String(midiNote),
                noteBar.reduced(3, 1),
                juce::Justification::centredLeft,
                1);

            if (isSelectedNote)
            {
                g.setColour(juce::Colours::white);
                g.drawRoundedRectangle(noteBar.toFloat().reduced(1.0f), 3.0f, 2.0f);
            }
        }

        g.setColour(juce::Colour(0xffcfe8ef));
'''
    text = replace_once(text, insert_after, duration_bar_code, "PluginEditor.cpp insert melody duration bar drawing")
else:
    print("SKIP: duration bar drawing already present")

write(editor_cpp_path, text)

print("v1.15.0 Phase 4 patch applied successfully.")

