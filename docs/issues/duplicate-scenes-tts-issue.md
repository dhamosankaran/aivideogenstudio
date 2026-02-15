# Issue Report: Duplicate Scenes in TTS/Video (Scene 1 & Scene 6)

**Date**: 2026-02-10  
**Status**: Root Cause Identified  
**Video ID**: 7 (script_id: 7)  
**Title**: How to Change Your Life 1% at a Time 📈

---

## Problem Summary

Scene 1 and Scene 6 are appearing **twice** in both the TTS audio and final video:

### Scene 1 Duplication:
- **First appearance**: "This simple math will blow your mind: tiny changes lead to radical transformation. Here is why."
- **Second appearance**: "This simple math will blow your mind: tiny changes lead to radical transformation. Here is why Atomic Habits is essential reading."

### Scene 6 Duplication:
- **First appearance**: "What is one tiny habit you are starting today? Comment below and subscribe for more life-changing book reviews!"
- **Second appearance**: "What's one tiny habit you're starting today? Comment below!"

---

## Root Cause Analysis

### The Issue is in Script Formatting Logic

**File**: `/backend/app/services/script_service.py`  
**Lines**: 159-163

```python
# Format for TTS (just the narration text)
formatted_parts = [script_data.hook]  # ← HOOK ADDED HERE
formatted_parts.extend([s.text for s in script_data.scenes])  # ← SCENE 1-6 ADDED HERE (Scene 1 contains hook!)
formatted_parts.append(script_data.call_to_action)  # ← CTA ADDED HERE (Scene 6 contains CTA!)
formatted_script = " ".join(formatted_parts)
```

The code concatenates:
1. `script_data.hook` (the standalone hook)
2. All scenes (where Scene 1 already contains the hook content)
3. `script_data.call_to_action` (the standalone CTA, but Scene 6 already contains it)

### Why This Happens

The **LLM is following the prompt correctly**:

**File**: `/backend/app/prompts/__init__.py`  
**Lines**: 339-341, 356-357 (Book Review Prompt)

```
1. Scene 1 – Hook (~5 seconds, 12-15 words):
   Open with a bold, curiosity-driven statement about the book's core message.

6. Scene 6 – CTA (~5 seconds, 12-15 words):
   Strong call to action. Ask a question or prompt engagement.
```

But also:

```
"hook": "Bold opening statement about the book. 12-15 words.",
...
"call_to_action": "Engaging CTA - question or follow prompt",
```

The prompt asks for:
- A separate `hook` field
- Scene 1 which should be a "hook scene"
- A separate `call_to_action` field  
- Scene 6 which should be a "CTA scene"

This creates **semantic overlap** that the script service then combines, resulting in duplication.

---

## Evidence from Database

**Script 7 formatted_script** (used for TTS):
```
This simple math will blow your mind: tiny changes lead to radical transformation. Here is why. [DUPLICATE START]
This simple math will blow your mind: tiny changes lead to radical transformation. Here is why Atomic Habits is essential reading. [DUPLICATE END]
Author James Clear spent years studying the science of behavior...
[... scenes 3-5 ...]
What is one tiny habit you are starting today? Comment below and subscribe for more life-changing book reviews! [DUPLICATE START]
What's one tiny habit you're starting today? Comment below! [DUPLICATE END]
```

---

## Solution Options

### Option 1: Remove Hook/CTA from formatted_script (Recommended)
**Modify**: `/backend/app/services/script_service.py` line 159-163

```python
# Format for TTS (just the narration text from scenes only)
formatted_parts = [s.text for s in script_data.scenes]  # Don't include hook/CTA separately
formatted_script = " ".join(formatted_parts)
```

**Pro**: Simple fix, scenes already contain the hook and CTA content
**Con**: Breaks the mental model that hook/CTA are separate

### Option 2: Update Prompt to Be Explicit
**Modify**: `/backend/app/prompts/__init__.py`

Update the book review prompt to clarify:
- Scene 1 should NOT duplicate the hook field
- Scene 6 should NOT duplicate the call_to_action field
- Hook/CTA fields should be UNIQUE content

**Pro**: Keeps the structured data clean
**Con**: More complex prompt, may confuse LLM

### Option 3: Smart Detection + Removal
**Modify**: `/backend/app/services/script_service.py`

Add logic to detect if Scene 1 starts with hook content and skip adding hook separately:

```python
formatted_parts = []
# Only add hook if Scene 1 doesn't already contain it
if not script_data.scenes[0].text.startswith(script_data.hook[:20]):
    formatted_parts.append(script_data.hook)
formatted_parts.extend([s.text for s in script_data.scenes])
# Only add CTA if Scene 6 doesn't already contain it
if not script_data.scenes[-1].text.endswith(script_data.call_to_action[-20:]):
    formatted_parts.append(script_data.call_to_action)
formatted_script = " ".join(formatted_parts)
```

**Pro**: Handles both old and new scripts gracefully
**Con**: More complex, fragile logic

---

## Recommended Fix

**Use Option 1** because:
1. The scenes array already contains the full narrative flow (hook → content → CTA)
2. The separate `hook` and `call_to_action` fields are metadata for structure analysis, not separate narration
3. This is consistent with how commentary scripts work (lines 278-281 in the same file)

---

## Additional Notes

- This issue affects **book review videos** (60s format) specifically
- Regular news videos (20-30s) may have the same issue but it's less noticeable
- The same duplication pattern exists in `generate_commentary_script()` method (lines 278-281), suggesting this is intentional but creates TTS issues

---

## Next Steps

1. Decide on solution approach
2. Update script_service.py
3. Test with existing script 7 (may need to regenerate audio)
4. Update any other content types that use this pattern
