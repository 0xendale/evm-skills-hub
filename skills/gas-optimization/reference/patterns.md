# Gas Waste Pattern Library

The Seeker step matches a contract against these patterns. Each has: when it applies, a before/after, and a safety note. Savings are *typical* — always measure (see SKILL.md verification).

---

## 1. Storage packing

**Applies when:** a `struct` or contiguous state variables use sub-256-bit types that aren't adjacent. The compiler packs consecutive fields that fit in one 32-byte slot.

```solidity
// before — 3 slots
struct Pos { uint256 id; address owner; uint64 ts; bool open; }

// after — 2 slots (address 20B + uint64 8B + bool 1B = 29B share a slot)
struct Pos { uint256 id; address owner; uint64 ts; bool open; }
//           ^ keep uint256 alone; group the small types together
```

**Saving:** up to ~20,000 gas per slot avoided on writes.
**Safety:** only helps when packed fields are written in the same transaction; separate writes pay read-modify-write. Don't pack fields updated independently on hot paths.

---

## 2. `constant` / `immutable` instead of storage

**Applies when:** a state variable's value is fixed at compile time (`constant`) or set once in the constructor and never changed (`immutable`).

```solidity
// before
uint256 public fee = 30;            // SLOAD ~2100 each read

// after
uint256 public constant FEE = 30;   // inlined into bytecode, ~free
```

**Saving:** ~2,100 gas per avoided cold `SLOAD`.
**Safety:** value must truly never change after deployment.

---

## 3. Calldata over memory for external read-only args

**Applies when:** an `external`/`public` function takes an array/`string`/`bytes` arg it only reads.

```solidity
// before
function sum(uint256[] memory xs) external pure returns (uint256 s) { ... }

// after
function sum(uint256[] calldata xs) external pure returns (uint256 s) { ... }
```

**Saving:** avoids copying calldata into memory + memory expansion.
**Safety:** `calldata` is read-only; if the body mutates the arg, keep `memory`.

---

## 4. Cache storage reads / array length in loops

**Applies when:** a loop reads `arr.length` or any storage value every iteration.

```solidity
// before
for (uint256 i = 0; i < arr.length; i++) { total += arr[i]; }

// after
uint256 len = arr.length;                 // one SLOAD, then stack (dup)
for (uint256 i = 0; i < len; i++) { total += arr[i]; }
```

**Saving:** ~100 gas per avoided warm `SLOAD` per iteration (more if cold).
**Safety:** only cache values that don't change inside the loop.

---

## 5. Unchecked increment for bounded counters

**Applies when:** a loop counter (or other arithmetic) provably cannot overflow.

```solidity
// before
for (uint256 i = 0; i < len; i++) { ... }

// after
for (uint256 i = 0; i < len;) { ...; unchecked { ++i; } }
```

**Saving:** ~30–40 gas per operation (Solidity ≥0.8 overflow checks removed).
**Safety:** NEVER wrap user-controlled inputs or token/balance math without a prior `require` bound. Overflow here is a critical vulnerability.

---

## 6. Mappings over arrays for lookup

**Applies when:** code scans an array to find/validate an element and does not need ordered iteration.

```solidity
// before — O(n) scan
address[] members;
function isMember(address a) public view returns (bool) {
    for (uint256 i; i < members.length; ++i) if (members[i] == a) return true;
    return false;
}

// after — O(1) keccak slot
mapping(address => bool) isMember;
```

**Saving:** scales with n; turns linear `SLOAD`s into one.
**Safety:** lose cheap enumeration; keep an array too if you must iterate.

---

## 7. Transient storage (EIP-1153, Cancun)

**Applies when:** a flag or accumulator only needs to live for the duration of one transaction (reentrancy locks, Uniswap-V4-style flash accounting of net deltas).

```solidity
// before — 20k cold SSTORE to set, refund on clear
bool private locked;

// after — TSTORE/TLOAD, flat 100 gas, auto-cleared at tx end
//   assembly { tstore(0, 1) }  ... assembly { let l := tload(0) }
```

**Saving:** 100 gas vs up to 20,000 per slot.
**Safety:** clears at the end of the **transaction**, not the call frame. Explicitly reset flags (`locked = false`) so nested/batched calls in the same tx don't inherit stale state.

---

## 8. Bitwise shift for ×/÷ by powers of two

**Applies when:** multiplying or dividing by a constant power of two.

```solidity
// before:  x * 2     x / 2      (MUL/DIV cost 5 gas)
// after :  shl(1, x) shr(1, x)  (SHL/SHR cost 3 gas)   // in assembly
```

**Saving:** 2 gas per op. Often the compiler already does this — **measure before claiming it.**
**Safety:** semantics differ for signed division (rounding toward zero vs floor); only for unsigned.

---

## 9. Branchless min/max in Yul

**Applies when:** a hot path uses `if/else` to pick a max/min, and the `JUMPI` cost matters.

```solidity
// after — no conditional jump
// z := xor(x, mul(xor(x, y), gt(y, x)))   // z = max(x, y)
```

**Saving:** avoids `JUMP`/`JUMPI` pipeline disruption.
**Safety:** assembly bypasses Solidity's safety checks; keep it tiny and well-commented.

---

## 10. EVM scratch space for hashing (Yul)

**Applies when:** computing a `keccak256` of a few words and you want to skip memory-expansion cost.

**Mechanics:** memory `0x00`–`0x3f` is free scratch space; `0x40` holds the free-memory pointer; `0x60`–`0x80` is the zero slot and must stay empty.

```solidity
// assembly {
//   mstore(0x00, key)
//   mstore(0x20, slot)
//   let h := keccak256(0x00, 0x40)
// }
```

**Saving:** avoids allocating fresh memory + expansion cost.
**Safety:** when mixing Yul and Solidity, restore/advance the free-memory pointer at `0x40` to avoid memory collisions.
