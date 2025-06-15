module.exports = {
  printWidth: 100,
  singleQuote: true,
  trailingComma: 'es5',
  plugins: ['@trivago/prettier-plugin-sort-imports'],
  importOrderSeparation: true,
  importOrderSortSpecifiers: true,
  importOrder: ['^react(.*)$', '<THIRD_PARTY_MODULES>', '^@/(.*)$', '^[./]'],
};
