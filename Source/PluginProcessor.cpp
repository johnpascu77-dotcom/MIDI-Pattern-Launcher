#include "PluginProcessor.h"
#include "PluginEditor.h"

#include <cmath>
#include <algorithm>

//==============================================================================
NewProjectAudioProcessor::NewProjectAudioProcessor()
#ifndef JucePlugin_PreferredChannelConfigurations
    : AudioProcessor(BusesProperties()),
    apvts(*this, nullptr, "Parameters", createParameterLayout())
#else
    : apvts(*this, nullptr, "Parameters", createParameterLayout())
#endif
{
    initialisePatterns();
}

NewProjectAudioProcessor::~NewProjectAudioProcessor()
{
}

juce::AudioProcessorValueTreeState::ParameterLayout NewProjectAudioProcessor::createParameterLayout()
{
    std::vector<std::unique_ptr<juce::RangedAudioParameter>> parameters;

    parameters.push_back(std::make_unique<juce::AudioParameterChoice>(
        juce::ParameterID("activePatternParam", 1),
        "Active Pattern",
        juce::StringArray{ "Stopped", "Pattern 1", "Pattern 2", "Pattern 3" },
        0));

    parameters.push_back(std::make_unique<juce::AudioParameterChoice>(
        juce::ParameterID("targetPatternParam", 1),
        "Target Pattern",
        juce::StringArray{ "Pattern 1", "Pattern 2", "Pattern 3" },
        0));

    parameters.push_back(std::make_unique<juce::AudioParameterInt>(
        juce::ParameterID("transposeParam", 1),
        "Transpose",
        -48,
        48,
        0));

    parameters.push_back(std::make_unique<juce::AudioParameterInt>(
        juce::ParameterID("rotationParam", 1),
        "Rotation",
        0,
        15,
        0));

    parameters.push_back(std::make_unique<juce::AudioParameterBool>(
        juce::ParameterID("inversionParam", 1),
        "Inversion",
        false));

    return { parameters.begin(), parameters.end() };
}

juce::AudioProcessorValueTreeState& NewProjectAudioProcessor::getAPVTS()
{
    return apvts;
}

void NewProjectAudioProcessor::updateAutomationParametersForPattern(int patternIndex)
{
    syncParametersFromPattern(patternIndex);
}

void NewProjectAudioProcessor::syncParametersFromPattern(int patternIndex)
{
    if (patternIndex < 0 || patternIndex >= numPatterns)
        return;

    const int transpose = getPatternTranspose(patternIndex);
    const int rotation = getPatternRotation(patternIndex);
    const bool inversion = getPatternInverted(patternIndex);

    if (auto* parameter = apvts.getParameter("transposeParam"))
        parameter->setValueNotifyingHost(parameter->convertTo0to1(static_cast<float>(transpose)));

    if (auto* parameter = apvts.getParameter("rotationParam"))
        parameter->setValueNotifyingHost(parameter->convertTo0to1(static_cast<float>(rotation)));

    if (auto* parameter = apvts.getParameter("inversionParam"))
        parameter->setValueNotifyingHost(inversion ? 1.0f : 0.0f);

    lastTransposeParam = transpose;
    lastRotationParam = rotation;
    lastInversionParam = inversion;
}

