#pragma once

#include <JuceHeader.h>
#include <vector>
#include <array>
#include <atomic>

class MidiPatternLauncherAudioProcessor : public juce::AudioProcessor
{
public:
    MidiPatternLauncherAudioProcessor();
    ~MidiPatternLauncherAudioProcessor() override;

    void prepareToPlay(double sampleRate, int samplesPerBlock) override;
    void releaseResources() override;

#ifndef JucePlugin_PreferredChannelConfigurations
    bool isBusesLayoutSupported(const BusesLayout& layouts) const override;
#endif

    void processBlock(juce::AudioBuffer<float>&, juce::MidiBuffer&) override;

    juce::AudioProcessorEditor* createEditor() override;
    bool hasEditor() const override;

    const juce::String getName() const override;

    bool acceptsMidi() const override;
    bool producesMidi() const override;
    bool isMidiEffect() const override;
    double getTailLengthSeconds() const override;

    int getNumPrograms() override;
    int getCurrentProgram() override;
    void setCurrentProgram(int index) override;
    const juce::String getProgramName(int index) override;
    void changeProgramName(int index, const juce::String& newName) override;

    void getStateInformation(juce::MemoryBlock& destData) override;
    void setStateInformation(const void* data, int sizeInBytes) override;

    juce::AudioProcessorValueTreeState& getAPVTS();
    void updateAutomationParametersForPattern(int patternIndex);

    int getGridModeIndex() const;
    int getGridStepCount() const;
    bool isTernaryGridMode() const;

    int getDisplayActivePattern() const;
    int getDisplayPendingPattern() const;
    int getDisplayCurrentStep() const;
    int getDisplayCurrentBar() const;

    bool stepHasNote(int patternIndex, int stepIndex) const;
    int getStepNote(int patternIndex, int stepIndex) const;
    int getStepVelocity(int patternIndex, int stepIndex) const;
    int getStepDurationSteps(int patternIndex, int stepIndex) const;

    void setStepValues(int patternIndex, int stepIndex, int note, int velocity, int durationSteps);
    void clearStep(int patternIndex, int stepIndex);
    void makeStepNote(int patternIndex, int stepIndex);
    void changeStepNote(int patternIndex, int stepIndex, int delta);
    void changeStepVelocity(int patternIndex, int stepIndex, int delta);
    void changeStepDuration(int patternIndex, int stepIndex, int delta);
    void copyPattern(int sourcePatternIndex, int destinationPatternIndex);
    void clearPattern(int patternIndex);

    int getTargetPatternIndex() const;
    int getTargetStepIndex() const;
    int getTargetNote() const;
    int getTargetVelocity() const;
    int getTargetDurationSteps() const;
    bool getTargetEnabled() const;

    void setTargetPatternAndStep(int patternIndex, int stepIndex);
    void updateTargetParametersFromStep();
    void applyTargetParametersToStep();

    int getPatternTranspose(int patternIndex) const;
    void changePatternTranspose(int patternIndex, int deltaSemitones);
    void resetPatternTranspose(int patternIndex);
    int getTransposedStepNote(int patternIndex, int stepIndex) const;
    int applyPatternTransformsToNote(int patternIndex, int note) const;

    int getPatternRotation(int patternIndex) const;
    void changePatternRotation(int patternIndex, int deltaSteps);
    void resetPatternRotation(int patternIndex);
    int getRotatedSourceStepIndex(int patternIndex, int playbackStepIndex) const;

    int getPatternLoopLength(int patternIndex) const;
    void setPatternLoopLength(int patternIndex, int length);
    void changePatternLoopLength(int patternIndex, int deltaSteps);

    bool getPatternInverted(int patternIndex) const;
    void togglePatternInverted(int patternIndex);
    void setPatternInverted(int patternIndex, bool shouldBeInverted);
    int getInvertedStepNote(int patternIndex, int stepIndex) const;
    int getTransformedStepNote(int patternIndex, int stepIndex) const;

private:
    static juce::AudioProcessorValueTreeState::ParameterLayout createParameterLayout();

