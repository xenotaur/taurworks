# Getting started with Taurworks

In this tutorial you will install Taurworks, create a project, and switch into
it with `tw activate`. At the end, one command from any directory will put
your shell in the project's working directory, ready to work.

You need:

- **bash** (zsh is expected to work for `tw`; `tl` is written for bash).
- **Python 3.11 or newer.**
- **[pipx](https://pipx.pypa.io/)**, with its app directory (`~/.local/bin`
  by default) on your `PATH`.
- A checkout of the Taurworks repository. Taurworks is not published to PyPI.

Conda is optional. You only need it if you want Taurworks to activate a Conda
environment for you, which this tutorial covers in its last step.

## 1. Install

From the root of your Taurworks checkout:

```bash
scripts/install
```

This installs the `taurworks` command with pipx, then runs `taurworks setup`,
which writes two shell files and prints two `source` lines:

```text
Add these lines to your shell startup file (e.g. ~/.bashrc) to enable tw and tl:

source /home/you/.config/taurworks/taurworks-shell.sh
source /home/you/.config/taurworks/tl.source
```

## 2. Turn on `tw` and `tl`

Taurworks never edits your shell startup files. Copy the two printed `source`
lines into `~/.bashrc` (or `~/.zshrc`) yourself, then open a new shell or run
the two lines once in your current one.

Check that it worked:

```bash
tw help
```

You should see the `taurworks` usage text. You now have three commands:

- `taurworks` — the program itself.
- `tw` — a shell function that wraps `taurworks` and can also change your
  current shell. This is the one you will use day to day.
- `tl` — an emergency fallback you can ignore for now.

## 3. Tell Taurworks where your projects live

Pick a directory to hold your projects — the *workspace root* — and record it:

```bash
mkdir -p ~/Workspace
```

```bash
tw workspace set ~/Workspace
```

## 4. Create a project

```bash
tw project create Demo --working-dir repo --create-working-dir
```

It does not matter which directory you run this from. Taurworks creates the
project under the workspace root:

```text
~/Workspace/Demo/
  .taurworks/
    config.toml      <- project settings
  repo/              <- the working directory, where your code goes
```

`~/Workspace/Demo` is the *project root*. `repo` is the *working directory*:
the place you actually want to be when you work on the project.

## 5. Activate it

From anywhere:

```bash
tw activate Demo
```

```text
tw activate: note: Activation guidance is ready, but no Conda activation environment is configured. ...
tw activate: changed directory to /home/you/Workspace/Demo/repo
```

Your shell is now in the project's working directory. The `note:` line is a
reminder that this project has no Conda environment attached; it is not an
error, and step 7 shows how to attach one. List your projects to
see it:

```bash
tw projects
```

```text
Available projects:

- Demo    initialized    workspace
```

## 6. Make activation do more

Open `~/Workspace/Demo/.taurworks/config.toml` in an editor and add an
activation message and an exported variable, so the file looks like this:

```toml
schema_version = 1

[project]
name = "Demo"

[paths]
working_dir = "repo"

[activation]
message = "Ready for work on Demo"

[activation.exports]
DEMO_MODE = "development"
```

Activate again:

```bash
tw activate Demo
```

```text
tw activate: note: Activation guidance is ready, but no Conda activation environment is configured. ...
tw activate: exported 1 variable(s)
tw activate: changed directory to /home/you/Workspace/Demo/repo
Ready for work on Demo
```

```bash
echo $DEMO_MODE
```

```text
development
```

## 7. Optional: attach a Conda environment

If you use Conda and already have an environment for this project (Taurworks
does not create one for you here), record its name:

```bash
tw project env set my-env-name --project Demo
```

From now on `tw activate Demo` runs `conda activate my-env-name` before
exporting variables and changing directory, and the `note:` line goes away.

## What you have learned

- `scripts/install` then two `source` lines sets up `taurworks`, `tw`, and
  `tl`.
- A project is a directory with a `.taurworks/config.toml`, and usually a
  separate working directory inside it.
- `tw activate NAME` works from any directory.

## Next steps

- Bring in projects you already have:
  [Create, initialize, and register projects](../how-to/manage-projects.md).
- Everything `tw activate` can do:
  [Activate a project](../how-to/activate-projects.md).
- When `tw` stops working:
  [Use `tl`, the break-glass fallback](../how-to/use-tl-fallback.md).
- Why there are three commands: [Concepts](../explanation/concepts.md).
