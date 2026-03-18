import type { CapacitorConfig } from '@capacitor/cli';

const config: CapacitorConfig = {
  appId: 'de.meinausflug.app',
  appName: 'MeinAusflug',
  webDir: 'www',
  server: {
    url: 'https://meinausflug.onrender.com',
    cleartext: false
  }
};

export default config;