// Load configuration from environment or config file
const path = require('path');
// Environment variable overrides
const config = {
  disableHotReload: process.env.DISABLE_HOT_RELOAD === 'true',
};
module.exports = {
  webpack: {
    alias: {
      '@': path.resolve(__dirname, 'src'),
    },
    configure: (webpackConfig) => {
      
      // Disable hot reload completely if environment variable is set
      if (config.disableHotReload) {
        // Remove hot reload related plugins
        webpackConfig.plugins = webpackConfig.plugins.filter(plugin => {
          return !(plugin.constructor.name === 'HotModuleReplacementPlugin');
        });
        
        // Disable watch mode
        webpackConfig.watch = false;
        webpackConfig.watchOptions = {
          ignored: /.*/, // Ignore all files
        };
      }
      
      return webpackConfig;
    },
  },
  devServer: {
    host: '0.0.0.0',
    port: 3000,
    allowedHosts: 'all',
    historyApiFallback: true,
    headers: {
      'Access-Control-Allow-Origin': '*',
    },
    // Client configuration for newer webpack versions
    client: {
      webSocketURL: 'auto://0.0.0.0:0/ws'
    }
  }
};
