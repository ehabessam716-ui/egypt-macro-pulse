# Vercel front door

This folder is the whole Vercel project: it serves the site under a clean address (e.g. `egypt-pulse.vercel.app`)
by proxying every request to the GitHub Pages build, and adds HTTP security headers GitHub Pages cannot set.
Nothing is built here — data keeps updating automatically through the GitHub workflows.

Set up once in the Vercel dashboard: Add New → Project → import `egypt-macro-pulse` → Root Directory: `vercel`
→ Framework preset: Other → Deploy. Then Settings → Domains to pick the name (or add your own domain later).
