# GLYPH8 Automation

This file explains how to automate the GLYPH system so it can run on its own.

## What is automated

The automation script performs these steps:

1. Extracts text from selected files in `~/Downloads`.
2. Saves extracted text as `.txt` files in `docs/downloads_corpus/`.
3. Creates event records from the extracted texts.
4. Builds context references from the extracted corpus and stores them in the event engine.
5. Processes each event using the GLYPH event engine.
6. Saves a JSON results file with the generated responses and a `context_references.json` file.
7. Logs the run activity to `docs/automation.log`.

## Run once

From the `GLYPH8` folder:

```bash
python3 automation.py ~/Downloads --output docs/downloads_corpus --results docs/automation_results --log docs/automation.log
```

## Run repeatedly

Use the `--interval` option to repeat the cycle every N seconds.

```bash
python3 automation.py ~/Downloads --output docs/downloads_corpus --results docs/automation_results --log docs/automation.log --interval 3600
```

This runs the extractor and event processing every hour.

## Scheduling on macOS

### Use `launchd`

Create a file at `~/Library/LaunchAgents/com.glyph8.automation.plist` with a command that runs the script periodically.

Example plist:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key>
  <string>com.glyph8.automation</string>
  <key>ProgramArguments</key>
  <array>
    <string>/usr/bin/python3</string>
    <string>/Users/jayjonah/8glyphs27/GLYPH8/automation.py</string>
    <string>/Users/jayjonah/Downloads</string>
    <string>--output</string>
    <string>/Users/jayjonah/8glyphs27/GLYPH8/docs/downloads_corpus</string>
    <string>--results</string>
    <string>/Users/jayjonah/8glyphs27/GLYPH8/docs/automation_results</string>
    <string>--log</string>
    <string>/Users/jayjonah/8glyphs27/GLYPH8/docs/automation.log</string>
  </array>
  <key>StartInterval</key>
  <integer>3600</integer>
  <key>RunAtLoad</key>
  <true/>
</dict>
</plist>
```

Then load it with:

```bash
launchctl load ~/Library/LaunchAgents/com.glyph8.automation.plist
```

## Keeping automation focused

- Use the event-driven model: every cycle processes extracted files as discrete events.
- Keep the system from producing unsolicited guidance by limiting the output to candidate responses only.
- Store previous results so each new run can compare incoming data against prior data.
- Use the source metadata saved in each event to keep analysis structural rather than personal.

## Next steps

- Add more file rules to `automation.py` if you want more sources.
- Add a validation layer that checks each result against a strict scope filter.
- Convert the generated event responses into a dashboard or API if you want a live SaaS experience.
