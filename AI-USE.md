<!-- SPDX-License-Identifier: GPL-3.0-or-later -->
# How AI is used in this project

*[Português](AI-USE.pt-BR.md)*

This repository is built with an AI coding assistant (Claude Code, from Anthropic) working under a written method
(`docs/Method/AI-Workflow.md`). This page says what the assistant does and what only a person decides.

## What the assistant does

- Writes and edits code, tests, scripts and documentation, one requirement at a time. Every change cites the
  requirement of the specification (`docs/Functionality/FSD.md`) that it serves.
- Writes the test first and runs it: on the host, on the reference board (a Waveshare ESP32-S3-RLCD-4.2 on the
  developer's notebook, through the bench driver `python -m bench`), and in CI.
- Records what happened in the test plan (`testing/test-plan.yaml`) with the commit it ran on. A result that did
  not run stays `not done`; a failing requirement is recorded as failing, with its cause.
- Proposes values and behaviours the specification does not yet state. A proposal is marked as such and becomes a
  requirement only when the responsible person accepts it.
- Commits with a `Co-Authored-By` trailer that names the model, so the authorship of each commit is visible.

## What only a person decides

- **What the project must do**: accepting or rejecting a requirement, a value, or a change of the specification.
- **Releases**: the tag, the publication to the ESP Component Registry, and registering the CI runner on the
  notebook. The assistant never tags, never publishes and never pushes without being asked.
- **Anything public and outward-facing**: the pull request to the upstream, the message to other maintainers,
  the text of any announcement.
- **Anything that can hurt**: sound above the bench volume, with listeners present; changing the system with
  `sudo`; deleting or rewriting history that was already sent.
- **The listening study**: its protocol, its ethics approval (CEP / Plataforma Brasil), who listens, and every
  claim about intelligibility. No claim about listeners is made without the approved study.

## What the assistant does not decide, and does not claim

A test that passes on the board is evidence about the board, not about listeners. Automatic speech-recognition
scores, when they exist, are estimates and are labelled so. The project does not claim to be the first offline
pt-BR text to speech on the ESP32.