void NewProjectAudioProcessor::syncEngineFromParameters()
{
    auto* activePatternValue = apvts.getRawParameterValue("activePatternParam");
    auto* targetPatternValue = apvts.getRawParameterValue("targetPatternParam");
    auto* transposeValue = apvts.getRawParameterValue("transposeParam");
    auto* rotationValue = apvts.getRawParameterValue("rotationParam");
    auto* inversionValue = apvts.getRawParameterValue("inversionParam");

    if (activePatternValue == nullptr
        || targetPatternValue == nullptr
        || transposeValue == nullptr
        || rotationValue == nullptr
        || inversionValue == nullptr)
    {
        return;
    }

    const int activeParam = juce::jlimit(0, numPatterns, static_cast<int>(std::round(activePatternValue->load())));
    const int targetParam = juce::jlimit(0, numPatterns - 1, static_cast<int>(std::round(targetPatternValue->load())));
    const int transposeParam = juce::jlimit(-48, 48, static_cast<int>(std::round(transposeValue->load())));
    const int rotationParam = juce::jlimit(0, patternLength - 1, static_cast<int>(std::round(rotationValue->load())));
    const bool inversionParam = inversionValue->load() >= 0.5f;

    if (activeParam != lastActivePatternParam)
    {
        const int requestedPattern = activeParam - 1; // 0 = stopped, 1..3 = pattern 0..2

        if (requestedPattern != activePattern)
        {
            pendingPattern = requestedPattern;
            displayPendingPattern.store(pendingPattern);
        }

        lastActivePatternParam = activeParam;
    }

    if (targetParam != lastTargetPatternParam)
    {
        lastTargetPatternParam = targetParam;
        syncParametersFromPattern(targetParam);
        return;
    }

    if (targetParam >= 0 && targetParam < numPatterns)
    {
        patternTranspose[static_cast<size_t>(targetParam)] = transposeParam;
        patternRotation[static_cast<size_t>(targetParam)] = rotationParam;
        patternInverted[static_cast<size_t>(targetParam)] = inversionParam;

        lastTransposeParam = transposeParam;
        lastRotationParam = rotationParam;
        lastInversionParam = inversionParam;
    }
}
//==============================================================================
void NewProjectAudioProcessor::initialisePatterns()
{
    for (auto& pattern : patterns)
    {
        for (auto& step : pattern)
            step = Step{};
    }

    // Pattern 1:
    // C eighth, E eighth, G quarter, C quarter, G eighth, E eighth
    patterns[0] =
    {
        Step { 60, 110, 2 },
        Step { -1,   0, 0 },
        Step { 64,  90, 2 },
        Step { -1,   0, 0 },
        Step { 67, 100, 4 },
        Step { -1,   0, 0 },
        Step { -1,   0, 0 },
        Step { -1,   0, 0 },
        Step { 72, 105, 4 },
        Step { -1,   0, 0 },
        Step { -1,   0, 0 },
        Step { -1,   0, 0 },
        Step { 67,  85, 2 },
        Step { -1,   0, 0 },
        Step { 64,  80, 2 },
        Step { -1,   0, 0 }
    };

    // Pattern 2:
    // Bass phrase.
    patterns[1] =
    {
        Step { 48, 120, 4 },
        Step { -1,   0, 0 },
        Step { -1,   0, 0 },
        Step { -1,   0, 0 },
        Step { 55,  90, 2 },
        Step { -1,   0, 0 },
        Step { 57, 100, 2 },
        Step { -1,   0, 0 },
        Step { 55,  95, 4 },
        Step { -1,   0, 0 },
        Step { -1,   0, 0 },
        Step { -1,   0, 0 },
        Step { 48, 110, 4 },
        Step { -1,   0, 0 },
        Step { -1,   0, 0 },
        Step { -1,   0, 0 }
    };

    // Pattern 3:
    // Simple melodic phrase.
    patterns[2] =
    {
        Step { 60, 105, 2 },
        Step { -1,   0, 0 },
        Step { 62,  80, 2 },
        Step { -1,   0, 0 },
        Step { 64,  95, 4 },
        Step { -1,   0, 0 },
        Step { -1,   0, 0 },
        Step { -1,   0, 0 },
        Step { 67, 115, 2 },
        Step { -1,   0, 0 },
        Step { 64,  85, 2 },
        Step { -1,   0, 0 },
        Step { 62,  75, 2 },
        Step { -1,   0, 0 },
        Step { 60, 100, 2 },
        Step { -1,   0, 0 }
    };

    patternTranspose = { 0, 0, 0 };
    patternRotation = { 0, 0, 0 };
    patternInverted = { false, false, false };
}

