import type { CapacitorConfig } from '@capacitor/cli';

const config: CapacitorConfig = {
  appId: 'de.meinausflug.app',
  appName: 'MeinAusflug',
  webDir: 'www',
  android: {
    allowMixedContent: false,
  },
  server: {
    url: 'https://meinausflug.onrender.com',
    cleartext: false,
    androidScheme: 'https',
  },
  plugins: {
    SplashScreen: {
      launchShowDuration: 1200,
      backgroundColor: '#0e1117',
      androidScaleType: 'CENTER_CROP',
      showSpinner: false,
    },
  },
};

export default config;
