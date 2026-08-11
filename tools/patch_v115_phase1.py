from pathlib import Path
import re

paths = {
    "processor_cpp": Path("Source/PluginProcessor.cpp"),
    "processor_h": Path("Source/PluginProcessor.h"),
    "editor_cpp": Path("Source/PluginEditor.cpp"),
    "editor_h": Path("Source/PluginEditor.h"),
}

for name, path in paths.items():
    if not path.exists():
        raise SystemExit(f"ERROR: Missing file: {path}")

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

def insert_before_once(text, marker, insertion, label):
    count = text.count(marker)
    require(count == 1, f"Expected exactly one marker for {label}, found {count}")
    if insertion.strip() in text:
        print(f"SKIP: {label} already present")
        return text
    return text.replace(marker, insertion + marker, 1)

# =============================================================================
# Source/PluginProcessor.cpp

path = paths["processor_cpp"]
text = read(path)

require('"gridModeParam"' in text, 'gridModeParam not found in PluginProcessor.cpp')
require('"targetStepParam"' in text, 'targetStepParam not found in PluginProcessor.cpp')

if '"editorViewModeParam"' not in text:
    marker = '''    parameters.push_back(std::make_unique<juce::AudioParameterInt>(
        juce::ParameterID("targetStepParam", 1),'''
    insertion = '''    parameters.push_back(std::make_unique<juce::AudioParameterChoice>(
        juce::ParameterID("editorViewModeParam", 1),
        "Editor View Mode",
        juce::StringArray{ "Matrix", "Melody" },
        0));

'''
    text = insert_before_once(text, marker, insertion, "add editorViewModeParam before targetStepParam")
else:
    print("SKIP: editorViewModeParam already present")

if "MidiPatternLauncherAudioProcessor::getEditorViewModeIndex() const" not in text:
    marker = '''void MidiPatternLauncherAudioProcessor::updateAutomationParametersForPattern(int patternIndex)'''
    insertion = '''int MidiPatternLauncherAudioProcessor::getEditorViewModeIndex() const
{
    return juce::jlimit(0, 1, getChoiceParameterIndex("editorViewModeParam"));
}

bool MidiPatternLauncherAudioProcessor::isMelodyPaintMode() const
{
    return getEditorViewModeIndex() == 1;
}

'''
    text = insert_before_once(text, marker, insertion, "add editor view accessor implementations")
else:
    print("SKIP: editor view accessor implementations already present")

write(path, text)

# =============================================================================
# Source/PluginProcessor.h

path = paths["processor_h"]
text = read(path)

if "int getEditorViewModeIndex() const;" not in text:
    old = '''    int getGridModeIndex() const;
    int getGridStepCount() const;
    bool isTernaryGridMode() const;

    int getDisplayActivePattern() const;'''
    new = '''    int getGridModeIndex() const;
    int getGridStepCount() const;
    bool isTernaryGridMode() const;

    int getEditorViewModeIndex() const;
    bool isMelodyPaintMode() const;

    int getDisplayActivePattern() const;'''
    text = replace_once(text, old, new, "PluginProcessor.h editor view declarations")
else:
    print("SKIP: editor view declarations already present")

write(path, text)

# =============================================================================
# Source/PluginEditor.h

path = paths["editor_h"]
text = read(path)

if "juce::Label editorViewModeLabel;" not in text:
    text = replace_once(
        text,
        '''    juce::Label targetPatternLabel;
    juce::Label gridModeLabel;
    juce::Label targetStepLabel;''',
        '''    juce::Label targetPatternLabel;
    juce::Label gridModeLabel;
    juce::Label editorViewModeLabel;
    juce::Label targetStepLabel;''',
        "PluginEditor.h editorViewModeLabel"
    )
else:
    print("SKIP: editorViewModeLabel already present")

if "juce::ComboBox editorViewModeBox;" not in text:
    text = replace_once(
        text,
        '''    juce::ComboBox targetPatternBox;
    juce::ComboBox gridModeBox;
    juce::Slider targetStepSlider;''',
        '''    juce::ComboBox targetPatternBox;
    juce::ComboBox gridModeBox;
    juce::ComboBox editorViewModeBox;
    juce::Slider targetStepSlider;''',
        "PluginEditor.h editorViewModeBox"
    )
else:
    print("SKIP: editorViewModeBox already present")

if "editorViewModeAttachment" not in text:
    text = replace_once(
        text,
        '''    std::unique_ptr<ComboBoxAttachment> targetPatternAttachment;
    std::unique_ptr<ComboBoxAttachment> gridModeAttachment;
    std::unique_ptr<SliderAttachment> targetStepAttachment;''',
        '''    std::unique_ptr<ComboBoxAttachment> targetPatternAttachment;
    std::unique_ptr<ComboBoxAttachment> gridModeAttachment;
    std::unique_ptr<ComboBoxAttachment> editorViewModeAttachment;
    std::unique_ptr<SliderAttachment> targetStepAttachment;''',
        "PluginEditor.h editorViewModeAttachment"
    )
else:
    print("SKIP: editorViewModeAttachment already present")

write(path, text)

# =============================================================================
# Source/PluginEditor.cpp

path = paths["editor_cpp"]
text = read(path)

if 'setupLabel(editorViewModeLabel, "View");' not in text:
    text = replace_once(
        text,
        '''    setupLabel(targetPatternLabel, "Pattern");
    setupLabel(gridModeLabel, "Grid");
    setupLabel(targetStepLabel, "Step");''',
        '''    setupLabel(targetPatternLabel, "Pattern");
    setupLabel(gridModeLabel, "Grid");
    setupLabel(editorViewModeLabel, "View");
    setupLabel(targetStepLabel, "Step");''',
        "PluginEditor.cpp setup editorViewModeLabel"
    )
