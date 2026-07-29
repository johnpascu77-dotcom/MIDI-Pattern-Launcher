#include "PluginProcessor.h"
#include "PluginEditor.h"

NewProjectAudioProcessorEditor::NewProjectAudioProcessorEditor(NewProjectAudioProcessor& p)
    : AudioProcessorEditor(&p),
    audioProcessor(p)
{
    setSize(720, 710);

    addAndMakeVisible(editPattern1Button);
    addAndMakeVisible(editPattern2Button);
    addAndMakeVisible(editPattern3Button);

    addAndMakeVisible(copyToP1Button);
    addAndMakeVisible(copyToP2Button);
    addAndMakeVisible(copyToP3Button);
    addAndMakeVisible(clearPatternButton);

    addAndMakeVisible(noteDownButton);
    addAndMakeVisible(noteUpButton);
    addAndMakeVisible(velocityDownButton);
    addAndMakeVisible(velocityUpButton);
    addAndMakeVisible(durationDownButton);
    addAndMakeVisible(durationUpButton);
    addAndMakeVisible(clearButton);
    addAndMakeVisible(makeNoteButton);

    addAndMakeVisible(transposeDownOctaveButton);
    addAndMakeVisible(transposeDownButton);
    addAndMakeVisible(transposeResetButton);
    addAndMakeVisible(transposeUpButton);
    addAndMakeVisible(transposeUpOctaveButton);

    addAndMakeVisible(rotationDownButton);
    addAndMakeVisible(rotationResetButton);
    addAndMakeVisible(rotationUpButton);
    addAndMakeVisible(inversionToggleButton);

    setupButtonCallbacks();
    updateEditPatternButtonHighlights();

    startTimerHz(20);
}

NewProjectAudioProcessorEditor::~NewProjectAudioProcessorEditor()
{
    stopTimer();
}

