---
description: Learn a concept using the 80/20 rule - get the essential knowledge without the fluff
---

# /learning - Accelerated Understanding

## Purpose
When I suggest something you don't understand, use this command. I'll explain the concept optimized for a **PM with mid-level engineering knowledge** — not a tutorial for beginners, not a PhD thesis.

## How to Use
```
/learning [concept or technology]
```

## What I Will Provide

### The 80/20 Explanation

1. **What it is** (1-2 sentences)
2. **Why it matters for our project** (direct relevance)
3. **How it works** (mental model, not implementation details)
4. **When to use it** (decision criteria)
5. **When NOT to use it** (anti-patterns)
6. **One real example** from our codebase or project

## Format

```markdown
# Learning: [Concept Name]

## TL;DR
[One sentence that captures the essence]

## Why This Matters for AIVideoGen
[Direct connection to our project]

## Mental Model
[Analogy or simplified explanation]

```
[Simple diagram if helpful]
```

## Decision Guide
| Use When | Don't Use When |
|----------|----------------|
| ... | ... |

## In Our Project
[Concrete example of where/how we'd use this]

## Go Deeper (Optional)
- [Link to best resource if you want to learn more]
```

---

## Example

**You**: `/learning` What's a webhook and why do we need one?

**Me**:
```markdown
# Learning: Webhooks

## TL;DR
A webhook is a "reverse API" — instead of us asking a server for data, the server pushes data to us when something happens.

## Why This Matters for AIVideoGen
When a video finishes processing on ElevenLabs, instead of us checking every 5 seconds "is it done?", ElevenLabs can ping our server: "Hey, it's done. Here's the file."

## Mental Model
Think of it like pizza delivery:
- **Polling (checking)**: Calling the pizza shop every 2 minutes: "Is my pizza ready?"
- **Webhook**: Giving them your number. They call YOU when it's ready.

```
WITHOUT WEBHOOK:              WITH WEBHOOK:
┌──────┐  check? ┌──────┐    ┌──────┐         ┌──────┐
│ You  │ ──────► │Server│    │ You  │ ◄────── │Server│
│      │ ◄────── │      │    │      │  done!  │      │
│      │   no    │      │    │      │         │      │  
│      │ ──────► │      │    └──────┘         └──────┘
│      │ ◄────── │      │
│      │   yes!  │      │
└──────┘         └──────┘
(wastes resources)        (efficient)
```

## Decision Guide
| Use Webhooks When | Don't Use When |
|-------------------|----------------|
| Long-running external process | Quick synchronous responses |
| You need real-time updates | You control both systems |
| Third-party service (ElevenLabs, Stripe) | Internal microservices (use queues) |

## In Our Project
ElevenLabs TTS can take 10-30 seconds. Instead of polling, we'll:
1. Register a webhook URL: `https://our-app.com/api/webhooks/tts-complete`
2. ElevenLabs calls that URL when audio is ready
3. We save the audio and trigger video composition

## Go Deeper (Optional)
- [Webhook.site](https://webhook.site) - Free tool to test webhooks
```

---

## What I Won't Do

- ❌ Assume you know nothing (no "first, let's understand what a variable is")
- ❌ Go into academic depth (no "the lambda calculus origins of...")
- ❌ Give you a tutorial (no "Step 1: Install Node.js")
- ❌ Make you feel dumb (this is learning, not gatekeeping)

---

> [!TIP]
> Use this liberally. There's no shame in not knowing something. The AI subscription is your tuition — get your money's worth.
