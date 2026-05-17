import baseConfig from './js_config.mjs';
import globals from 'globals';

export default [
  ...baseConfig,
  {
    languageOptions: {sourceType: 'module', globals: {...globals.browser}},
  },
];
