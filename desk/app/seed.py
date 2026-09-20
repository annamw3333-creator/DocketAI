from __future__ import annotations

from . import storage

HARBOR_BOT_ID = "harbor-hearth"
HAVEN_BOT_ID = "haven-abodes"

HARBOR_FAQ = [
    {
        "question": "What are your hours?",
        "answer": "Harbor & Hearth is open Tuesday–Sunday 5pm–10pm. Kitchen closes at 9:30pm. Closed Mondays.",
    },
    {
        "question": "Do you take reservations?",
        "answer": "Yes — we are happy to book a table for parties up to 8. Larger groups please call the restaurant.",
    },
    {
        "question": "Is there a vegetarian menu?",
        "answer": "We offer several vegetarian and vegan plates; ask about tonight's seasonal sides. We are pet-friendly on the patio only.",
    },
    {
        "question": "Parking?",
        "answer": "Street parking and a validated lot one block east. Validation stamps at the host stand.",
    },
    {
        "question": "Cancellation policy",
        "answer": "Please give us 24 hours notice to cancel or change a reservation so we can seat another guest.",
    },
]

HARBOR_SCRIPT = [
    "Welcome to Harbor & Hearth — how can we help tonight?",
    "I'd be glad to check availability and get that reserved for you.",
    "I'm sorry about that — I can transfer you to our manager for a callback.",
    "Our policy is 24 hours notice for cancellations.",
    "Patio seating is pet-friendly; dining room is not.",
]

HARBOR_PROMPT = """You are the Harbor & Hearth restaurant assistant.
Answer only from the approved FAQ. Warm, concise tone.
For complaints or manager requests, offer a human handoff and collect a phone number.
When booking, confirm party size, date, time, and name, then say the reservation is booked.
Never invent prices or guarantee specific tables."""

# ---------------------------------------------------------------------------
# Haven · Aesthetic Abodes — Calgary residential cleaning (conversion bot)
# Hard limits: never directly book, never promise, never refund/discount,
# never invent prices beyond the published $25 pet fee.
# ---------------------------------------------------------------------------

