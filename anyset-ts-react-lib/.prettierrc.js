module.exports = {
  printWidth: 100,
  singleQuote: true,
  trailingComma: 'es5',
  // Add the plugin and its configuration
  plugins: ['@trivago/prettier-plugin-sort-imports'],
  importOrder: [
    '^react(.*)$', // React and react-native
    '<THIRD_PARTY_MODULES>', // Third-party modules
    '^@/(.*)$', // Internal aliases
    '^[./]', // Relative imports
  ],
  importOrderSeparation: true,
  importOrderSortSpecifiers: true,
};