void NewProjectAudioProcessorEditor::setupButtonCallbacks()
{
    editPattern1Button.onClick = [this]()
        {
            selectedEditPattern = 0;
            updateEditPatternButtonHighlights();
            repaint();
        };

    editPattern2Button.onClick = [this]()
        {
            selectedEditPattern = 1;
            updateEditPatternButtonHighlights();
            repaint();
        };

    editPattern3Button.onClick = [this]()
        {
            selectedEditPattern = 2;
            updateEditPatternButtonHighlights();
            repaint();
        };

    copyToP1Button.onClick = [this]()
        {
            const int sourcePattern = getDisplayedPattern();
            audioProcessor.copyPattern(sourcePattern, 0);
            selectedEditPattern = 0;
            updateEditPatternButtonHighlights();
            repaint();
        };

    copyToP2Button.onClick = [this]()
        {
            const int sourcePattern = getDisplayedPattern();
            audioProcessor.copyPattern(sourcePattern, 1);
            selectedEditPattern = 1;
            updateEditPatternButtonHighlights();
            repaint();
        };

    copyToP3Button.onClick = [this]()
        {
            const int sourcePattern = getDisplayedPattern();
            audioProcessor.copyPattern(sourcePattern, 2);
            selectedEditPattern = 2;
            updateEditPatternButtonHighlights();
            repaint();
        };

    clearPatternButton.onClick = [this]()
        {
            audioProcessor.clearPattern(getDisplayedPattern());
            repaint();
        };

    noteDownButton.onClick = [this]()
        {
            audioProcessor.changeStepNote(getDisplayedPattern(), selectedStep, -1);
            repaint();
        };

    noteUpButton.onClick = [this]()
        {
            audioProcessor.changeStepNote(getDisplayedPattern(), selectedStep, 1);
            repaint();
        };

    velocityDownButton.onClick = [this]()
        {
            audioProcessor.changeStepVelocity(getDisplayedPattern(), selectedStep, -5);
            repaint();
        };

    velocityUpButton.onClick = [this]()
        {
            audioProcessor.changeStepVelocity(getDisplayedPattern(), selectedStep, 5);
            repaint();
        };

    durationDownButton.onClick = [this]()
        {
            audioProcessor.changeStepDuration(getDisplayedPattern(), selectedStep, -1);
            repaint();
        };

    durationUpButton.onClick = [this]()
        {
            audioProcessor.changeStepDuration(getDisplayedPattern(), selectedStep, 1);
            repaint();
        };

    clearButton.onClick = [this]()
        {
            audioProcessor.clearStep(getDisplayedPattern(), selectedStep);
            repaint();
        };

    makeNoteButton.onClick = [this]()
        {
            audioProcessor.makeStepNote(getDisplayedPattern(), selectedStep);
            repaint();
        };

    transposeDownOctaveButton.onClick = [this]()
        {
            const int pattern = getDisplayedPattern();
            audioProcessor.changePatternTranspose(pattern, -12);
            audioProcessor.updateAutomationParametersForPattern(pattern);
            repaint();
        };

    transposeDownButton.onClick = [this]()
        {
            const int pattern = getDisplayedPattern();
            audioProcessor.changePatternTranspose(pattern, -1);
            audioProcessor.updateAutomationParametersForPattern(pattern);
            repaint();
        };

    transposeResetButton.onClick = [this]()
        {
            const int pattern = getDisplayedPattern();
            audioProcessor.resetPatternTranspose(pattern);
            audioProcessor.updateAutomationParametersForPattern(pattern);
            repaint();
        };

    transposeUpButton.onClick = [this]()
        {
            const int pattern = getDisplayedPattern();
            audioProcessor.changePatternTranspose(pattern, 1);
            audioProcessor.updateAutomationParametersForPattern(pattern);
            repaint();
        };

    transposeUpOctaveButton.onClick = [this]()
        {
            const int pattern = getDisplayedPattern();
            audioProcessor.changePatternTranspose(pattern, 12);
            audioProcessor.updateAutomationParametersForPattern(pattern);
            repaint();
        };

    rotationDownButton.onClick = [this]()
        {
            const int pattern = getDisplayedPattern();
            audioProcessor.changePatternRotation(pattern, -1);
            audioProcessor.updateAutomationParametersForPattern(pattern);
            repaint();
        };

    rotationResetButton.onClick = [this]()
        {
            const int pattern = getDisplayedPattern();
            audioProcessor.resetPatternRotation(pattern);
            audioProcessor.updateAutomationParametersForPattern(pattern);
            repaint();
        };

    rotationUpButton.onClick = [this]()
        {
            const int pattern = getDisplayedPattern();
            audioProcessor.changePatternRotation(pattern, 1);
            audioProcessor.updateAutomationParametersForPattern(pattern);
            repaint();
        };

    inversionToggleButton.onClick = [this]()
        {
            const int pattern = getDisplayedPattern();
            audioProcessor.togglePatternInverted(pattern);
            audioProcessor.updateAutomationParametersForPattern(pattern);
            repaint();
        };
}

void NewProjectAudioProcessorEditor::updateEditPatternButtonHighlights()
{
    auto setButtonStyle = [](juce::TextButton& button, bool selected)
        {
            if (selected)
            {
                button.setColour(juce::TextButton::buttonColourId, juce::Colour(0xff5aa6b8));
                button.setColour(juce::TextButton::buttonOnColourId, juce::Colour(0xff5aa6b8));
                button.setColour(juce::TextButton::textColourOffId, juce::Colours::white);
                button.setColour(juce::TextButton::textColourOnId, juce::Colours::white);
            }
            else
            {
                button.setColour(juce::TextButton::buttonColourId, juce::Colour(0xff26363b));
                button.setColour(juce::TextButton::buttonOnColourId, juce::Colour(0xff26363b));
                button.setColour(juce::TextButton::textColourOffId, juce::Colour(0xffedf6f8));
                button.setColour(juce::TextButton::textColourOnId, juce::Colour(0xffedf6f8));
            }
        };

    setButtonStyle(editPattern1Button, selectedEditPattern == 0);
    setButtonStyle(editPattern2Button, selectedEditPattern == 1);
    setButtonStyle(editPattern3Button, selectedEditPattern == 2);
}

