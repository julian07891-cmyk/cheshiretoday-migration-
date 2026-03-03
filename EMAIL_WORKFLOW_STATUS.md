# Cheshire Today – Production Email Workflow Summary  
**Date:** 28 February 2026  

## 1️⃣ Welcome Newsletter

**Purpose:** First email sent to new subscribers to onboard them and explain the newsletter options.  

**Status:** ✅ Ready for production  

**Key Features:**  
- **Width & Responsiveness:** 680px, mobile-friendly via viewport meta.  
- **Personalization:** Subscriber email used in tracked preference & unsubscribe links.  
- **Links:**  
  - Preferences → `/newsletter/preferences?email=...`  
  - Unsubscribe → `/unsubscribe?email=...`  
  - Both are tracked per recipient (`_get_tracked_url` applied).  
- **Content/Layout:**  
  - Hero section included (if available).  
  - Clean HTML text, no placeholder links or “Read More →”.  
  - Brand-aligned styling.  
- **Testing:** Preview generated: `/tmp/welcome_email_preview.html`  
- **Backend Status:** `email_service.py` compiles; helper functions for tracked links present.  

---

## 2️⃣ Daily Brief

**Purpose:** Daily 07:30 AM email summarizing the top Cheshire + business + AI/Tech news.  

**Status:** ✅ Ready for production (scheduler disabled until go-live)  

**Key Features:**  
- **Sections:**  
  - Local Developments (max 3 articles)  
  - Business & Finance (max 2)  
  - AI & Technology (max 1)  
  - National Context (max 2)  
- **Article Selection:**  
  - Deduplicated by title & keyword similarity.  
  - Pillar enforcement: Local → AI/Tech → Business → National  
  - Gaming, entertainment, and non-project categories excluded.  
- **Fallbacks:**  
  - AI/Tech fallback: last 48h Mongo query ensures authority presence.  
- **Personalization:**  
  - Tracked preference & unsubscribe links per recipient.  
- **Testing:** Preview generated: `/tmp/daily_brief_preview.html`  

---

## 3️⃣ Weekly Roundup

**Purpose:** Sunday 09:00 AM digest highlighting major weekly stories.  

**Status:** ✅ Ready for production  

**Key Features:**  
- **Sections:**  
  - “In Case You Missed It” (top trending content)  
- **Article Selection & Bucketing:**  
  - Rebucketing ensures project-aligned pillars (Local → Business → AI/Tech → National).  
- **Personalization:**  
  - Tracked preference & unsubscribe links included per recipient.  
- **Testing:** Preview generated: `/tmp/weekly_roundup_preview_fixed.html`  

---

## 4️⃣ Technical Notes

- **SMTP:** Configured but not required for preview/testing; production-ready settings stored in environment variables (`SMTP_HOST`, `SMTP_USER`, `SMTP_PASSWORD`).  
- **Backend:**  
  - `backend/app/email_service.py` contains all helpers for:  
    - `_is_local`, `_is_business`, `_is_tech`  
    - `_is_banned_category`  
    - `_get_tracked_url`  
  - Bucketing, caps, and post-cap rebucketing applied.  
- **Preview:** All previews written to `/tmp/` for verification before sending.  

---

## 5️⃣ Next Steps to Go-Live

1. Configure SMTP credentials for production.  
2. Enable scheduler for Daily Brief and Weekly Roundup.  
3. Optional: Run a small test batch to verify tracking links & analytics.  