NewProjectAudioProcessor::Step NewProjectAudioProcessor::getStepForPattern(int patternIndex,
    int stepIndex) const
{
    if (patternIndex < 0 || patternIndex >= numPatterns)
        return Step{};

    stepIndex = ((stepIndex % patternLength) + patternLength) % patternLength;

    return patterns[static_cast<size_t>(patternIndex)]
        [static_cast<size_t>(stepIndex)];
}

//==============================================================================
int NewProjectAudioProcessor::getDisplayActivePattern() const
{
    return displayActivePattern.load();
}

int NewProjectAudioProcessor::getDisplayPendingPattern() const
{
    return displayPendingPattern.load();
}

int NewProjectAudioProcessor::getDisplayCurrentStep() const
{
    return displayCurrentStep.load();
}

int NewProjectAudioProcessor::getDisplayCurrentBar() const
{
    return displayCurrentBar.load();
}

bool NewProjectAudioProcessor::stepHasNote(int patternIndex, int stepIndex) const
{
    const Step step = getStepForPattern(patternIndex, stepIndex);

    return step.note >= 0
        && step.velocity > 0
        && step.durationSteps > 0;
}

int NewProjectAudioProcessor::getStepNote(int patternIndex, int stepIndex) const
{
    return getStepForPattern(patternIndex, stepIndex).note;
}

int NewProjectAudioProcessor::getStepVelocity(int patternIndex, int stepIndex) const
{
    return getStepForPattern(patternIndex, stepIndex).velocity;
}

int NewProjectAudioProcessor::getStepDurationSteps(int patternIndex, int stepIndex) const
{
    return getStepForPattern(patternIndex, stepIndex).durationSteps;
}

void NewProjectAudioProcessor::setStepValues(int patternIndex,
    int stepIndex,
    int note,
    int velocity,
    int durationSteps)
{
    if (patternIndex < 0 || patternIndex >= numPatterns)
        return;

    if (stepIndex < 0 || stepIndex >= patternLength)
        return;

    auto& step = patterns[static_cast<size_t>(patternIndex)]
        [static_cast<size_t>(stepIndex)];

    if (note < 0 || velocity <= 0 || durationSteps <= 0)
    {
        step.note = -1;
        step.velocity = 0;
        step.durationSteps = 0;
        return;
    }

    step.note = juce::jlimit(0, 127, note);
    step.velocity = juce::jlimit(1, 127, velocity);
    step.durationSteps = juce::jlimit(1, 16, durationSteps);
}

void NewProjectAudioProcessor::clearStep(int patternIndex, int stepIndex)
{
    setStepValues(patternIndex, stepIndex, -1, 0, 0);
}

void NewProjectAudioProcessor::makeStepNote(int patternIndex, int stepIndex)
{
    if (stepHasNote(patternIndex, stepIndex))
        return;

    setStepValues(patternIndex, stepIndex, 60, 100, 1);
}

void NewProjectAudioProcessor::changeStepNote(int patternIndex, int stepIndex, int delta)
{
    Step step = getStepForPattern(patternIndex, stepIndex);

    if (step.note < 0)
    {
        setStepValues(patternIndex, stepIndex, 60, 100, 1);
        return;
    }

    setStepValues(patternIndex,
        stepIndex,
        step.note + delta,
        step.velocity,
        step.durationSteps);
}

void NewProjectAudioProcessor::changeStepVelocity(int patternIndex, int stepIndex, int delta)
{
    Step step = getStepForPattern(patternIndex, stepIndex);

    if (step.note < 0)
    {
        setStepValues(patternIndex, stepIndex, 60, 100, 1);
        return;
    }

    setStepValues(patternIndex,
        stepIndex,
        step.note,
        step.velocity + delta,
        step.durationSteps);
}

void NewProjectAudioProcessor::changeStepDuration(int patternIndex, int stepIndex, int delta)
{
    Step step = getStepForPattern(patternIndex, stepIndex);

    if (step.note < 0)
    {
        setStepValues(patternIndex, stepIndex, 60, 100, 1);
        return;
    }

    setStepValues(patternIndex,
        stepIndex,
        step.note,
        step.velocity,
        step.durationSteps + delta);
}