void NewProjectAudioProcessorEditor::timerCallback()
{
    updateEditPatternButtonHighlights();
    repaint();
}

juce::String NewProjectAudioProcessorEditor::patternNameFromValue(int value) const
{
    if (value == 0)
        return "Pattern 1";

    if (value == 1)
        return "Pattern 2";

    if (value == 2)
        return "Pattern 3";

    return "Stopped";
}

juce::String NewProjectAudioProcessorEditor::pendingNameFromValue(int value) const
{
    if (value == -2)
        return "None";

    if (value == -1)
        return "Stop";

    if (value == 0)
        return "Pattern 1";

    if (value == 1)
        return "Pattern 2";

    if (value == 2)
        return "Pattern 3";

    return "Unknown";
}

juce::String NewProjectAudioProcessorEditor::transposeTextFromValue(int value) const
{
    if (value > 0)
        return "+" + juce::String(value);

    return juce::String(value);
}

juce::String NewProjectAudioProcessorEditor::inversionTextFromValue(bool value) const
{
    return value ? "On" : "Off";
}

juce::String NewProjectAudioProcessorEditor::rotationTextFromValue(int value) const
{
    if (value > 0)
        return "+" + juce::String(value);

    return juce::String(value);
}

int NewProjectAudioProcessorEditor::getDisplayedPattern() const
{
    return selectedEditPattern;
}

juce::Rectangle<int> NewProjectAudioProcessorEditor::getStepArea() const
{
    auto bounds = getLocalBounds().reduced(24);

    bounds.removeFromTop(42);   // title
    bounds.removeFromTop(26);   // version
    bounds.removeFromTop(16);
    bounds.removeFromTop(112);  // status box
    bounds.removeFromTop(20);
    bounds.removeFromTop(24);   // editing pattern text
    bounds.removeFromTop(10);
    bounds.removeFromTop(38);   // edit pattern buttons
    bounds.removeFromTop(8);
    bounds.removeFromTop(34);   // pattern tools buttons
    bounds.removeFromTop(18);
    bounds.removeFromTop(24);   // monitor title
    bounds.removeFromTop(8);

    return bounds.removeFromTop(78);
}

juce::Rectangle<int> NewProjectAudioProcessorEditor::getStepBox(int stepIndex) const
{
    auto stepArea = getStepArea();

    const int numberOfSteps = 16;
    const int gap = 5;
    const int stepWidth = (stepArea.getWidth() - ((numberOfSteps - 1) * gap)) / numberOfSteps;
    const int stepHeight = 48;

    return juce::Rectangle<int>(stepArea.getX() + stepIndex * (stepWidth + gap),
        stepArea.getY(),
        stepWidth,
        stepHeight);
}

void NewProjectAudioProcessorEditor::updateSelectedStepFromMousePosition(juce::Point<int> position)
{
    for (int i = 0; i < 16; ++i)
    {
        if (getStepBox(i).contains(position))
        {
            selectedStep = i;
            repaint();
            return;
        }
    }
}

void NewProjectAudioProcessorEditor::mouseDown(const juce::MouseEvent& event)
{
    updateSelectedStepFromMousePosition(event.getPosition());
}

