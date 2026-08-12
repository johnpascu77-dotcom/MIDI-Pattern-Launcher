from pathlib import Path

cpp_path = Path("Source/PluginEditor.cpp")

if not cpp_path.exists():
    raise SystemExit("ERROR: Source/PluginEditor.cpp not found")

cpp = cpp_path.read_text(encoding="utf-8")


# -----------------------------------------------------------------------------
# 1. Find and patch active Matrix cell text from duration-only to velocity+duration
# -----------------------------------------------------------------------------

old_block = '''                g.drawText(
                    "d" + juce::String(duration),
                    textBox.removeFromTop(16),
                    juce::Justification::centred);
'''

new_block = '''                const int velocity = juce::jlimit(1, 127, audioProcessor.getStepVelocity(patternIndex, stepIndex));

                g.drawText(
                    "v" + juce::String(velocity) + " d" + juce::String(duration),
                    textBox.removeFromTop(16),
                    juce::Justification::centred);
'''

if old_block not in cpp:
    if '"v" + juce::String(velocity) + " d" + juce::String(duration)' in cpp:
        print("Matrix cell velocity text already appears present; continuing.")
    else:
        raise SystemExit("ERROR: Could not find Matrix duration text block")
else:
    cpp = cpp.replace(old_block, new_block, 1)


# -----------------------------------------------------------------------------
# 2. Update version text
# -----------------------------------------------------------------------------

if '"v1.17.3 - Matrix Velocity Paint"' in cpp:
    cpp = cpp.replace('"v1.17.3 - Matrix Velocity Paint"', '"v1.17.4 - Matrix Velocity Display"', 1)
elif '"v1.17.4 - Matrix Velocity Display"' in cpp:
    print("Version text already appears updated to v1.17.4; continuing.")
else:
    print("WARNING: Could not find v1.17.3 version text; version label not updated.")


cpp_path.write_text(cpp, encoding="utf-8")

print("v1.17.4 applied: Matrix cells now display velocity and duration.")
