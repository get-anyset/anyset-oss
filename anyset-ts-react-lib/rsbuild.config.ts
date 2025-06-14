import { defineConfig } from '@rsbuild/core';
import { pluginReact } from '@rsbuild/plugin-react';
import { pluginSvgr } from '@rsbuild/plugin-svgr';
// Ensure you have `styled-components` or `@emotion/styled` if you use pluginStyledComponents
// For this setup, we'll assume styled-components might be used by components in the library.
// If not, this plugin can be removed.
// import { pluginStyledComponents } from '@rsbuild/plugin-styled-components';
import { pluginBabel } from '@rsbuild/plugin-babel';

export default defineConfig({
  plugins: [
    pluginReact(),
    pluginSvgr({
      svgrOptions: {
        exportType: 'default', // Or 'named' if you prefer
      }
    }),
    // pluginStyledComponents(), // Uncomment if styled-components is a direct dependency or peerDependency of your library
    pluginBabel({
      include: /\.(?:jsx?|tsx?)$/,
      exclude: /[\/]node_modules[\/]/,
    }),
  ],
  build: {
    target: 'es2020', // Or your desired target
    outDir: 'dist',
    sourceMap: true, // Generate source maps for easier debugging
    // Configure for library mode
    lib: {
      entry: './src/index.ts', // Assuming src/index.ts is the entry point
      name: 'AnysetReact', // Global variable name if used in UMD builds
      formats: ['es', 'cjs', 'umd'], // Output formats
      fileName: (format, entryName) => `${entryName}.${format}.js`, // Naming convention for output files
    },
    // Rsbuild will automatically configure externals for peerDependencies.
    // If you have other externals, you can define them here.
    // externals: {
    //   'some-other-lib': 'SomeOtherLib',
    // },
    // Ensure CSS is handled appropriately for a library
    // This might involve extracting CSS to separate files or embedding it,
    // depending on your library's needs.
    // For now, default Rsbuild behavior for CSS in libraries is usually sufficient.
    cssMinify: 'lightningcss', // Use lightningcss for faster CSS minification
  },
  // Define source entry if not using the default 'src/index' pattern recognized by rsbuild
  source: {
    entry: {
      index: './src/index.ts', // Explicitly define entry
    },
  },
  output: {
    // Ensures that assets like SVGs are handled correctly when bundled.
    // dataUriCondition: {
    //   maxSize: 10 * 1024, // Inline assets smaller than 10kb (adjust as needed)
    // },
    // Set a public path if your library's assets need to be loaded from a specific path
    // assetPrefix: '/static/', // Example for assets served from /static/
  },
  tools: {
    // Optional: Further fine-tune bundler (e.g., Rspack or Webpack) configuration
    // bundlerChain(chain, { bundler }) {
    //   if (bundler.name === 'rspack') {
    //     // Rspack specific configurations
    //   }
    // }
    // Configure TypeScript to emit declaration files
    // This is crucial for a TypeScript library.
    // Rsbuild handles this via its TypeScript plugin integration usually.
    // We will also adjust tsconfig.json for this.
  },
  // Ensure that tsconfig.json path is correctly resolved if it's not in the default location
  // performance: {
  //   printFileSize: true,
  // },
});
