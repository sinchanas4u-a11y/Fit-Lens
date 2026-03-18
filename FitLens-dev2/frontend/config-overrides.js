module.exports = function override(config, env) {
  // Fix for webpack dev server allowedHosts issue
  if (config.devServer) {
    config.devServer.allowedHosts = 'all';
  }
  return config;
};