void NewProjectAudioProcessorEditor::paint(juce::Graphics& g)
{
    g.fillAll(juce::Colour(0xff2f3f45));

    const int activePattern = audioProcessor.getDisplayActivePattern();
    const int pendingPattern = audioProcessor.getDisplayPendingPattern();
    const int currentStep = audioProcessor.getDisplayCurrentStep();
    const int currentBar = audioProcessor.getDisplayCurrentBar();

    const int displayedPattern = getDisplayedPattern();
    const int patternTranspose = audioProcessor.getPatternTranspose(displayedPattern);
    const int patternRotation = audioProcessor.getPatternRotation(displayedPattern);
    const bool patternInverted = audioProcessor.getPatternInverted(displayedPattern);

    auto bounds = getLocalBounds().reduced(24);

    //==========================================================================
    // Title

    g.setColour(juce::Colours::white);
    g.setFont(22.0f);
    g.drawFittedText("MIDI Pattern Launcher",
        bounds.removeFromTop(42),
        juce::Justification::centred,
        1);

    g.setFont(14.0f);
    g.setColour(juce::Colour(0xffcfe8ef));
    g.drawFittedText("v1.9.0 - Pattern tools",
        bounds.removeFromTop(28),
        juce::Justification::centred,
        1);

    bounds.removeFromTop(16);

    //==========================================================================
    // Status box

    g.setColour(juce::Colour(0xff1f2d32));
    auto statusBox = bounds.removeFromTop(112);
    g.fillRoundedRectangle(statusBox.toFloat(), 8.0f);

    g.setColour(juce::Colours::white);
    g.setFont(16.0f);

    juce::String statusText;
    statusText << "Active Pattern: " << patternNameFromValue(activePattern) << "\n";
    statusText << "Pending: " << pendingNameFromValue(pendingPattern) << "\n";
    statusText << "Current Bar: " << currentBar << "\n";
    statusText << "Current Step: " << currentStep << " / 16";

    g.drawFittedText(statusText,
        statusBox.reduced(18),
        juce::Justification::centredLeft,
        4);

    bounds.removeFromTop(20);

    //==========================================================================
    // Edit pattern selector text

    g.setColour(juce::Colours::white);
    g.setFont(15.0f);

    juce::String selectorText;
    selectorText << "Editing Pattern: " << (displayedPattern + 1)
        << "    Playback Active: " << patternNameFromValue(activePattern)
        << "    Tr: " << transposeTextFromValue(patternTranspose)
        << "    Rot: " << rotationTextFromValue(patternRotation)
        << "    Inv: " << inversionTextFromValue(patternInverted);

    g.drawFittedText(selectorText,
        bounds.removeFromTop(24),
        juce::Justification::centredLeft,
        1);

    bounds.removeFromTop(10);

    // Reserve space for Edit P1/P2/P3 buttons.
    // The actual button bounds are set in resized().
    bounds.removeFromTop(38);

    bounds.removeFromTop(8);

    // Reserve space for pattern tool buttons.
    bounds.removeFromTop(34);

    bounds.removeFromTop(18);

    //==========================================================================
    // Visual pattern monitor title

    g.setColour(juce::Colours::white);
    g.setFont(16.0f);

    juce::String monitorTitle;
    monitorTitle << "Step Monitor/Edit: Edit Pattern " << (displayedPattern + 1);

    g.drawFittedText(monitorTitle,
        bounds.removeFromTop(24),
        juce::Justification::centredLeft,
        1);

    bounds.removeFromTop(8);

    // Reserve step row space. We draw using getStepBox() to keep mouse hit-test
    // and drawing positions perfectly matched.
    bounds.removeFromTop(78);

    const int numberOfSteps = 16;

    for (int i = 0; i < numberOfSteps; ++i)
    {
        auto stepBox = getStepBox(i);

        const bool hasNote = audioProcessor.stepHasNote(displayedPattern, i);
        const bool isCurrentStep = activePattern == displayedPattern && currentStep == (i + 1);
        const bool isSelectedStep = selectedStep == i;

        if (isCurrentStep)
            g.setColour(juce::Colour(0xfff5c542));
        else if (hasNote)
            g.setColour(juce::Colour(0xff5aa6b8));
        else
            g.setColour(juce::Colour(0xff26363b));

        g.fillRoundedRectangle(stepBox.toFloat(), 5.0f);

        if (isCurrentStep)
            g.setColour(juce::Colours::black);
        else
            g.setColour(juce::Colours::white);

        g.drawRoundedRectangle(stepBox.toFloat(), 5.0f, 1.0f);

        if (isSelectedStep)
        {
            g.setColour(juce::Colours::white);
            g.drawRoundedRectangle(stepBox.toFloat().reduced(1.5f), 5.0f, 3.0f);
        }

        if (isCurrentStep)
            g.setColour(juce::Colours::black);
        else
            g.setColour(juce::Colours::white);

        g.setFont(13.0f);

        juce::String stepText;
        stepText << (i + 1);

        if (hasNote)
        {
            const int note = audioProcessor.getStepNote(displayedPattern, i);
            const int duration = audioProcessor.getStepDurationSteps(displayedPattern, i);

            stepText << "\n";
            stepText << note;
            stepText << "\n";
            stepText << "d";
            stepText << duration;
        }
        else
        {
            stepText << "\n";
            stepText << "-";
        }

        g.drawFittedText(stepText,
            stepBox.reduced(3),
            juce::Justification::centred,
            3);
    }

    bounds.removeFromTop(14);

    //==========================================================================
    // Selected step editor display

    g.setColour(juce::Colour(0xff1f2d32));
    auto editorBox = bounds.removeFromTop(82);
    g.fillRoundedRectangle(editorBox.toFloat(), 8.0f);

    const bool selectedHasNote = audioProcessor.stepHasNote(displayedPattern, selectedStep);
    const int selectedNote = audioProcessor.getStepNote(displayedPattern, selectedStep);
    const int selectedTransformedNote = audioProcessor.getTransformedStepNote(displayedPattern, selectedStep);
    const int selectedVelocity = audioProcessor.getStepVelocity(displayedPattern, selectedStep);
    const int selectedDuration = audioProcessor.getStepDurationSteps(displayedPattern, selectedStep);

    g.setColour(juce::Colours::white);
    g.setFont(15.0f);

    juce::String editorText;
    editorText << "Selected Step: " << (selectedStep + 1) << "    ";
    editorText << "Edit Pattern: " << (displayedPattern + 1) << "    ";
    editorText << "Tr: " << transposeTextFromValue(patternTranspose) << "    ";
    editorText << "Rot: " << rotationTextFromValue(patternRotation) << "    ";
    editorText << "Inv: " << inversionTextFromValue(patternInverted) << "\n";

    if (selectedHasNote)
    {
        editorText << "Note: " << selectedNote;

        if (patternTranspose != 0 || patternInverted)
            editorText << " -> " << selectedTransformedNote;

        editorText << "    ";
        editorText << "Velocity: " << selectedVelocity << "    ";
        editorText << "Duration: d" << selectedDuration;
    }
    else
    {
        editorText << "Rest step";
    }

    g.drawFittedText(editorText,
        editorBox.reduced(16),
        juce::Justification::centredLeft,
        2);

    inversionToggleButton.setButtonText(patternInverted ? "Inv On" : "Inv Off");

    // Bottom controls are real buttons laid out in resized().
}

