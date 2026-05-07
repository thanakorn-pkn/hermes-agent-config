---
name: obsidian-project-bootstrap
description: Bootstrap a new active project in an Obsidian PARA vault by creating a Homepage and Implementation Plan, checking for existing project folders first, and committing the scaffold.
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [obsidian, para, projects, bootstrap, pkm]
    category: knowledge
---

# Obsidian Project Bootstrap

Use this skill when the user asks to create a new project in the Obsidian vault, especially when the project is meant to be active, long-lived, and re-enterable later.

## Core workflow

1. **Orient the vault**
   - Read `INDEX.md` and `AGENTS.md` if the vault context is not already loaded.
   - Confirm the vault root, usually `$OBSIDIAN_VAULT_PATH` or `/data/syncthing/obsidian-second-brain`.

2. **Check for an existing project folder first**
   - Search `10_projects/` for matching names before creating anything new.
   - Reuse an existing folder if a match exists; do not duplicate project roots.

3. **Create the project scaffold**
   - Add `Homepage.md` as the entry point.
   - Add `Implementation Plan.md` as the operating plan.
   - Use Obsidian-friendly markdown and add frontmatter.

4. **Recommended Homepage sections**
   - Vision / purpose
   - Boundaries / non-goals
   - Initial stack or assumptions
   - First outcomes / milestones
   - Related links
   - Next step

5. **Recommended Implementation Plan sections**
   - Phases or workstreams
   - Success criteria
   - Operational constraints / recovery rules when relevant
   - Related links back to the homepage and adjacent projects

6. **If the project is an AI identity / digital twin / assistant operator**
   - Separate project-owned identity from the user's personal identity
   - Keep project-owned email/accounts distinct from personal accounts
   - Make approval boundaries explicit for anything public, irreversible, or compliance-sensitive

7. **Commit the scaffold**
   - Use a meaningful commit message like `project(<name>): add initial project scaffold`.

## Good defaults

- Keep the homepage short and easy to resume from.
- Make the implementation plan actionable but not over-detailed.
- Link the new project to nearby related projects when appropriate.
- Prefer a safe, restartable setup over a perfect one.