//==============================================================================
// v1.3.0 transpose helpers.
// These are non-destructive: they do not change the stored step notes.

int NewProjectAudioProcessor::getPatternTranspose(int patternIndex) const
{
    if (patternIndex < 0 || patternIndex >= numPatterns)
        return 0;

    return patternTranspose[static_cast<size_t>(patternIndex)];
}

void NewProjectAudioProcessor::changePatternTranspose(int patternIndex, int deltaSemitones)
{
    if (patternIndex < 0 || patternIndex >= numPatterns)
        return;

    auto& transpose = patternTranspose[static_cast<size_t>(patternIndex)];
    transpose = juce::jlimit(-48, 48, transpose + deltaSemitones);
}

void NewProjectAudioProcessor::resetPatternTranspose(int patternIndex)
{
    if (patternIndex < 0 || patternIndex >= numPatterns)
        return;

    patternTranspose[static_cast<size_t>(patternIndex)] = 0;
}

int NewProjectAudioProcessor::getTransposedStepNote(int patternIndex, int stepIndex) const
{
    const Step step = getStepForPattern(patternIndex, stepIndex);

    if (step.note < 0)
        return -1;

    return juce::jlimit(0, 127, step.note + getPatternTranspose(patternIndex));
}
//==============================================================================
// v1.5.0 inversion helpers.
// These are non-destructive: stored step notes are never rewritten.
//
// Transform order:
//   Stored Note -> Inversion -> Transposition -> MIDI Output
//
// Inversion axis:
//   60 = middle C / C4.
//   Example:
//     64 becomes 56
//     67 becomes 53
//     60 remains 60

bool NewProjectAudioProcessor::getPatternInverted(int patternIndex) const
{
    if (patternIndex < 0 || patternIndex >= numPatterns)
        return false;

    return patternInverted[static_cast<size_t>(patternIndex)];
}

void NewProjectAudioProcessor::togglePatternInverted(int patternIndex)
{
    if (patternIndex < 0 || patternIndex >= numPatterns)
        return;

    auto& inverted = patternInverted[static_cast<size_t>(patternIndex)];
    inverted = !inverted;
}

void NewProjectAudioProcessor::setPatternInverted(int patternIndex, bool shouldBeInverted)
{
    if (patternIndex < 0 || patternIndex >= numPatterns)
        return;

    patternInverted[static_cast<size_t>(patternIndex)] = shouldBeInverted;
}

int NewProjectAudioProcessor::applyPatternTransformsToNote(int patternIndex, int note) const
{
    if (note < 0)
        return -1;

    int transformedNote = note;

    if (getPatternInverted(patternIndex))
        transformedNote = (inversionAxisNote * 2) - transformedNote;

    transformedNote += getPatternTranspose(patternIndex);

    return juce::jlimit(0, 127, transformedNote);
}

int NewProjectAudioProcessor::getInvertedStepNote(int patternIndex, int stepIndex) const
{
    const Step step = getStepForPattern(patternIndex, stepIndex);

    if (step.note < 0)
        return -1;

    if (!getPatternInverted(patternIndex))
        return step.note;

    return juce::jlimit(0, 127, (inversionAxisNote * 2) - step.note);
}

int NewProjectAudioProcessor::getTransformedStepNote(int patternIndex, int stepIndex) const
{
    const Step step = getStepForPattern(patternIndex, stepIndex);

    if (step.note < 0)
        return -1;

    return applyPatternTransformsToNote(patternIndex, step.note);
}
//==============================================================================
// v1.4.0 rotation helpers.
// These are non-destructive: they do not move or rewrite stored step data.
//
// Rotation meaning:
//   0  = no rotation
//   +1 = stored material sounds one step later
//   +2 = stored material sounds two steps later
//
// Therefore, when playback is currently at stepIndex, we read from:
//
//   sourceStepIndex = stepIndex - rotation
//
// with wraparound inside 0..15.

