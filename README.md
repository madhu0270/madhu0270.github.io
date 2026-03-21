# Portfolio (mdhakite.xyz)

Static, single-page portfolio inspired by a typographic, editorial layout (similar in *structure* to [baim.my](https://baim.my/)), tailored to **Madhusudan Dhakite**, QA, automation, and delivery.

## Run locally

Open `index.html` in a browser, or serve the folder:

```bash
npx serve .
```

## Deploy

Upload the HTML pages, `styles.css`, `script.js`, and `assets/` to your web host (or connect this folder to Netlify / Cloudflare Pages / GitHub Pages). The **Blog** section and header CTA point to [blogs.mdhakite.xyz](https://blogs.mdhakite.xyz) (configure DNS/hosting so that subdomain serves your blog).

## Assets

- `assets/headshot.png`, replace this file to update your photo (keep the same filename or change paths in `index.html`).
- `assets/logos/`, local marks for credentials (Google “G”, Harvard Kennedy School badge, Simplilearn & Tricentis square SVGs, Agile Alliance PNG from [agilealliance.org](https://www.agilealliance.org/)). Swap files if you refresh branding.

## Customize

- **LinkedIn**: Update the `href` on the LinkedIn pill in `index.html` if your public profile URL differs.
- **Employer-specific projects**: The live résumé PDF is linked; you can add a “Featured work” grid later with real case studies and images.
- **Colors / fonts**: Edit CSS variables at the top of `styles.css`.