HAVEN_FAQ = [
    {
        "question": "What services do you offer?",
        "answer": (
            "I'd be happy to help. Aesthetic Abodes offers Calgary residential cleaning: "
            "standard cleans, deep cleans, move-in/out, listing-ready cleans, and Airbnb "
            "turnovers. Tell me which fits, plus bedrooms and whether pets are home, and "
            "I'll point you to our booking or quote form."
        ),
    },
    {
        "question": "How do I book online booking form quote form start a clean",
        "answer": (
            "I'd be glad to help you get started. I can't finalize cleans here in chat — "
            "please use https://aestheticabodes.ca/booking/ or our quote form at "
            "https://aestheticabodes.ca/instant-free-quote/. You can also text or email "
            "825-521-3311 / hello@aestheticabodes.ca. Share service type, home size, pets, "
            "and preferred timing so the team can follow up."
        ),
    },
    {
        "question": "Do you clean with pets in the home? pet fee charge extra",
        "answer": (
            "Yes — we are pet-friendly and happy to help homes with pets. When pets are "
            "present there is a $25 pet fee. Please secure pets during the visit so our "
            "team can work safely. Add pets on the quote or booking form so it's noted."
        ),
    },
    {
        "question": "Can I get the same cleaner each time?",
        "answer": (
            "When scheduling allows, we aim to send a familiar cleaner — I can't promise "
            "or guarantee a specific person. Note a preference on "
            "https://aestheticabodes.ca/booking/ or text 825-521-3311 and the desk will do "
            "their best."
        ),
    },
    {
        "question": "Where do you serve Calgary neighbourhood",
        "answer": (
            "We focus on Calgary residential homes. Share your neighbourhood or postal "
            "code if you're unsure — or start a quote at "
            "https://aestheticabodes.ca/instant-free-quote/ and the team will confirm "
            "coverage."
        ),
    },
    {
        "question": "How much does a clean cost? pricing rates",
        "answer": (
            "I'd be glad to help with pricing. It depends on home size, condition, and "
            "service type — the only dollar amount I can state is our $25 pet fee when "
            "pets are present. I don't invent other prices. Text or call 825-521-3311 or "
            "email hello@aestheticabodes.ca, or open the quote form on our site, and the "
            "team will prepare an accurate number for your Calgary home."
        ),
    },
    {
        "question": "Contact phone email reach you",
        "answer": (
            "You can reach Aesthetic Abodes at 825-521-3311 or hello@aestheticabodes.ca. "
            "I'm glad to help here too — or guide you to booking and quote forms on "
            "aestheticabodes.ca."
        ),
    },
    {
        "question": "Deep clean move-in move-out listing Airbnb bedroom price how much",
        "answer": (
            "I'd be glad to help with a deep clean for your bedroom count and home size. "
            "Deep cleans, move-in/out, listing prep, and Airbnb turnovers are all available "
            "in Calgary. I don't invent prices beyond the $25 pet fee — text or call "
            "825-521-3311 or email hello@aestheticabodes.ca and our team will be happy to "
            "prepare an accurate quote."
        ),
    },
    {
        "question": "Book Saturday appointment schedule Sam book me this weekend",
        "answer": (
            "I'd be happy to help you get Saturday set up — I can't complete or confirm "
            "bookings here in chat. Please finish on https://aestheticabodes.ca/booking/ "
            "(name, phone, service, home size, pets, preferred day). Or text 825-521-3311 / "
            "email hello@aestheticabodes.ca and the team will take it from there."
        ),
    },
    {
        "question": "Standard clean regular upkeep",
        "answer": (
            "A standard clean covers the regular upkeep that keeps your Calgary home "
            "feeling fresh between deeper resets. I'd be happy to help you start — use "
            "https://aestheticabodes.ca/booking/ or the quote form on our site, or text "
            "825-521-3311."
        ),
    },
    {
        "question": "Cancel cancellation furious ridiculous angry complaint damaged upset",
        "answer": (
            "I'm sorry you're dealing with this — that sounds frustrating. I can't resolve "
            "cancellations or damage claims here, but I'm glad to connect you with a human. "
            "Please text or call 825-521-3311 or email hello@aestheticabodes.ca and a "
            "manager will follow up. What's the best number to reach you?"
        ),
    },
    {
        "question": "Refund money back reimbursement full refund terrible want refund right now",
        "answer": (
            "I'm sorry this has been disappointing. I don't issue refunds in chat — a "
            "human on our team needs to review. Please text or call 825-521-3311 or email "
            "hello@aestheticabodes.ca with what happened and the best callback number; "
            "they'll take care of next steps."
        ),
    },
    {
        "question": "Discount coupon promo code cheaper deal freebie percent off promo code 20% leaving",
        "answer": (
            "I hear you wanting a better rate — I don't offer discounts, coupons, or "
            "promos here, and I won't invent special pricing. For an accurate quote on "
            "your home, open the quote form on our site or text/email 825-521-3311 / "
            "hello@aestheticabodes.ca and the team can help."
        ),
    },
    {
        "question": "Speak to a real person human agent manager",
        "answer": (
            "Of course — I'm glad to connect you with a human. Please text or call "
            "825-521-3311 or email hello@aestheticabodes.ca and share your name and "
            "callback number so we can transfer your request promptly."
        ),
    },
]

HAVEN_SCRIPT = [
    "Hi — I'm Haven with Aesthetic Abodes. How can I help with your Calgary home today?",
    "I'd be glad to help you get a clean booked via our forms or by text — I can't finalize it here in chat.",
    "When pets are present we add a $25 pet fee — happy to note that for your visit.",
    "When scheduling allows we aim for a familiar cleaner, though I can't guarantee a specific person.",
    "For pricing beyond the pet fee, our team will text or call you — or use the quote form on our site.",
    "You can reach us at 825-521-3311 or hello@aestheticabodes.ca anytime.",
    "I'm sorry about that — I can connect you with a human via text or email; I won't issue refunds or discounts here.",
    "Please complete https://aestheticabodes.ca/booking/ or our quote form so the team can confirm details.",
]