int NewProjectAudioProcessor::getPatternRotation(int patternIndex) const
{
    if (patternIndex < 0 || patternIndex >= numPatterns)
        return 0;

    return patternRotation[static_cast<size_t>(patternIndex)];
}

void NewProjectAudioProcessor::changePatternRotation(int patternIndex, int deltaSteps)
{
    if (patternIndex < 0 || patternIndex >= numPatterns)
        return;

    auto& rotation = patternRotation[static_cast<size_t>(patternIndex)];

    rotation += deltaSteps;
    rotation = ((rotation % patternLength) + patternLength) % patternLength;
}

void NewProjectAudioProcessor::resetPatternRotation(int patternIndex)
{
    if (patternIndex < 0 || patternIndex >= numPatterns)
        return;

    patternRotation[static_cast<size_t>(patternIndex)] = 0;
}

int NewProjectAudioProcessor::getRotatedSourceStepIndex(int patternIndex,
    int playbackStepIndex) const
{
    const int rotation = getPatternRotation(patternIndex);

    return ((playbackStepIndex - rotation) % patternLength + patternLength) % patternLength;
}

//==============================================================================
const juce::String NewProjectAudioProcessor::getName() const
{
    return JucePlugin_Name;
}

bool NewProjectAudioProcessor::acceptsMidi() const
{
#if JucePlugin_WantsMidiInput
    return true;
#else
    return false;
#endif
}

bool NewProjectAudioProcessor::producesMidi() const
{
#if JucePlugin_ProducesMidiOutput
    return true;
#else
    return false;
#endif
}

bool NewProjectAudioProcessor::isMidiEffect() const
{
#if JucePlugin_IsMidiEffect
    return true;
#else
    return false;
#endif
}

double NewProjectAudioProcessor::getTailLengthSeconds() const
{
    return 0.0;
}

int NewProjectAudioProcessor::getNumPrograms()
{
    return 1;
}

int NewProjectAudioProcessor::getCurrentProgram()
{
    return 0;
}

void NewProjectAudioProcessor::setCurrentProgram(int index)
{
    juce::ignoreUnused(index);
}

const juce::String NewProjectAudioProcessor::getProgramName(int index)
{
    juce::ignoreUnused(index);
    return {};
}

void NewProjectAudioProcessor::changeProgramName(int index, const juce::String& newName)
{
    juce::ignoreUnused(index, newName);
}

//==============================================================================
void NewProjectAudioProcessor::prepareToPlay(double sampleRate, int samplesPerBlock)
{
    juce::ignoreUnused(samplesPerBlock);

    mySampleRate = sampleRate;

    activePattern = -1;
    pendingPattern = -2;

    patternStartStep = 0;
    lastPlayedStep = -1;
    lastLaunchBar = -1;

    wasHostPlaying = false;

    pendingNoteOffs.clear();

    displayActivePattern.store(-1);
    displayPendingPattern.store(-2);
    displayCurrentStep.store(0);
    displayCurrentBar.store(0);
}

void NewProjectAudioProcessor::releaseResources()
{
    pendingNoteOffs.clear();
}

#ifndef JucePlugin_PreferredChannelConfigurations
bool NewProjectAudioProcessor::isBusesLayoutSupported(const BusesLayout& layouts) const
{
    juce::ignoreUnused(layouts);
    return true;
}
#endif

//==============================================================================
// Central MIDI safety cleanup.
//
// This intentionally sends individual note-offs for all 128 notes and an
// All Notes Off message. The individual note-offs are the important part for
// stubborn instruments/hosts that do not fully react to CC-style panic messages.

void NewProjectAudioProcessor::sendAllNotesOffNow(juce::MidiBuffer& midiMessages, int sampleOffset)
{
    for (int note = 0; note < 128; ++note)
        midiMessages.addEvent(juce::MidiMessage::noteOff(1, note), sampleOffset);

    midiMessages.addEvent(juce::MidiMessage::allNotesOff(1), sampleOffset);

    pendingNoteOffs.clear();
}

