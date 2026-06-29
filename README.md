# EVM Skills Hub

A public library of installable **EVM agent-skills**. Drop them into your AI
coding agent and it can audit, optimize, and analyze EVM smart contracts.

## Skills

| Skill | Use it when you want to… |
|---|---|
| [`gas-optimization`](skills/gas-optimization/SKILL.md) | Reduce gas; storage packing, calldata, unchecked math, transient storage — measured, not guessed. |
| [`vulnerability-scanning`](skills/vulnerability-scanning/SKILL.md) | Get a severity-rated security audit (reentrancy, access control, delegatecall, SWC-mapped). |
| [`arbitrage-analysis`](skills/arbitrage-analysis/SKILL.md) | Quantify DeFi arbitrage net of fees, gas, and slippage. |

## Install

### Claude Code (plugin — recommended)
```
/plugin marketplace add <owner>/evm-skills-hub
/plugin install evm-skills-hub
```
All skills install together and update with the marketplace.

### Any other agent runtime
Each skill is a self-contained folder. Copy the one(s) you want into your
runtime's skills directory:
```bash
# example: into a project-local Claude skills dir
cp -r skills/vulnerability-scanning ~/.claude/skills/
# or the cross-runtime location read by Codex/Gemini/etc.
cp -r skills/vulnerability-scanning ~/.agents/skills/
```
The skill activates when your agent matches a request to its `description`.

## How a skill works

Each skill drives a four-step workflow — **Seek → Innovate → Execute → Manage** —
that your agent follows, invoking real tools (e.g. Slither, Foundry) via your
shell when available and degrading gracefully when not. Skills are
runtime-agnostic and self-contained.

## Contributing

See [`AGENTS.md`](AGENTS.md) for the canonical skill format and how to add one.

## License
MIT