else:
    print("SKIP: setup editorViewModeLabel already present")

if "addAndMakeVisible(editorViewModeLabel);" not in text:
    text = replace_once(
        text,
        '''    addAndMakeVisible(targetPatternLabel);
    addAndMakeVisible(gridModeLabel);
    addAndMakeVisible(targetStepLabel);''',
        '''    addAndMakeVisible(targetPatternLabel);
    addAndMakeVisible(gridModeLabel);
    addAndMakeVisible(editorViewModeLabel);
    addAndMakeVisible(targetStepLabel);''',
        "PluginEditor.cpp add editorViewModeLabel visible"
    )
else:
    print("SKIP: editorViewModeLabel visibility already present")

if 'editorViewModeBox.addItem("Matrix", 1);' not in text:
    text = replace_once(
        text,
        '''    gridModeBox.addItem("Binary 16", 1);
    gridModeBox.addItem("Ternary 12", 2);''',
        '''    gridModeBox.addItem("Binary 16", 1);
    gridModeBox.addItem("Ternary 12", 2);

    editorViewModeBox.addItem("Matrix", 1);
    editorViewModeBox.addItem("Melody", 2);''',
        "PluginEditor.cpp editorViewModeBox items"
    )
else:
    print("SKIP: editorViewModeBox items already present")

if "addAndMakeVisible(editorViewModeBox);" not in text:
    text = replace_once(
        text,
        '''    addAndMakeVisible(targetPatternBox);
    addAndMakeVisible(gridModeBox);
    addAndMakeVisible(targetStepSlider);''',
        '''    addAndMakeVisible(targetPatternBox);
    addAndMakeVisible(gridModeBox);
    addAndMakeVisible(editorViewModeBox);
    addAndMakeVisible(targetStepSlider);''',
        "PluginEditor.cpp add editorViewModeBox visible"
    )
else:
    print("SKIP: editorViewModeBox visibility already present")

if 'apvts, "editorViewModeParam", editorViewModeBox' not in text:
    text = replace_once(
        text,
        '''    gridModeAttachment = std::make_unique<ComboBoxAttachment>(
        apvts, "gridModeParam", gridModeBox);''',
        '''    gridModeAttachment = std::make_unique<ComboBoxAttachment>(
        apvts, "gridModeParam", gridModeBox);

    editorViewModeAttachment = std::make_unique<ComboBoxAttachment>(
        apvts, "editorViewModeParam", editorViewModeBox);''',
        "PluginEditor.cpp editorViewMode attachment"
    )
else:
    print("SKIP: editorViewMode attachment already present")

if 'v1.15.0 - Melody Paint Mode' not in text:
    text = text.replace('v1.14.0 - True Metric Grid', 'v1.15.0 - Melody Paint Mode')
else:
    print("SKIP: version label already updated")

if "editorViewModeLabel.setBounds(targetRow1.removeFromLeft(targetLabelWidth));" not in text:
    old = '''    const int targetGap = 8;
    const int targetLabelWidth = 62;
    const int targetControlWidth = 160;

    targetPatternLabel.setBounds(targetRow1.removeFromLeft(targetLabelWidth));
    targetPatternBox.setBounds(targetRow1.removeFromLeft(targetControlWidth));
    targetRow1.removeFromLeft(targetGap);

    gridModeLabel.setBounds(targetRow1.removeFromLeft(targetLabelWidth));
    gridModeBox.setBounds(targetRow1.removeFromLeft(targetControlWidth));
    targetRow1.removeFromLeft(targetGap);

    targetStepLabel.setBounds(targetRow1.removeFromLeft(targetLabelWidth));
    targetStepSlider.setBounds(targetRow1.removeFromLeft(targetControlWidth));
    targetRow1.removeFromLeft(targetGap);

    targetEnabledLabel.setBounds(targetRow1.removeFromLeft(targetLabelWidth));
    targetEnabledButton.setBounds(targetRow1.removeFromLeft(targetControlWidth));'''
    new = '''    const int targetGap = 8;
    const int targetLabelWidth = 52;
    const int targetControlWidth = 150;

    targetPatternLabel.setBounds(targetRow1.removeFromLeft(targetLabelWidth));
    targetPatternBox.setBounds(targetRow1.removeFromLeft(targetControlWidth));
    targetRow1.removeFromLeft(targetGap);

    gridModeLabel.setBounds(targetRow1.removeFromLeft(targetLabelWidth));
    gridModeBox.setBounds(targetRow1.removeFromLeft(targetControlWidth));
    targetRow1.removeFromLeft(targetGap);

    editorViewModeLabel.setBounds(targetRow1.removeFromLeft(targetLabelWidth));
    editorViewModeBox.setBounds(targetRow1.removeFromLeft(targetControlWidth));
    targetRow1.removeFromLeft(targetGap);

    targetStepLabel.setBounds(targetRow1.removeFromLeft(targetLabelWidth));
    targetStepSlider.setBounds(targetRow1.removeFromLeft(targetControlWidth));'''
    text = replace_once(text, old, new, "PluginEditor.cpp row 1 layout")
else:
    print("SKIP: row 1 layout already updated")

write(path, text)

print("v1.15.0 Phase 1 robust patch applied successfully.")