void NewProjectAudioProcessor::processBlock(juce::AudioBuffer<float>& buffer,
    juce::MidiBuffer& midiMessages)
{
    buffer.clear();

    syncEngineFromParameters();

    //==========================================================================
    // 1. Read incoming MIDI trigger notes.
    // Trigger notes are consumed and not passed through.

    juce::MidiBuffer incomingMidi;
    incomingMidi.swapWith(midiMessages);

    midiMessages.clear();

    for (const auto metadata : incomingMidi)
    {
        const auto message = metadata.getMessage();

        if (message.isNoteOn())
        {
            const int noteNumber = message.getNoteNumber();

            int requestedPattern = -999;

            if (noteNumber == 36)
                requestedPattern = 0;
            else if (noteNumber == 38)
                requestedPattern = 1;
            else if (noteNumber == 40)
                requestedPattern = 2;

            if (requestedPattern != -999)
            {
                if (requestedPattern == activePattern)
                    pendingPattern = -1;    // Queue stop.
                else
                    pendingPattern = requestedPattern;

                displayPendingPattern.store(pendingPattern);
            }
        }
    }

    //==========================================================================
    // 2. Get host transport position.

    auto* hostPlayHead = getPlayHead();

    if (hostPlayHead == nullptr)
        return;

    auto position = hostPlayHead->getPosition();

    if (!position.hasValue())
        return;

    const auto isPlaying = position->getIsPlaying();

    // Immediate transport-stop panic.
    //
    // This handles the classic stuck-note case:
    // a note-on has been sent, but its scheduled future note-off would never
    // arrive because the host stopped before that musical position.
    if (wasHostPlaying && !isPlaying)
    {
        sendAllNotesOffNow(midiMessages, 0);
        displayCurrentStep.store(0);
    }

    wasHostPlaying = isPlaying;

    if (!isPlaying)
    {
        lastPlayedStep = -1;
        lastLaunchBar = -1;

        // sendAllNotesOffNow() already clears pendingNoteOffs on the actual
        // playing->stopped transition. This extra clear is harmless and keeps
        // internal state clean even if processing starts while stopped.
        pendingNoteOffs.clear();

        displayCurrentStep.store(0);
        return;
    }

    auto ppqPosition = position->getPpqPosition();

    if (!ppqPosition.hasValue())
        return;

    double bpmValue = 120.0;

    auto bpm = position->getBpm();

    if (bpm.hasValue() && *bpm > 0.0)
        bpmValue = *bpm;

    const double ppqStart = *ppqPosition;

    //==========================================================================
    // 3. Timing setup.

    const int numSamples = buffer.getNumSamples();

    const double quarterNotesPerSecond = bpmValue / 60.0;
    const double ppqPerSample = quarterNotesPerSecond / mySampleRate;

    if (ppqPerSample <= 0.0)
        return;

    const double ppqEnd = ppqStart + (ppqPerSample * static_cast<double> (numSamples));

    //==========================================================================
    // 4. Determine which sixteenth-note grid lines occur inside this block.

    const int firstStepInBlock = static_cast<int> (std::ceil(ppqStart / stepLengthInPpq));
    const int lastStepInBlock = static_cast<int> (std::floor(ppqEnd / stepLengthInPpq));

    constexpr int midiChannel = 1;

    for (int step = firstStepInBlock; step <= lastStepInBlock; ++step)
    {
        const double stepPpq = static_cast<double> (step) * stepLengthInPpq;

        int sampleOffset = static_cast<int> (std::round((stepPpq - ppqStart) / ppqPerSample));
        sampleOffset = juce::jlimit(0, numSamples - 1, sampleOffset);

        const int currentBar = step / stepsPerBar;
        const int displayStep = (step % stepsPerBar) + 1;
        const bool isAtBarStart = (step % stepsPerBar) == 0;

        displayCurrentBar.store(currentBar + 1);
        displayCurrentStep.store(displayStep);
        displayActivePattern.store(activePattern);
        displayPendingPattern.store(pendingPattern);

        //======================================================================
        // 4a. Send pending note-offs exactly on their musical target step.
        //
        // Important for transpose and rotation:
        // PendingNoteOff stores the exact MIDI note that was originally sent.
        // Therefore, if transpose or rotation changes while a note is held,
        // the correct note-off is still sent.

        for (auto it = pendingNoteOffs.begin(); it != pendingNoteOffs.end(); )
        {
            if (step >= it->targetStep)
            {
                midiMessages.addEvent(juce::MidiMessage::noteOff(it->channel, it->note),
                    sampleOffset);

                it = pendingNoteOffs.erase(it);
            }
            else
            {
                ++it;
            }
        }

        //======================================================================
        // 4b. Apply queued launch/stop only at the start of a new bar.
        //
        // Important safety behavior:
        // Before a pattern stop or switch is applied, force all currently
        // sounding notes off at the exact bar-boundary sample offset.
        //
        // This prevents long notes from the previous pattern from leaking into
        // the stopped state or into the next pattern.

        if (pendingPattern != -2 && isAtBarStart && currentBar != lastLaunchBar)
        {
            sendAllNotesOffNow(midiMessages, sampleOffset);

            activePattern = pendingPattern;
            pendingPattern = -2;

            displayActivePattern.store(activePattern);
            displayPendingPattern.store(pendingPattern);

            patternStartStep = step;
            lastPlayedStep = -1;
            lastLaunchBar = currentBar;

            if (activePattern < 0)
                displayCurrentStep.store(0);
        }

        //======================================================================
        // 4c. If stopped, do not generate new notes.

        if (activePattern < 0)
            continue;

        //======================================================================
        // 4d. Generate note-on at this exact grid point.

        if (step == lastPlayedStep)
            continue;

        const int stepsSincePatternStart = step - patternStartStep;
        const int playbackStepIndex = ((stepsSincePatternStart % patternLength) + patternLength) % patternLength;

        // v1.4.0:
        // Rotation is applied only to the source step lookup.
        // The playback clock and displayed current step remain unchanged.
        const int sourceStepIndex = getRotatedSourceStepIndex(activePattern, playbackStepIndex);

        const Step currentStepData = getStepForPattern(activePattern, sourceStepIndex);

        if (currentStepData.note >= 0
            && currentStepData.velocity > 0
            && currentStepData.durationSteps > 0)
        {
            const auto stepVelocity = static_cast<juce::uint8> (
                juce::jlimit(1, 127, currentStepData.velocity)
                );

            const int outputNote = applyPatternTransformsToNote(activePattern, currentStepData.note);

            midiMessages.addEvent(juce::MidiMessage::noteOn(midiChannel,
                outputNote,
                stepVelocity),
                sampleOffset);

            PendingNoteOff noteOff;
            noteOff.note = outputNote;
            noteOff.channel = midiChannel;
            noteOff.targetStep = step + currentStepData.durationSteps;

            pendingNoteOffs.push_back(noteOff);
        }

        lastPlayedStep = step;
    }
}

