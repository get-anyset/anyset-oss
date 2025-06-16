import { defineConfig } from 'tsup';

export default defineConfig({
  entry: {
    'api-integration': 'src/api-integration/api-integration.ts',
    'api-integration/types': 'src/api-integration/types.ts',
    'components/DummyComponent': 'src/components/DummyComponent/DummyComponent.tsx',
  },
  format: ['esm', 'cjs'],
  dts: true,
  clean: true,
  external: ['react', 'react-dom'],
  tsconfig: 'tsconfig.json',
});
