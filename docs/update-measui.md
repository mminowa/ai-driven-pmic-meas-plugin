# Updating the .measui File with Measurement Plug-In UI Creator

This guide describes how to regenerate a `.measui` file using the
[NI Measurement Plug-In UI Creator](https://github.com/ni/measurement-plugin-converter-python).
Run this procedure whenever `measurement.py` configuration parameters or outputs change.

> **Note:** This guide assumes a **Windows** environment. All commands use PowerShell or
> Windows batch files and are not directly applicable to macOS or Linux.

---

## Plugin-Specific Values

Look up the following values in the plugin's spec files before starting. Replace
`<plugin_name>` with the plugin directory name (e.g. `pmic_efficiency`).

| Item | Where to find it |
|---|---|
| Plug-in directory | `docs/specs/<plugin_name>.md` → Plugin Configuration section |
| Measurement service name | `docs/specs/<plugin_name>.md` → Plugin Configuration section |
| Generated `.measui` filename | `<MeasurementServiceName>.measui` (service name + `.measui`) |
| UI specification | `docs/specs/<plugin_name>_ui.md` |

---

## Prerequisites

- Python 3.10+ installed and available on PATH
- The plug-in dependencies already installed (`.venv` exists inside the plug-in directory listed in **Plugin-Specific Values** above)

---

## Step 1 — Create a dedicated virtual environment

Create a `venv` folder at the project root to isolate the UI Creator from the plug-in venv.

```powershell
# Run from the project root
py -3.12 -m venv venv
```

---

## Step 2 — Download the UI Creator wheel and install script

Download both files from the
[1.0.0 release page](https://github.com/ni/measurement-plugin-converter-python/releases/tag/1.0.0)
and save them to the **project root**:

| File | Direct download URL |
|---|---|
| `ni_measurement_plugin_ui_creator-1.0.0-py3-none-any.whl` | `https://github.com/ni/measurement-plugin-converter-python/releases/download/1.0.0/ni_measurement_plugin_ui_creator-1.0.0-py3-none-any.whl` |
| `install.bat` | `https://raw.githubusercontent.com/ni/measurement-plugin-converter-python/main/batch_files/install.bat` |

```powershell
# PowerShell one-liners (run from project root)
Invoke-WebRequest -Uri "https://github.com/ni/measurement-plugin-converter-python/releases/download/1.0.0/ni_measurement_plugin_ui_creator-1.0.0-py3-none-any.whl" -OutFile "ni_measurement_plugin_ui_creator-1.0.0-py3-none-any.whl"
Invoke-WebRequest -Uri "https://raw.githubusercontent.com/ni/measurement-plugin-converter-python/main/batch_files/install.bat" -OutFile "install.bat"
```

---

## Step 3 — Modify install.bat and rename it

The downloaded `install.bat` calls `pip` from the global environment.
Replace the `pip install` line to use the `venv` created in Step 1.

Open `install.bat` and change:

```bat
pip install !whl_files!
```

to:

```bat
venv\Scripts\pip install !whl_files!
```

Then rename the file to `install_ui_creator.bat` and add the new name to `.gitignore`
so Git does not track it:

```powershell
Rename-Item install.bat install_ui_creator.bat
```

---

## Step 4 — Install the UI Creator

Run `install_ui_creator.bat` from the project root.

```bat
install_ui_creator.bat
```

Expected output:

```
pip install ni_measurement_plugin_ui_creator-1.0.0-py3-none-any.whl
...
Successfully installed ni-measurement-plugin-ui-creator-1.0.0
All installations are complete.
```

---

## Step 5 — Start the measurement service (separate terminal)

Open a **new terminal**, navigate to the plug-in directory listed in **Plugin-Specific Values** above, and start the gRPC service.

```bat
cd <plugin_directory>
start.bat
```

Leave this terminal open. The service must be running while the UI Creator runs.

---

## Step 6 — Generate the .measui file

In the **original terminal** (with `venv` active), run the UI Creator:

```powershell
venv\Scripts\ni-measurement-plugin-ui-creator create
```

The tool queries the running discovery service and lists available measurements.
Select the measurement service name listed in **Plugin-Specific Values** above when prompted.

```
? Select a measurement service: (Use arrow keys)
 > <MeasurementServiceName>
```

The tool generates `<MeasurementServiceName>.measui` in the current directory.

---

## Step 7 — Copy the generated file into the plug-in directory

Move the generated `.measui` file (see **Plugin-Specific Values** above for the filename)
into the plug-in directory, overwriting the existing one.

```powershell
Move-Item -Force <MeasurementServiceName>.measui <plugin_directory>\<MeasurementServiceName>.measui
```

---

## Step 8 — Add and remove controls in Measurement Plug-In UI Editor

The UI Creator 1.0.0 supports the following data types: `Integer`, `Float`, `String`,
`Boolean`, and 1D arrays of those types. `Enum` and `DoubleXYDataArray1D` controls
are not supported and must be added manually.

Also remove controls that do not need to appear in the UI — for example, input parameters
whose default value is always used (no need for the user to change them from the UI), or
outputs that do not need to be displayed.

---

## Step 9 — Adjust the layout to match the UI specification

Rearrange and resize controls to match the layout defined in the UI specification file
listed in **Plugin-Specific Values**.


---

## Step 10 — Stop the measurement service

In the terminal running `start.bat`, press **Enter** to stop the service.

---

## Notes

- The generated `.measui` binds all controls to the channel paths declared in `measurement.py`
  via `@measurement_service.configuration` and `@measurement_service.output`.
- Do **not** commit `venv/`, `install.bat`, or the `.whl` file to the repository.
  Add them to `.gitignore` if needed.
