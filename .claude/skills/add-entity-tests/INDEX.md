# Add Entity Tests Skill - Documentation Index

This directory contains all documentation and templates for the add-entity-tests skill.

## Start Here

1. **README.md** - Overview and usage instructions
2. **QUICK_REFERENCE.md** - Critical patterns checklist (⭐ READ THIS FIRST)
3. **CORRECTIONS.md** - Common errors and how to fix them
4. **SKILL.md** - Detailed skill instructions for Claude
5. **template.md** - Code templates with placeholders

## Documentation Purpose

### QUICK_REFERENCE.md ⭐ START HERE
**Purpose**: One-page checklist of correct vs incorrect patterns
**Use when**: Generating tests or debugging test failures
**Contains**:
- ✓ Correct code patterns with examples
- ✗ Common mistakes to avoid
- Checklist before running tests
- Reference to Task entity tests

### CORRECTIONS.md
**Purpose**: Detailed explanations of each error and its fix
**Use when**: You encounter a specific error during test generation
**Contains**:
- 11 common error patterns
- Wrong vs correct code examples for each
- Explanations of why the error occurs
- Summary checklist

### README.md
**Purpose**: Skill overview and quick start guide
**Use when**: First time using the skill or showing others how to use it
**Contains**:
- What the skill does
- Prerequisites
- Usage instructions
- Example output
- Test coverage matrix
- Troubleshooting guide

### SKILL.md
**Purpose**: Complete instructions for Claude to execute the skill
**Use when**: Claude is generating the tests
**Contains**:
- Step-by-step generation process
- Questions to ask users
- File generation order
- Validation steps
- Error handling

### template.md
**Purpose**: Code templates with placeholders for generation
**Use when**: Need template structure (but prefer Task tests as examples)
**Contains**:
- Fixture template
- Mapper test template
- Service test template
- Router test template
- conftest.py updates

### examples/sample.md
**Purpose**: Complete example of User entity tests
**Status**: ⚠️ OUTDATED - Use Task tests as canonical reference instead
**Contains**:
- Full User entity test suite
- Note: Some patterns may be outdated

## Canonical Reference Implementation

**The Task entity tests are the authoritative reference:**

```
src/tests/
├── fixtures/
│   └── task_fixtures.py          ← Correct fixture patterns
└── unit/
    ├── mappers/
    │   └── test_task_mapper.py   ← Correct mapper test patterns
    ├── services/
    │   └── test_task_service.py  ← Correct service test patterns (with filters)
    └── routers/
        └── test_task.py          ← Correct router test patterns (unit style)
```

**When in doubt, copy Task test patterns exactly.**

## Quick Navigation

- **Need to generate tests?** → Start with QUICK_REFERENCE.md
- **Hit an error?** → Check CORRECTIONS.md for that specific error
- **First time using skill?** → Read README.md
- **Claude generating tests?** → Follow SKILL.md
- **Need code templates?** → Look at Task tests first, then template.md
- **Want a complete example?** → See Task tests (not sample.md - it's outdated)

## File Priority Order

When generating tests, consult documentation in this order:

1. **QUICK_REFERENCE.md** - Check correct patterns
2. **Task entity tests** - Copy exact patterns from working code
3. **CORRECTIONS.md** - Verify you're not making common mistakes
4. **SKILL.md** - Follow generation steps
5. **template.md** - Use as fallback template structure

## Common Questions

**Q: Which file should I read first?**
A: QUICK_REFERENCE.md - it has everything you need on one page.

**Q: I got an error, where do I look?**
A: Check CORRECTIONS.md for that exact error pattern with explanation.

**Q: Where are the best examples?**
A: The Task entity tests in `src/tests/`. They are tested, validated, and correct.

**Q: Is examples/sample.md accurate?**
A: No, it uses outdated patterns. Use Task tests as the reference instead.

**Q: Do I need to read template.md?**
A: Not really. It's better to copy patterns from Task tests directly.

## Updates and Maintenance

**Last Updated**: January 2026
**Based On**: Task entity test implementation
**Status**: ✅ Current and validated

**If patterns change**:
1. Update QUICK_REFERENCE.md first
2. Update CORRECTIONS.md with new error patterns
3. Update SKILL.md with new instructions
4. Update template.md if needed
5. Keep Task tests as the source of truth

## Contributing

If you find a new error pattern or improvement:
1. Verify the pattern works in actual tests
2. Add to CORRECTIONS.md with example
3. Update QUICK_REFERENCE.md if it's critical
4. Update this INDEX.md if adding new files
