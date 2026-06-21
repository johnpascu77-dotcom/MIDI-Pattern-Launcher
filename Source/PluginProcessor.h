#pragma once

#include <JuceHeader.h>
#include <vector>
#include <array>
#include <atomic>

class NewProjectAudioProcessor : public juce::AudioProcessor
{
public:
    NewProjectAudioProcessor();
    ~NewProjectAudioProcessor() override;

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

    int getPatternTranspose(int patternIndex) const;
    void changePatternTranspose(int patternIndex, int deltaSemitones);
    void resetPatternTranspose(int patternIndex);
    int getTransposedStepNote(int patternIndex, int stepIndex) const;

    int getPatternRotation(int patternIndex) const;
    void changePatternRotation(int patternIndex, int deltaSteps);
    void resetPatternRotation(int patternIndex);
    int getRotatedSourceStepIndex(int patternIndex, int playbackStepIndex) const;

private:
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
    static constexpr int patternLength = 16;
    static constexpr int stepsPerBar = 16;
    static constexpr double stepLengthInPpq = 0.25;

    using Pattern = std::array<Step, patternLength>;

    void initialisePatterns();
    void sendAllNotesOffNow(juce::MidiBuffer& midiMessages, int sampleOffset);
    Step getStepForPattern(int patternIndex, int stepIndex) const;

    double mySampleRate = 44100.0;

    std::array<Pattern, numPatterns> patterns;

    // v1.3.0: non-destructive event-time transpose.
    std::array<int, numPatterns> patternTranspose{ 0, 0, 0 };

    // v1.4.0: non-destructive playback-time rotation.
    // 0 = no rotation.
    // +1 means stored material sounds one step later.
    std::array<int, numPatterns> patternRotation{ 0, 0, 0 };

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

    JUCE_DECLARE_NON_COPYABLE_WITH_LEAK_DETECTOR(NewProjectAudioProcessor)
};