void NewProjectAudioProcessorEditor::resized()
{
    auto bounds = getLocalBounds().reduced(24);

    bounds.removeFromTop(42);   // title
    bounds.removeFromTop(26);   // version
    bounds.removeFromTop(16);
    bounds.removeFromTop(112);  // status box
    bounds.removeFromTop(20);
    bounds.removeFromTop(24);   // editing pattern text
    bounds.removeFromTop(10);

    auto editPatternRow = bounds.removeFromTop(38);

    const int selectorGap = 10;
    const int selectorButtonWidth = 105;

    editPattern1Button.setBounds(editPatternRow.removeFromLeft(selectorButtonWidth));
    editPatternRow.removeFromLeft(selectorGap);

    editPattern2Button.setBounds(editPatternRow.removeFromLeft(selectorButtonWidth));
    editPatternRow.removeFromLeft(selectorGap);

    editPattern3Button.setBounds(editPatternRow.removeFromLeft(selectorButtonWidth));

    bounds.removeFromTop(8);

    auto patternToolsRow = bounds.removeFromTop(34);

    const int toolsGap = 8;
    const int toolsButtonWidth = (patternToolsRow.getWidth() - (3 * toolsGap)) / 4;

    copyToP1Button.setBounds(patternToolsRow.removeFromLeft(toolsButtonWidth));
    patternToolsRow.removeFromLeft(toolsGap);

    copyToP2Button.setBounds(patternToolsRow.removeFromLeft(toolsButtonWidth));
    patternToolsRow.removeFromLeft(toolsGap);

    copyToP3Button.setBounds(patternToolsRow.removeFromLeft(toolsButtonWidth));
    patternToolsRow.removeFromLeft(toolsGap);

    clearPatternButton.setBounds(patternToolsRow.removeFromLeft(toolsButtonWidth));

    bounds.removeFromTop(18);
    bounds.removeFromTop(24);   // monitor title
    bounds.removeFromTop(8);
    bounds.removeFromTop(78);   // step area
    bounds.removeFromTop(14);
    bounds.removeFromTop(82);   // selected step display
    bounds.removeFromTop(18);

    auto buttonRow = bounds.removeFromTop(38);

    const int gap = 8;
    const int buttonWidth = (buttonRow.getWidth() - (7 * gap)) / 8;

    noteDownButton.setBounds(buttonRow.removeFromLeft(buttonWidth));
    buttonRow.removeFromLeft(gap);

    noteUpButton.setBounds(buttonRow.removeFromLeft(buttonWidth));
    buttonRow.removeFromLeft(gap);

    velocityDownButton.setBounds(buttonRow.removeFromLeft(buttonWidth));
    buttonRow.removeFromLeft(gap);

    velocityUpButton.setBounds(buttonRow.removeFromLeft(buttonWidth));
    buttonRow.removeFromLeft(gap);

    durationDownButton.setBounds(buttonRow.removeFromLeft(buttonWidth));
    buttonRow.removeFromLeft(gap);

    durationUpButton.setBounds(buttonRow.removeFromLeft(buttonWidth));
    buttonRow.removeFromLeft(gap);

    clearButton.setBounds(buttonRow.removeFromLeft(buttonWidth));
    buttonRow.removeFromLeft(gap);

    makeNoteButton.setBounds(buttonRow.removeFromLeft(buttonWidth));

    bounds.removeFromTop(14);

    //==========================================================================
    // v1.4.1:
    // Consolidated transform row.
    //
    // Transpose and rotation now share one horizontal row so the UI does not
    // continue growing vertically as more musical transformations are added.

    auto transformRow = bounds.removeFromTop(38);

    const int transformGap = 6;
    const int transformButtonWidth = 62;
    const int transformSectionGap = 14;

    transposeDownOctaveButton.setBounds(transformRow.removeFromLeft(transformButtonWidth));
    transformRow.removeFromLeft(transformGap);

    transposeDownButton.setBounds(transformRow.removeFromLeft(transformButtonWidth));
    transformRow.removeFromLeft(transformGap);

    transposeResetButton.setBounds(transformRow.removeFromLeft(transformButtonWidth));
    transformRow.removeFromLeft(transformGap);

    transposeUpButton.setBounds(transformRow.removeFromLeft(transformButtonWidth));
    transformRow.removeFromLeft(transformGap);

    transposeUpOctaveButton.setBounds(transformRow.removeFromLeft(transformButtonWidth));

    transformRow.removeFromLeft(transformSectionGap);

    rotationDownButton.setBounds(transformRow.removeFromLeft(transformButtonWidth));
    transformRow.removeFromLeft(transformGap);

    rotationResetButton.setBounds(transformRow.removeFromLeft(transformButtonWidth));
    transformRow.removeFromLeft(transformGap);

    rotationUpButton.setBounds(transformRow.removeFromLeft(transformButtonWidth));

    transformRow.removeFromLeft(transformSectionGap);

    inversionToggleButton.setBounds(transformRow.removeFromLeft(transformButtonWidth));
}
