---
name: obsidian-pkb-integration
description: Integrate a personal knowledge base (PKB) in an Obsidian vault with Hermes so the agent can reliably search, operate on, and persist notes using vault-specific rules.
---

# Obsidian PKB Integration

Use this when a user has an Obsidian-based PKB and wants Hermes to treat it as an operational knowledge/project store, not just a folder of markdown files.

## Goal

Make Hermes PKB-aware by default for the user's vault at `/srv/syncthing/obsidian-second-brain` while keeping the vault itself as the source of truth for governance, roles, and workflows.

## Installed vault target

This bridge skill is wired to the Obsidian vault at `/srv/syncthing/obsidian-second-brain`.

- `OBSIDIAN_VAULT_PATH` should point to `/srv/syncthing/obsidian-second-brain`
- Treat that path as the default PKB unless the user explicitly overrides it
- Use Obsidian-compatible Markdown and wikilinks (`[[Note Name]]`) when reading or writing vault content

## Default operating behavior

Before major PKB work, Hermes should:

1. Read `/srv/syncthing/obsidian-second-brain/AGENTS.md`
2. Read `/srv/syncthing/obsidian-second-brain/README.md`
3. Read `/srv/syncthing/obsidian-second-brain/INDEX.md`

If `INDEX.md` is empty, missing useful navigation, or otherwise insufficient for the task, fall back to direct search/scan in `/srv/syncthing/obsidian-second-brain/30_resources/`.

- Exclude `/srv/syncthing/obsidian-second-brain/30_resources/_sources/` from that fallback search unless the task is source lookup, ingest, or provenance validation
- Prefer updating existing notes over creating duplicates
- Route persistence by default to `10_projects/` for project/task notes, `30_resources/` for reusable knowledge/reference/synthesis, and `00_inbox/` for rough capture
- Use the vault workflow skill files as the source of truth for detailed procedures instead of restating them here

Relevant vault workflow skills:

- `/srv/syncthing/obsidian-second-brain/30_resources/AI Agent/Skills/knowledge-management/write/SKILL.md`
- `/srv/syncthing/obsidian-second-brain/30_resources/AI Agent/Skills/knowledge-management/query/SKILL.md`
- `/srv/syncthing/obsidian-second-brain/30_resources/AI Agent/Skills/knowledge-management/ingest/SKILL.md`
- `/srv/syncthing/obsidian-second-brain/30_resources/AI Agent/Skills/knowledge-management/lint/SKILL.md`
- `/srv/syncthing/obsidian-second-brain/30_resources/AI Agent/Skills/knowledge-management/release/SKILL.md`

## Recommended architecture

Separate concerns into four layers:

1. `AGENTS.md` in the vault
   - Source of truth for governance, autonomy, persistence rules, write locations, and git behavior.
2. Vault role files (for example `30_resources/AI Agent/Roles/personal-assistant.md`)
   - Define identity, responsibilities, tone, and boundaries.
3. Vault workflow skills (for example `write`, `query`, `ingest`, `lint`, `release`)
   - Define how to operate inside the vault.
4. Hermes-side bridge skill/profile
   - Makes Hermes load the vault context by default and consult the vault rules before acting.

## Key principle

Do not rely on the role file or vault skills alone to make Hermes understand the PKB.

Vault files are passive unless Hermes is explicitly pointed at them through a bridge skill, profile, or system prompt. Without that bridge, Hermes can still read/write the vault when asked, but it will not reliably follow the PKB workflow by default.

## Integration steps

1. Use the vault root path `/srv/syncthing/obsidian-second-brain`.
   - `OBSIDIAN_VAULT_PATH` should point to this exact location.
2. Verify the vault has these core files:
   - `README.md`
   - `AGENTS.md`
   - `INDEX.md` (or decide what to do if it is empty/not maintained)
3. Inspect the actual location of vault workflow skills.
   - Do not trust documentation blindly; confirm the real path in the vault.
4. Patch the installed Hermes bridge skill so it explicitly points at this vault and loads the vault context by default.
5. In that bridge skill, instruct Hermes to:
   - treat the vault as an Obsidian vault
   - read `AGENTS.md`, `README.md`, and `INDEX.md` before major PKB work
   - fall back to direct search in `30_resources/` when `INDEX.md` is empty or insufficient
   - exclude `30_resources/_sources/` from fallback search unless doing source/ingest work
   - consult the vault workflow skill files for operations like write/query/ingest/lint/release
   - prefer updating existing notes over creating duplicates
   - persist project notes to `10_projects/`, reusable knowledge to `30_resources/`, and rough capture to `00_inbox/`
6. Preload that bridge skill in the user’s default Hermes profile if they want PKB-aware behavior by default.
7. Keep the personal-assistant role optional as a behavior overlay.
   - Use it when the user wants assistant-style prioritization and persistence behavior.
   - Do not make the role a hard dependency for basic PKB operations.

## What goes where

- Generic Obsidian conventions -> keep in a general Obsidian skill
- Vault-specific operating rules -> keep in the vault’s own docs/skills
- Hermes default PKB awareness -> put in the Hermes bridge skill/profile
- Assistant behavior -> keep in the role file

## Pitfalls discovered

### 1. Docs may disagree with reality

A vault may document one skill location while the actual files live elsewhere. Always inspect the vault filesystem and use the real paths.

### 2. Role != complete integration

A role file can say the right things, but that does not make Hermes automatically load or follow the vault workflow.

### 3. Skill set != universal awareness

Even if the vault has a complete knowledge-management skill set, another agent may not infer from that alone that the vault is Obsidian. State this explicitly in the role and/or bridge skill.

### 4. Empty `INDEX.md`

If query/lint workflows depend on `INDEX.md` but it is empty, either populate it or make the workflow fall back to direct search in `30_resources/`.

### 5. Avoid overloading the generic Obsidian skill

Do not cram all vault-specific policy into a generic Obsidian skill. Keep generic format rules separate from vault-specific workflow.

## Recommended wording for role files

Add a short explicit line such as:

`This is an Obsidian vault. Use Obsidian-compatible Markdown and wikilinks, and preserve existing vault conventions.`

This prevents ambiguity when a role is read in isolation.

## Good final setup

- Vault remains source of truth
- Hermes bridge skill makes PKB behavior available by default
- Personal-assistant role adds behavior, not operational coupling
- Query/search/persistence all route through the PKB structure consistently

## When to update existing skills instead

If a Hermes skill already exists for working with this exact PKB, patch that skill instead of creating a new one. Add:
- explicit Obsidian-vault language
- bridge-to-vault instructions
- guidance for empty or partial `INDEX.md`
- a warning to verify actual skill/document paths before trusting README text