//==============================================================================
bool NewProjectAudioProcessor::hasEditor() const
{
    return true;
}

juce::AudioProcessorEditor* NewProjectAudioProcessor::createEditor()
{
    return new NewProjectAudioProcessorEditor(*this);
}

//==============================================================================
void NewProjectAudioProcessor::getStateInformation(juce::MemoryBlock& destData)
{
    juce::XmlElement root("MidiPatternLauncher");

    root.setAttribute("version", "1.6.0");

    for (int patternIndex = 0; patternIndex < numPatterns; ++patternIndex)
    {
        auto* patternXml = root.createNewChildElement("Pattern");

        patternXml->setAttribute("index", patternIndex);
        patternXml->setAttribute("transpose", patternTranspose[static_cast<size_t>(patternIndex)]);
        patternXml->setAttribute("rotation", patternRotation[static_cast<size_t>(patternIndex)]);
        patternXml->setAttribute("inverted", patternInverted[static_cast<size_t>(patternIndex)] ? 1 : 0);

        for (int stepIndex = 0; stepIndex < patternLength; ++stepIndex)
        {
            const auto& step = patterns[static_cast<size_t>(patternIndex)]
                [static_cast<size_t>(stepIndex)];

            auto* stepXml = patternXml->createNewChildElement("Step");

            stepXml->setAttribute("index", stepIndex);
            stepXml->setAttribute("note", step.note);
            stepXml->setAttribute("velocity", step.velocity);
            stepXml->setAttribute("durationSteps", step.durationSteps);
        }
    }

    auto apvtsState = apvts.copyState();
    std::unique_ptr<juce::XmlElement> apvtsXml(apvtsState.createXml());

    if (apvtsXml != nullptr)
    {
        apvtsXml->setTagName("APVTS");
        root.addChildElement(apvtsXml.release());
    }

    copyXmlToBinary(root, destData);
}

