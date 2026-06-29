# EVM Cost Model

Ground every optimization claim in these facts. Costs are post-Cancun and approximate; the compiler version and warm/cold state shift exact numbers, so **measure** rather than asserting from this table.

## Data location cost hierarchy

| Location | Op | Cost (approx) | Notes |
|---|---|---|---|
| Persistent storage | `SSTORE` set (zero→nonzero) | ~20,000 | Most expensive; modifies permanent state |
| | `SSTORE` update (warm) | ~5,000 | Slot already touched this tx |
| | `SLOAD` cold | ~2,100 | First read of a slot in a tx |
| | `SLOAD` warm | ~100 | Subsequent reads |
| Transient storage | `TSTORE`/`TLOAD` | 100 (flat) | EIP-1153; cleared at end of **transaction** |
| Memory | `MSTORE`/`MLOAD` | ~3/word | Plus **quadratic expansion** as memory grows |
| Calldata | `CALLDATALOAD` | ~3/word | Read-only; no alloc/copy |

**Quadratic memory expansion:** the EVM charges progressively more gas as the memory high-water mark rises. Large or unbounded memory arrays can dominate cost and cause out-of-gas. Prefer calldata for read-only inputs; bound memory usage.

## Storage slots and packing

- Storage is addressed in 32-byte (256-bit) slots.
- The compiler packs **consecutive** state/struct fields that together fit in one slot. A `uint256` fills a slot alone; `address` (20B) + `uint64` (8B) + `bool` (1B) = 29B share one slot.
- Reorder declarations so small types are adjacent → fewer `SSTORE`s. Packing only pays off when packed fields are written together.

## Opcode quick costs

| Op | Cost | Cheaper alternative |
|---|---|---|
| `MUL` / `DIV` | 5 | `SHL` / `SHR` = 3 (powers of two, unsigned) |
| checked `+`/`-`/`*` (≥0.8) | base + ~30–40 | `unchecked { }` when provably bounded |
| `JUMPI` (branch) | disrupts pipeline | branchless bitwise in Yul |

## Memory layout (for Yul)

| Range | Meaning |
|---|---|
| `0x00`–`0x3f` | Scratch space — free to use for hashing/temp without expansion |
| `0x40` | Free-memory pointer — update manually when mixing Yul/Solidity |
| `0x60`–`0x80` | Zero slot — must remain empty |

## Transient storage semantics (EIP-1153)

- Behaves like storage but **erased at the end of the transaction**, not the call frame.
- Enables flash accounting (track net deltas across swaps/liquidity ops, settle at tx boundary).
- **Must** be explicitly reset (e.g. `locked = false`) so batched/nested calls in the same tx don't read stale state.

## `constant` vs `immutable`

- `constant` — evaluated at compile time, inlined into bytecode.
- `immutable` — evaluated once in the constructor, embedded in runtime bytecode.
- Both replace ~2,100-gas `SLOAD`s with near-free bytecode reads.