    juce::AudioProcessorValueTreeState apvts;

    struct Step
    {
        int note = -1;
        int velocity = 0;
        int durationSteps = 0;
    };

    struct PendingNoteOff
    {
        int note = -1;
        int channel = 1;
        int targetStep = 0;
    };

    static constexpr int numPatterns = 3;

    // Maximum stored cells per pattern. v1.12.0 adds independent loop lengths,
    // but each pattern still stores 16 editable steps.
    static constexpr int patternLength = 16;

    static constexpr int minPatternLoopLength = 1;
    static constexpr int defaultPatternLoopLength = patternLength;

    static constexpr int stepsPerBar = 16;
    static constexpr double stepLengthInPpq = 0.25;

    using Pattern = std::array<Step, patternLength>;

    void initialisePatterns();
    void sendAllNotesOffNow(juce::MidiBuffer& midiMessages, int sampleOffset);
    Step getStepForPattern(int patternIndex, int stepIndex) const;

    void syncEngineFromParameters();
    void syncParametersFromPattern(int patternIndex);

    void syncTargetParametersFromStep();
    void syncTargetStepFromParameters();

    double mySampleRate = 44100.0;

    std::array<Pattern, numPatterns> patterns;

    // v1.3.0: non-destructive event-time transpose.
    std::array<int, numPatterns> patternTranspose{ 0, 0, 0 };

    // v1.4.0: non-destructive playback-time rotation.
    // 0 = no rotation.
    // +1 means stored material sounds one step later.
    std::array<int, numPatterns> patternRotation{ 0, 0, 0 };

    // v1.12.0: independent playback loop lengths.
    // Stored pattern data remains 16 steps, but each row may loop over 1..16 steps.
    std::array<int, numPatterns> patternLoopLength{
        defaultPatternLoopLength,
        defaultPatternLoopLength,
        defaultPatternLoopLength
    };

    // v1.5.0: non-destructive pitch inversion.
    // false = normal playback.
    // true  = mirror stored notes around inversionAxisNote before transposition.
    std::array<bool, numPatterns> patternInverted{ false, false, false };

    static constexpr int inversionAxisNote = 60;

    int getChoiceParameterIndex(const juce::String& parameterID) const;
    int getIntParameterValue(const juce::String& parameterID) const;
    bool getBoolParameterValue(const juce::String& parameterID) const;

    void setParameterPlainValueNotifyingHost(const juce::String& parameterID, float plainValue);

    std::atomic<bool> suppressParameterSync{ false };

    juce::String getTransposeParameterID(int patternIndex) const;
    juce::String getRotationParameterID(int patternIndex) const;
    juce::String getLengthParameterID(int patternIndex) const;
    juce::String getInversionParameterID(int patternIndex) const;

    int lastActivePatternParam = 0;

    int lastTargetPatternParam = 0;
    int lastTargetStepParam = 0;
    int lastTargetNoteParam = 60;
    int lastTargetVelocityParam = 100;
    int lastTargetDurationParam = 1;
    bool lastTargetEnabledParam = false;

    // Pattern state
    int activePattern = -1;        // -1 = stopped, 0/1/2 = active pattern
    int pendingPattern = -2;       // -2 = no pending change, -1 = pending stop, 0/1/2 = pending pattern

    // Timing state
    int patternStartStep = 0;
    int lastPlayedStep = -1;
    int lastLaunchBar = -1;

    std::vector<PendingNoteOff> pendingNoteOffs;

    // GUI display state. Written by audio thread, read by message thread.
    std::atomic<int> displayActivePattern{ -1 };
    std::atomic<int> displayPendingPattern{ -2 };
    std::atomic<int> displayCurrentStep{ 0 };
    std::atomic<int> displayCurrentBar{ 0 };

    bool wasHostPlaying = false;

    JUCE_DECLARE_NON_COPYABLE_WITH_LEAK_DETECTOR(MidiPatternLauncherAudioProcessor)
};