void NewProjectAudioProcessor::setStateInformation(const void* data, int sizeInBytes)
{
    auto xmlState = getXmlFromBinary(data, sizeInBytes);

    if (xmlState == nullptr)
        return;

    if (!xmlState->hasTagName("MidiPatternLauncher"))
        return;

    juce::MidiBuffer emptyMidiBuffer;
    sendAllNotesOffNow(emptyMidiBuffer, 0);

    activePattern = -1;
    pendingPattern = -2;

    for (auto* patternXml : xmlState->getChildWithTagNameIterator("Pattern"))
    {
        const int patternIndex = patternXml->getIntAttribute("index", -1);

        if (patternIndex < 0 || patternIndex >= numPatterns)
            continue;

        patternTranspose[static_cast<size_t>(patternIndex)] =
            juce::jlimit(-48, 48, patternXml->getIntAttribute("transpose", 0));

        patternRotation[static_cast<size_t>(patternIndex)] =
            juce::jlimit(0, patternLength - 1, patternXml->getIntAttribute("rotation", 0));

        patternInverted[static_cast<size_t>(patternIndex)] =
            patternXml->getIntAttribute("inverted", 0) != 0;

        for (auto* stepXml : patternXml->getChildWithTagNameIterator("Step"))
        {
            const int stepIndex = stepXml->getIntAttribute("index", -1);

            if (stepIndex < 0 || stepIndex >= patternLength)
                continue;

            auto& step = patterns[static_cast<size_t>(patternIndex)]
                [static_cast<size_t>(stepIndex)];

            const int restoredNote = stepXml->getIntAttribute("note", -1);
            const int restoredVelocity = stepXml->getIntAttribute("velocity", 0);
            const int restoredDurationSteps = stepXml->getIntAttribute("durationSteps", 0);

            if (restoredNote < 0)
            {
                step.note = -1;
                step.velocity = 0;
                step.durationSteps = 0;
            }
            else
            {
                step.note = juce::jlimit(0, 127, restoredNote);
                step.velocity = juce::jlimit(1, 127, restoredVelocity);
                step.durationSteps = juce::jlimit(1, patternLength, restoredDurationSteps);
            }
        }
    }

    if (auto* apvtsXml = xmlState->getChildByName("APVTS"))
    {
        juce::ValueTree apvtsTree = juce::ValueTree::fromXml(*apvtsXml);

        if (apvtsTree.isValid())
            apvts.replaceState(apvtsTree);
    }

    lastActivePatternParam = 0;
    lastTargetPatternParam = 0;
    lastTransposeParam = 0;
    lastRotationParam = 0;
    lastInversionParam = false;

    syncEngineFromParameters();

    activePattern = -1;
    pendingPattern = -2;

    lastPlayedStep = -1;
    lastLaunchBar = -1;
    pendingNoteOffs.clear();

    displayActivePattern.store(activePattern);
    displayPendingPattern.store(pendingPattern);
    displayCurrentStep.store(0);
}

//==============================================================================
// This creates new instances of the plugin.

juce::AudioProcessor* JUCE_CALLTYPE createPluginFilter()
{
    return new NewProjectAudioProcessor();
}

