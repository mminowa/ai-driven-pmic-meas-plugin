---
description: Phase 3 step 3 of 4 — generate the .measui with the NI Measurement Plug-In UI Creator (Windows). Generation/copy only; no layout editing.
argument-hint: <short_name>  e.g. buck_ripple
---

You are running the **gen-measui** step of Phase 3 (Implementation) of the
Specification-Driven Development process in @CLAUDE.md. Short name: **$1**.

Phase 3 is split into four commands run in order:
`/scaffold` → `/implement` → `/gen-measui` → `/refine-measui`. This command covers
@docs/update-measui.md **Steps 1–7**: install the UI Creator, run the measurement service, run
the UI Creator to generate the `.measui`, and copy it into the plug-in directory. Stop there —
adding/removing and laying out controls (update-measui.md Steps 8–9) is `/refine-measui`.

## Hard rule

`measurement.py` must be final before generating the UI, because the UI Creator queries the
running service for its parameters/outputs. If `/implement $1` has not been completed, tell the
user to finish it first and stop.

**This procedure requires Windows** (PowerShell + the running gRPC service). It is largely
interactive and environment-dependent: the UI Creator prompts you to pick the measurement
service, and the service runs in a separate terminal. Drive the file/setup steps you can, and
clearly hand the interactive steps to the user — do not pretend to have run a Windows-only or
interactive step that you could not execute here.

## Reference

- Full procedure: @docs/update-measui.md, **Steps 1–7**.
- Plug-in directory, service name, and generated filename: the **Project-Specific
  Configuration** table in @docs/update-measui.md.

## Steps

Follow @docs/update-measui.md, **Steps 1–7**:

1. Create a dedicated `venv` at the project root for the UI Creator.
2. Download the UI Creator wheel and `install.bat` to the project root.
3. Modify `install.bat` to use that `venv` and rename it to `install_ui_creator.bat`
   (add it to `.gitignore`).
4. Run `install_ui_creator.bat` to install the UI Creator.
5. In a separate terminal, start the measurement service (`start.bat`) and leave it running.
6. Run `ni-measurement-plugin-ui-creator create` and select the measurement service when
   prompted to generate `<ServiceName>.measui`.
7. Move the generated `.measui` into `src/$1/`, overwriting the existing one.

Do not edit the control layout or XML here — leave that for `/refine-measui`.

## Finish

Confirm the `.measui` was generated and copied into `src/$1/`, and remind the user not to
commit `venv/`, `install.bat`, or the `.whl`. Tell the user the next step is
`/refine-measui $1` to add unsupported controls and match the UI specification.

Keep all files, comments, and commit messages in **English**.
