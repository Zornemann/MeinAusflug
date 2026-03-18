import type { CapacitorConfig } from '@capacitor/cli';

const config: CapacitorConfig = {
  appId: 'de.meinausflug.app',
  appName: 'MeinAusflug',
  webDir: 'www',
  bundledWebRuntime: false,
  server: {
    url: 'https://meinausflug.onrender.com',
    cleartext: false,
    androidScheme: 'https'
  },
  plugins: {
    SplashScreen: {
      launchShowDuration: 1200,
      backgroundColor: '#ffffff',
      showSpinner: false
    }
  }
};

export default config;
