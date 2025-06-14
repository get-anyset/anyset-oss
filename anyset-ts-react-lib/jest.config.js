module.exports = {
  preset: 'ts-jest',
  testEnvironment: 'jest-environment-jsdom',
  roots: ['<rootDir>/src'], // Look for tests in the src directory
  moduleNameMapper: {
    // Handle CSS Modules (if you use them, e.g., *.module.css, *.module.scss)
    '\.(css|less|scss|sass)$': 'identity-obj-proxy',
    // Handle static assets
    '\.(jpg|jpeg|png|gif|webp|svg)$': '<rootDir>/__mocks__/fileMock.js',
    // Alias for imports like @/components/*
    '^@/(.*)$': '<rootDir>/src/$1',
  },
  setupFilesAfterEnv: ['<rootDir>/jest.setup.js'], // For setting up testing library, etc.
  transform: {
    '^.+\.(ts|tsx)$': ['ts-jest', {
      tsconfig: '<rootDir>/tsconfig.json', // Use the package's tsconfig
    }],
  },
  collectCoverageFrom: [
    'src/**/*.{ts,tsx}',
    '!src/**/*.d.ts', // Don't collect coverage from declaration files
    '!src/**/index.{ts,tsx}', // Usually, index files just re-export, adjust if needed
    '!src/**/stories.{ts,tsx}', // Exclude storybook files if any
    '!src/__mocks__/**/*', // Exclude mocks
  ],
  coverageDirectory: 'coverage',
  coverageReporters: ['json', 'lcov', 'text', 'clover'],
  // reporters: [ "default", "jest-junit" ] // Example for JUnit reports if needed
};