HAVEN_PROMPT = """You are Haven, the website assistant for Aesthetic Abodes (Calgary residential cleaning).
Display name: Haven · Aesthetic Abodes. Bubble name: Haven.

PRIMARY GOAL: conversion — guide visitors to a clean BOOKED outcome by sending them to the
booking form, Instant Free Quote form, or text/email. Be empathetic, warm, and premium.

Facts you may share:
- Phone: 825-521-3311 · Email: hello@aestheticabodes.ca
- Services: standard, deep, move-in/out, listing-ready, Airbnb turnover
- Published pet fee: $25 when pets are present
- Same-cleaner preference when scheduling allows (never guarantee a specific cleaner)
- Calgary-focused residential service
- Booking: https://aestheticabodes.ca/booking/
- Quote form: https://aestheticabodes.ca/instant-free-quote/

HARD LIMITS — NEVER:
- Do NOT directly book cleans (no confirming appointments, no "you're booked", no "I've scheduled").
- Do NOT make promises (timing guarantees, specific cleaner guarantees, outcome guarantees).
- Do NOT issue refunds.
- Do NOT offer or invent discounts, coupons, promo codes, or freebies.
- Do NOT invent prices (except stating the published $25 pet fee).

INSTEAD:
- Answer FAQs accurately from approved company knowledge.
- Empathize with frustrations.
- Collect intent (service type, home size/bedrooms, pets, preferred timing) then send them to
  Instant Free Quote or Booking form, or invite text 825-521-3311 / email hello@aestheticabodes.ca.
- For refunds, discounts, damage, or complaints: empathize + escalate to a human via text/email —
  never resolve by promising money off or a refund.
- When discussing price, prefer phone/email/quote form; do not say cleans are free.
"""


def seed_demo() -> dict:
    storage.init_db()
    bot = storage.create_bot(
        name="Harbor & Hearth",
        vertical="salon",  # demo uses hospitality; pack still runnable via cleaning/dental/etc.
        faq=HARBOR_FAQ,
        script=HARBOR_SCRIPT,
        prompt=HARBOR_PROMPT,
        bot_id=HARBOR_BOT_ID,
    )
    # Also seed a cleaning vertical twin for pack demos
    storage.create_bot(
        name="Sparkle & Co Cleaning",
        vertical="cleaning",
        faq=[
            {"question": "Deep clean price", "answer": "A deep clean for a 3-bedroom typically starts around $250; we are happy to confirm after a quick walkthrough."},
            {"question": "Pets", "answer": "We are pet-friendly — please secure pets during the visit."},
            {"question": "Book", "answer": "We can schedule Saturday mornings; please share name and phone to confirm."},
        ],
        script=[
            "Thanks for calling Sparkle & Co — how can I help?",
            "I'd be glad to book that Saturday slot for you.",
            "I'm sorry — I can transfer you to a specialist about property damage.",
        ],
        prompt="Cleaning desk: FAQ only, escalate damage claims, confirm bookings with name/phone.",
        bot_id="sparkle-cleaning",
    )
    storage.create_bot(
        name="Haven · Aesthetic Abodes",
        vertical="cleaning",
        faq=HAVEN_FAQ,
        script=HAVEN_SCRIPT,
        prompt=HAVEN_PROMPT,
        bot_id=HAVEN_BOT_ID,
    )
    return bot


def seed_haven() -> dict:
    """Ensure Haven · Aesthetic Abodes (haven-abodes) is present."""
    storage.init_db()
    return storage.create_bot(
        name="Haven · Aesthetic Abodes",
        vertical="cleaning",
        faq=HAVEN_FAQ,
        script=HAVEN_SCRIPT,
        prompt=HAVEN_PROMPT,
        bot_id=HAVEN_BOT_ID,
    )
