#include "PluginProcessor.h"
#include "PluginEditor.h"

NewProjectAudioProcessorEditor::NewProjectAudioProcessorEditor(NewProjectAudioProcessor& p)
    : AudioProcessorEditor(&p),
    audioProcessor(p)
{
    setSize(900, 760);

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

    auto setupLabel = [](juce::Label& label, const juce::String& text)
        {
            label.setText(text, juce::dontSendNotification);
            label.setColour(juce::Label::textColourId, juce::Colours::white);
            label.setJustificationType(juce::Justification::centredLeft);
        };

    setupLabel(targetTitleLabel, "Host Target Step Parameters");
    setupLabel(targetPatternLabel, "Pattern");
    setupLabel(targetStepLabel, "Step");
    setupLabel(targetNoteLabel, "Note");
    setupLabel(targetVelocityLabel, "Velocity");
    setupLabel(targetDurationLabel, "Duration");
    setupLabel(targetEnabledLabel, "Enabled");

    addAndMakeVisible(targetTitleLabel);
    addAndMakeVisible(targetPatternLabel);
    addAndMakeVisible(targetStepLabel);
    addAndMakeVisible(targetNoteLabel);
    addAndMakeVisible(targetVelocityLabel);
    addAndMakeVisible(targetDurationLabel);
    addAndMakeVisible(targetEnabledLabel);

    targetPatternBox.addItem("Pattern 1", 1);
    targetPatternBox.addItem("Pattern 2", 2);
    targetPatternBox.addItem("Pattern 3", 3);

    auto setupSlider = [](juce::Slider& slider)
        {
            slider.setSliderStyle(juce::Slider::IncDecButtons);
            slider.setTextBoxStyle(juce::Slider::TextBoxRight, false, 56, 22);
            slider.setColour(juce::Slider::textBoxTextColourId, juce::Colours::white);
            slider.setColour(juce::Slider::textBoxBackgroundColourId, juce::Colour(0xff1f2d32));
            slider.setColour(juce::Slider::textBoxOutlineColourId, juce::Colour(0xff5aa6b8));
        };

    setupSlider(targetStepSlider);
    setupSlider(targetNoteSlider);
    setupSlider(targetVelocitySlider);
    setupSlider(targetDurationSlider);

    addAndMakeVisible(targetPatternBox);
    addAndMakeVisible(targetStepSlider);
    addAndMakeVisible(targetNoteSlider);
    addAndMakeVisible(targetVelocitySlider);
    addAndMakeVisible(targetDurationSlider);
    addAndMakeVisible(targetEnabledButton);

    auto& apvts = audioProcessor.getAPVTS();

    targetPatternAttachment = std::make_unique<ComboBoxAttachment>(
        apvts, "targetPatternParam", targetPatternBox);

    targetStepAttachment = std::make_unique<SliderAttachment>(
        apvts, "targetStepParam", targetStepSlider);

    targetNoteAttachment = std::make_unique<SliderAttachment>(
        apvts, "targetNoteParam", targetNoteSlider);

    targetVelocityAttachment = std::make_unique<SliderAttachment>(
        apvts, "targetVelocityParam", targetVelocitySlider);

    targetDurationAttachment = std::make_unique<SliderAttachment>(
        apvts, "targetDurationParam", targetDurationSlider);

    targetEnabledAttachment = std::make_unique<ButtonAttachment>(
        apvts, "targetEnabledParam", targetEnabledButton);

    audioProcessor.setTargetPatternAndStep(selectedEditPattern, selectedStep);

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
            audioProcessor.setTargetPatternAndStep(selectedEditPattern, selectedStep);
            updateEditPatternButtonHighlights();
            repaint();
        };
    editPattern2Button.onClick = [this]()
        {
            selectedEditPattern = 1;
            audioProcessor.setTargetPatternAndStep(selectedEditPattern, selectedStep);
            updateEditPatternButtonHighlights();
            repaint();
        };

    editPattern3Button.onClick = [this]()
        {
            selectedEditPattern = 2;
            audioProcessor.setTargetPatternAndStep(selectedEditPattern, selectedStep);
            updateEditPatternButtonHighlights();
            repaint();
        };

    copyToP1Button.onClick = [this]()
        {
            const int sourcePattern = getDisplayedPattern();
            audioProcessor.copyPattern(sourcePattern, 0);
            selectedEditPattern = 0;
            audioProcessor.setTargetPatternAndStep(selectedEditPattern, selectedStep);
            updateEditPatternButtonHighlights();
            repaint();
        };

    copyToP2Button.onClick = [this]()
        {
            const int sourcePattern = getDisplayedPattern();
            audioProcessor.copyPattern(sourcePattern, 1);
            selectedEditPattern = 1;
            audioProcessor.setTargetPatternAndStep(selectedEditPattern, selectedStep);
            updateEditPatternButtonHighlights();
            repaint();
        };

    copyToP3Button.onClick = [this]()
        {
            const int sourcePattern = getDisplayedPattern();
            audioProcessor.copyPattern(sourcePattern, 2);
            selectedEditPattern = 2;
            audioProcessor.setTargetPatternAndStep(selectedEditPattern, selectedStep);
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
    selectedEditPattern = audioProcessor.getTargetPatternIndex();
    selectedStep = audioProcessor.getTargetStepIndex();

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

juce::Rectangle<int> NewProjectAudioProcessorEditor::getPatternMatrixArea() const
{
    auto bounds = getLocalBounds().reduced(24);

    bounds.removeFromTop(32);   // title/version row
    bounds.removeFromTop(24);   // compact status row
    bounds.removeFromTop(14);
    bounds.removeFromTop(24);   // matrix title
    bounds.removeFromTop(8);

    return bounds.removeFromTop(154);
}

juce::Rectangle<int> NewProjectAudioProcessorEditor::getPatternStepBox(int patternIndex, int stepIndex) const
{
    auto matrixArea = getPatternMatrixArea();

    const int numberOfPatterns = 3;
    const int numberOfSteps = 16;

    juce::ignoreUnused(numberOfPatterns);

    const int rowHeight = 42;
    const int rowGap = 8;
    const int labelWidth = 34;
    const int transformWidth = 132;
    const int labelGap = 8;
    const int transformGap = 12;
    const int stepGap = 4;

    const int availableStepWidth = matrixArea.getWidth()
        - labelWidth
        - labelGap
        - transformGap
        - transformWidth;

    const int stepWidth = (availableStepWidth - ((numberOfSteps - 1) * stepGap)) / numberOfSteps;

    const int x = matrixArea.getX()
        + labelWidth
        + labelGap
        + stepIndex * (stepWidth + stepGap);

    const int y = matrixArea.getY()
        + patternIndex * (rowHeight + rowGap);

    return juce::Rectangle<int>(x, y, stepWidth, rowHeight);
}

void NewProjectAudioProcessorEditor::updateSelectedStepFromMousePosition(juce::Point<int> position)
{
    for (int patternIndex = 0; patternIndex < 3; ++patternIndex)
    {
        for (int stepIndex = 0; stepIndex < 16; ++stepIndex)
        {
            if (getPatternStepBox(patternIndex, stepIndex).contains(position))
            {
                selectedEditPattern = patternIndex;
                selectedStep = stepIndex;

                selectedEditPattern = audioProcessor.getTargetPatternIndex();
                selectedStep = audioProcessor.getTargetStepIndex();
                updateEditPatternButtonHighlights();

                repaint();
                return;
            }
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
    // Compact title/header

    auto titleRow = bounds.removeFromTop(32);

    g.setColour(juce::Colours::white);
    g.setFont(22.0f);
    g.drawFittedText("MIDI Pattern Launcher",
        titleRow.removeFromLeft(titleRow.getWidth() / 2),
        juce::Justification::centredLeft,
        1);

    g.setFont(14.0f);
    g.setColour(juce::Colour(0xffcfe8ef));
    g.drawFittedText("v1.11.0 - Pattern matrix",
        titleRow,
        juce::Justification::centredRight,
        1);

    auto statusRow = bounds.removeFromTop(24);

    g.setColour(juce::Colour(0xffcfe8ef));
    g.setFont(15.0f);

    juce::String compactStatus;
    compactStatus << "Active: " << patternNameFromValue(activePattern)
        << "    Pending: " << pendingNameFromValue(pendingPattern)
        << "    Bar: " << currentBar
        << "    Step: " << currentStep << " / 16";

    g.drawFittedText(compactStatus,
        statusRow,
        juce::Justification::centred,
        1);

    bounds.removeFromTop(14);

    //==========================================================================
    // Pattern matrix title

    g.setColour(juce::Colours::white);
    g.setFont(16.0f);

    juce::String matrixTitle;
    matrixTitle << "Pattern Matrix / Target Edit"
        << "    Selected: P" << (displayedPattern + 1)
        << " Step " << (selectedStep + 1);

    g.drawFittedText(matrixTitle,
        bounds.removeFromTop(24),
        juce::Justification::centredLeft,
        1);

    bounds.removeFromTop(8);

    //==========================================================================
    // Pattern matrix

    auto matrixArea = getPatternMatrixArea();

    const int rowHeight = 42;
    const int rowGap = 8;
    const int labelWidth = 34;
    const int transformWidth = 132;
    const int labelGap = 8;
    const int transformGap = 12;

    for (int patternIndex = 0; patternIndex < 3; ++patternIndex)
    {
        const int rowY = matrixArea.getY() + patternIndex * (rowHeight + rowGap);

        auto labelBox = juce::Rectangle<int>(matrixArea.getX(),
            rowY,
            labelWidth,
            rowHeight);

        const bool isActivePattern = activePattern == patternIndex;
        const bool isPendingPattern = pendingPattern == patternIndex;
        const bool isSelectedPattern = displayedPattern == patternIndex;

        if (isActivePattern)
            g.setColour(juce::Colour(0xfff5c542));
        else if (isSelectedPattern)
            g.setColour(juce::Colour(0xff5aa6b8));
        else
            g.setColour(juce::Colour(0xff26363b));

        g.fillRoundedRectangle(labelBox.toFloat(), 5.0f);

        if (isPendingPattern)
        {
            g.setColour(juce::Colour(0xffff9f43));
            g.drawRoundedRectangle(labelBox.toFloat().reduced(1.0f), 5.0f, 2.0f);
        }
        else
        {
            g.setColour(juce::Colours::white);
            g.drawRoundedRectangle(labelBox.toFloat(), 5.0f, 1.0f);
        }

        g.setColour(isActivePattern ? juce::Colours::black : juce::Colours::white);
        g.setFont(15.0f);
        g.drawFittedText("P" + juce::String(patternIndex + 1),
            labelBox.reduced(3),
            juce::Justification::centred,
            1);

        for (int stepIndex = 0; stepIndex < 16; ++stepIndex)
        {
            auto stepBox = getPatternStepBox(patternIndex, stepIndex);

            const bool hasNote = audioProcessor.stepHasNote(patternIndex, stepIndex);
            const bool isCurrentStep = activePattern == patternIndex && currentStep == (stepIndex + 1);
            const bool isSelectedStep = selectedEditPattern == patternIndex && selectedStep == stepIndex;

            if (isCurrentStep)
                g.setColour(juce::Colour(0xfff5c542));
            else if (hasNote)
                g.setColour(juce::Colour(0xff5aa6b8));
            else
                g.setColour(juce::Colour(0xff26363b));

            g.fillRoundedRectangle(stepBox.toFloat(), 5.0f);

            g.setColour(isCurrentStep ? juce::Colours::black : juce::Colours::white);
            g.drawRoundedRectangle(stepBox.toFloat(), 5.0f, 1.0f);

            if (isSelectedStep)
            {
                g.setColour(juce::Colours::white);
                g.drawRoundedRectangle(stepBox.toFloat().reduced(1.5f), 5.0f, 3.0f);
            }

            g.setColour(isCurrentStep ? juce::Colours::black : juce::Colours::white);
            g.setFont(12.0f);

            juce::String stepText;
            stepText << (stepIndex + 1);

            if (hasNote)
            {
                const int note = audioProcessor.getStepNote(patternIndex, stepIndex);
                const int duration = audioProcessor.getStepDurationSteps(patternIndex, stepIndex);

                stepText << "\n" << note;
                stepText << "\n" << "d" << duration;
            }
            else
            {
                stepText << "\n-";
            }

            g.drawFittedText(stepText,
                stepBox.reduced(2),
                juce::Justification::centred,
                3);
        }

        const int transformX = matrixArea.getRight() - transformWidth;

        auto transformBox = juce::Rectangle<int>(transformX,
            rowY,
            transformWidth,
            rowHeight);

        const int rowTranspose = audioProcessor.getPatternTranspose(patternIndex);
        const int rowRotation = audioProcessor.getPatternRotation(patternIndex);
        const bool rowInverted = audioProcessor.getPatternInverted(patternIndex);

        juce::String transformText;
        transformText << "Tr " << transposeTextFromValue(rowTranspose)
            << "  Rot " << rotationTextFromValue(rowRotation)
            << "\nInv " << inversionTextFromValue(rowInverted);

        juce::ignoreUnused(transformGap);

        g.setColour(juce::Colour(0xffcfe8ef));
        g.setFont(13.0f);
        g.drawFittedText(transformText,
            transformBox,
            juce::Justification::centredLeft,
            2);
    }

    bounds.removeFromTop(154);
    bounds.removeFromTop(14);

    //==========================================================================
    // Selected step editor display

    g.setColour(juce::Colour(0xff1f2d32));
    auto editorBox = bounds.removeFromTop(62);
    g.fillRoundedRectangle(editorBox.toFloat(), 8.0f);

    const bool selectedHasNote = audioProcessor.stepHasNote(displayedPattern, selectedStep);
    const int selectedNote = audioProcessor.getStepNote(displayedPattern, selectedStep);
    const int selectedTransformedNote = audioProcessor.getTransformedStepNote(displayedPattern, selectedStep);
    const int selectedVelocity = audioProcessor.getStepVelocity(displayedPattern, selectedStep);
    const int selectedDuration = audioProcessor.getStepDurationSteps(displayedPattern, selectedStep);

    g.setColour(juce::Colours::white);
    g.setFont(15.0f);

    juce::String editorText;
    editorText << "Selected: P" << (displayedPattern + 1)
        << " Step " << (selectedStep + 1) << "    ";
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

    bounds.removeFromTop(32);   // title/version row
    bounds.removeFromTop(24);   // compact status row
    bounds.removeFromTop(14);
    bounds.removeFromTop(24);   // matrix title
    bounds.removeFromTop(8);
    bounds.removeFromTop(154);  // matrix area
    bounds.removeFromTop(14);
    bounds.removeFromTop(62);   // selected step display
    bounds.removeFromTop(16);

    //==========================================================================
    // Step edit buttons

    auto buttonRow = bounds.removeFromTop(36);

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

    bounds.removeFromTop(10);

    //==========================================================================
    // Pattern selection/tools row

    auto patternToolsRow = bounds.removeFromTop(36);

    const int toolsGap = 8;
    const int toolCount = 7;
    const int toolsButtonWidth = (patternToolsRow.getWidth() - ((toolCount - 1) * toolsGap)) / toolCount;

    editPattern1Button.setBounds(patternToolsRow.removeFromLeft(toolsButtonWidth));
    patternToolsRow.removeFromLeft(toolsGap);

    editPattern2Button.setBounds(patternToolsRow.removeFromLeft(toolsButtonWidth));
    patternToolsRow.removeFromLeft(toolsGap);

    editPattern3Button.setBounds(patternToolsRow.removeFromLeft(toolsButtonWidth));
    patternToolsRow.removeFromLeft(toolsGap);

    copyToP1Button.setBounds(patternToolsRow.removeFromLeft(toolsButtonWidth));
    patternToolsRow.removeFromLeft(toolsGap);

    copyToP2Button.setBounds(patternToolsRow.removeFromLeft(toolsButtonWidth));
    patternToolsRow.removeFromLeft(toolsGap);

    copyToP3Button.setBounds(patternToolsRow.removeFromLeft(toolsButtonWidth));
    patternToolsRow.removeFromLeft(toolsGap);

    clearPatternButton.setBounds(patternToolsRow.removeFromLeft(toolsButtonWidth));

    bounds.removeFromTop(10);

    //==========================================================================
    // Transform row

    auto transformRow = bounds.removeFromTop(36);

    const int transformGap = 6;
    const int transformButtonWidth = 66;
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

    bounds.removeFromTop(14);

    //==========================================================================
    // Host target parameters

    auto targetTitleRow = bounds.removeFromTop(22);
    targetTitleLabel.setBounds(targetTitleRow);

    bounds.removeFromTop(6);

    auto targetRow1 = bounds.removeFromTop(32);

    const int targetGap = 8;
    const int targetLabelWidth = 62;
    const int targetControlWidth = 160;

    targetPatternLabel.setBounds(targetRow1.removeFromLeft(targetLabelWidth));
    targetPatternBox.setBounds(targetRow1.removeFromLeft(targetControlWidth));
    targetRow1.removeFromLeft(targetGap);

    targetStepLabel.setBounds(targetRow1.removeFromLeft(targetLabelWidth));
    targetStepSlider.setBounds(targetRow1.removeFromLeft(targetControlWidth));
    targetRow1.removeFromLeft(targetGap);

    targetEnabledLabel.setBounds(targetRow1.removeFromLeft(targetLabelWidth));
    targetEnabledButton.setBounds(targetRow1.removeFromLeft(targetControlWidth));

    bounds.removeFromTop(6);

    auto targetRow2 = bounds.removeFromTop(32);

    targetNoteLabel.setBounds(targetRow2.removeFromLeft(targetLabelWidth));
    targetNoteSlider.setBounds(targetRow2.removeFromLeft(targetControlWidth));
    targetRow2.removeFromLeft(targetGap);

    targetVelocityLabel.setBounds(targetRow2.removeFromLeft(targetLabelWidth));
    targetVelocitySlider.setBounds(targetRow2.removeFromLeft(targetControlWidth));
    targetRow2.removeFromLeft(targetGap);

    targetDurationLabel.setBounds(targetRow2.removeFromLeft(targetLabelWidth));
    targetDurationSlider.setBounds(targetRow2.removeFromLeft(targetControlWidth));
}
