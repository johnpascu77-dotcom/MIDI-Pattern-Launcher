from pathlib import Path

cpp_path = Path("Source/PluginEditor.cpp")

if not cpp_path.exists():
    raise SystemExit("ERROR: Source/PluginEditor.cpp not found")

cpp = cpp_path.read_text(encoding="utf-8")


# -----------------------------------------------------------------------------
# 1. Patch Matrix stepText cell text to include velocity.
# -----------------------------------------------------------------------------

old_block = '''                if (hasNote)
                {
                    const int note = audioProcessor.getStepNote(patternIndex, stepIndex);
                    const int duration = audioProcessor.getStepDurationSteps(patternIndex, stepIndex);

                    stepText << "\\n" << note;
                    stepText << "\\n" << "d" << duration;
                }
'''

new_block = '''                if (hasNote)
                {
                    const int note = audioProcessor.getStepNote(patternIndex, stepIndex);
                    const int velocity = juce::jlimit(1, 127, audioProcessor.getStepVelocity(patternIndex, stepIndex));
                    const int duration = audioProcessor.getStepDurationSteps(patternIndex, stepIndex);

                    stepText << "\\n" << note;
                    stepText << "\\n" << "v" << velocity << " d" << duration;
                }
'''

if old_block not in cpp:
    if 'stepText << "\\\\n" << "v" << velocity << " d" << duration;' in cpp or 'stepText << "\\n" << "v" << velocity << " d" << duration;' in cpp:
        print("Matrix stepText velocity display already appears present; continuing.")
    else:
        raise SystemExit("ERROR: Could not find Matrix stepText note/duration block")
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
