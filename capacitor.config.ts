import type { CapacitorConfig } from "@capacitor/cli";

const WEB_URL = process.env.CAPACITOR_WEB_URL || "https://YOUR-RENDER-URL.onrender.com";

const config: CapacitorConfig = {
  appId: "de.meinausflug.app",
  appName: "MeinAusflug",
  webDir: "www",
  bundledWebRuntime: false,
  server: {
    url: WEB_URL,
    cleartext: false,
    androidScheme: "https"
  },
};

export default config;
