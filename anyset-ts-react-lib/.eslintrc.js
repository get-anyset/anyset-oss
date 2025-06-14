module.exports = {
  root: true, // Prevent ESLint from looking further up the directory tree
  parser: '@typescript-eslint/parser',
  plugins: [
    '@typescript-eslint',
    'react',
    'react-hooks',
    'jsx-a11y',
  ],
  extends: [
    'eslint:recommended',
    'plugin:@typescript-eslint/recommended',
    'plugin:react/recommended',
    'plugin:react/jsx-runtime', // For new JSX transform
    'plugin:react-hooks/recommended',
    'plugin:jsx-a11y/recommended',
    'eslint-config-prettier', // Must be last to override other configs
  ],
  settings: {
    react: {
      version: 'detect', // Automatically detect the React version
    },
  },
  env: {
    browser: true,
    es2021: true,
    node: true,
    jest: true, // For Jest global variables in test files
  },
  rules: {
    // Basic ESLint rules
    'no-console': 'warn',
    'no-unused-vars': 'off', // Use @typescript-eslint/no-unused-vars instead

    // TypeScript specific rules
    '@typescript-eslint/no-unused-vars': ['warn', { argsIgnorePattern: '^_' }],
    '@typescript-eslint/explicit-module-boundary-types': 'off',
    '@typescript-eslint/no-explicit-any': 'warn',

    // React specific rules
    'react/prop-types': 'off', // Not needed with TypeScript
    'react/jsx-key': 'warn',
    'react-hooks/rules-of-hooks': 'error',
    'react-hooks/exhaustive-deps': 'warn',

    // Add any project specific rules here
  },
  overrides: [
    {
      files: ['*.js', '*.cjs', '*.mjs'], // Files to consider as Node.js environment (e.g. config files)
      env: {
        node: true,
        browser: false,
      },
      rules: {
        '@typescript-eslint/no-var-requires': 'off', // Allow require in JS files like .eslintrc.js itself
      }
    },
    {
      files: ['**/__tests__/**/*.[jt]s?(x)', '**/?(*.)+(spec|test).[jt]s?(x)'],
      extends: ['plugin:testing-library/react'], // if @testing-library/react is used
    }
  ],
  ignorePatterns: [
    'node_modules/',
    'dist/',
    'build/',
    '.rsbuild/',
    '*.js', // Ignoring root level JS config files for now, will refine if needed
    '*.cjs',
    '*.mjs',
    'coverage/'
  ],
};
