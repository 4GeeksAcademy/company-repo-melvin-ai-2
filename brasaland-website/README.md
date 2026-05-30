# Brasaland Website

## Local Development

1. Open this folder in VS Code or your preferred editor.
2. From the repository root, run either the npm script:

   ```sh
   npm run web:dev
   ```

   or a Codespaces-compatible static server with npx:

   ```sh
   npx serve brasaland-website -l 8080
   ```

   If you are already inside `brasaland-website/`, you can run:

   ```sh
   npx serve . -l 8080
   ```

   or with Python:

   ```sh
   python3 -m http.server 8080 --directory brasaland-website
   ```

3. Open http://localhost:8080 in your browser or use Codespaces port forwarding.
4. For full local setup notes, see `LOCAL-DEV.md`.

## Features
- Responsive, accessible, and SEO-optimized static site
- Bilingual (English/Spanish) with language toggle
- Tailwind CSS via CDN
- Landing page, locations page, and Brasa Points sign-up form
- Custom JS for translations and dynamic logic

## File Structure
- `index.html` — Landing page
- `signup.html` — Brasa Points registration form
- `locations.html` — Locations info
- `site.js` — Bilingual logic and dynamic features

## Contact
For support, contact info@brasaland.com
