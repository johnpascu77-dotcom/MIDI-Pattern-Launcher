#pragma once

#include <JuceHeader.h>
#include "PluginProcessor.h"

class MidiPatternLauncherAudioProcessorEditor : public juce::AudioProcessorEditor,
    private juce::Timer
{
public:
    explicit MidiPatternLauncherAudioProcessorEditor(MidiPatternLauncherAudioProcessor&);
    ~MidiPatternLauncherAudioProcessorEditor() override;

    void paint(juce::Graphics&) override;
    void resized() override;
    void mouseDown(const juce::MouseEvent& event) override;
    void mouseDrag(const juce::MouseEvent& event) override;
    void mouseUp(const juce::MouseEvent& event) override;

private:
    void timerCallback() override;

    juce::String patternNameFromValue(int value) const;
    juce::String pendingNameFromValue(int value) const;
    juce::String transposeTextFromValue(int value) const;
    juce::String rotationTextFromValue(int value) const;
    juce::String inversionTextFromValue(bool value) const;

    int getDisplayedPattern() const;
    juce::Rectangle<int> getPatternMatrixArea() const;
    juce::Rectangle<int> getPatternStepBox(int patternIndex, int stepIndex) const;

    bool getPatternStepAtPosition(juce::Point<int> position, int& patternIndexOut, int& stepIndexOut) const;
    void updateSelectedStepFromMousePosition(juce::Point<int> position);
    void toggleStepAtMousePosition(juce::Point<int> position);
    void setStepAtMousePosition(juce::Point<int> position, bool shouldHaveNote);
    void setPatternStepValue(int patternIndex, int stepIndex, bool shouldHaveNote);

    void setupButtonCallbacks();
    void updateEditPatternButtonHighlights();

    using ButtonAttachment = juce::AudioProcessorValueTreeState::ButtonAttachment;
    using ComboBoxAttachment = juce::AudioProcessorValueTreeState::ComboBoxAttachment;
    using SliderAttachment = juce::AudioProcessorValueTreeState::SliderAttachment;

    MidiPatternLauncherAudioProcessor& audioProcessor;

    int selectedStep = 0;
    int selectedEditPattern = 0;
    
    bool isDraggingPatternStepEdit = false;
    bool dragPaintValue = true;
    int lastEditedPattern = -1;
    int lastEditedStep = -1;

    juce::TextButton editPattern1Button{ "Edit P1" };
    juce::TextButton editPattern2Button{ "Edit P2" };
    juce::TextButton editPattern3Button{ "Edit P3" };

    juce::TextButton copyToP1Button{ "Copy > P1" };
    juce::TextButton copyToP2Button{ "Copy > P2" };
    juce::TextButton copyToP3Button{ "Copy > P3" };
    juce::TextButton clearPatternButton{ "Clear Pattern" };

    juce::TextButton noteDownButton{ "Note -" };
    juce::TextButton noteUpButton{ "Note +" };
    juce::TextButton velocityDownButton{ "Vel -" };
    juce::TextButton velocityUpButton{ "Vel +" };
    juce::TextButton durationDownButton{ "Dur -" };
    juce::TextButton durationUpButton{ "Dur +" };
    juce::TextButton clearButton{ "Clear Step" };
    juce::TextButton makeNoteButton{ "Make Note" };

    juce::TextButton transposeDownOctaveButton{ "Tr -12" };
    juce::TextButton transposeDownButton{ "Tr -" };
    juce::TextButton transposeResetButton{ "Tr 0" };
    juce::TextButton transposeUpButton{ "Tr +" };
    juce::TextButton transposeUpOctaveButton{ "Tr +12" };

    juce::TextButton rotationDownButton{ "Rot -" };
    juce::TextButton rotationResetButton{ "Rot 0" };
    juce::TextButton rotationUpButton{ "Rot +" };
    juce::TextButton inversionToggleButton{ "Inv Off" };

    juce::Label targetTitleLabel;
    juce::Label targetPatternLabel;
    juce::Label gridModeLabel;
    juce::Label targetStepLabel;
    juce::Label targetNoteLabel;
    juce::Label targetVelocityLabel;
    juce::Label targetDurationLabel;
    juce::Label targetEnabledLabel;

    juce::ComboBox targetPatternBox;
    juce::ComboBox gridModeBox;
    juce::Slider targetStepSlider;

    juce::Slider targetNoteSlider;
    juce::Slider targetVelocitySlider;
    juce::Slider targetDurationSlider;
    juce::ToggleButton targetEnabledButton{ "Enabled" };

    std::unique_ptr<ComboBoxAttachment> targetPatternAttachment;
    std::unique_ptr<ComboBoxAttachment> gridModeAttachment;
    std::unique_ptr<SliderAttachment> targetStepAttachment;
    std::unique_ptr<SliderAttachment> targetNoteAttachment;
    std::unique_ptr<SliderAttachment> targetVelocityAttachment;
    std::unique_ptr<SliderAttachment> targetDurationAttachment;
    std::unique_ptr<ButtonAttachment> targetEnabledAttachment;

    JUCE_DECLARE_NON_COPYABLE_WITH_LEAK_DETECTOR(MidiPatternLauncherAudioProcessorEditor)
};
