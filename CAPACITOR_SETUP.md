# Capacitor Setup

1. Deploy the Streamlit app to Render.
2. Set your Render URL in `capacitor.config.ts` via `CAPACITOR_WEB_URL`.
3. Run `npm install`.
4. Run `npm run cap:add:android` once.
5. Run `npm run cap:sync`.
6. Run `npm run cap:open` and build the AAB in Android Studio.

Notes:
- This wrapper uses the hosted web app URL.
- Supabase stays unchanged.
- Browser notifications inside Streamlit still work while the web app is open.
