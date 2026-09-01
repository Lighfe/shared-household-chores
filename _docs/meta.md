# How these docs grow

AGENTS.md and _docs/process.md are indexes for a fresh agent, not archives.
New detail goes into its own file, not into these two.

Where new detail goes

- A repo-wide constraint (applies to every agent, every task) -> AGENTS.md Rules, one line
- A new command a fresh agent needs -> AGENTS.md Commands, one line
- A lifecycle/role-specific rule (grooming, QA, closing) -> process.md Rules, one line
- A judgment call made while grooming or implementing, beyond what the issue says -> _docs/decisions.md
- Anything that needs more than a one-line entry in any of the above -> its own file under _docs/, linked from the section it replaces

When it happens

- PM, while grooming (lifecycle step 2): record judgment calls in decisions.md as part of grooming, not after
- Engineer, while implementing (step 3): name any new command or constraint worth keeping in the closing comment
- Orchestrator, before closing an issue (step 6): apply any command/rule the engineer flagged, then close

A section that has grown past ~7 lines is a signal to split it into its own
file, leaving one pointer line behind. AGENTS.md and process.md should never
need more than a skim to read start to finish.
