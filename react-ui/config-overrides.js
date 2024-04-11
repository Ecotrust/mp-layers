module.exports = function override(config, env) {
    // Do not append hashes to filenames in production
    // if (env === 'production') {
      config.output.filename = 'static/js/layer_picker.js';
      config.output.chunkFilename = 'static/js/layer_picker.chunk.js';
      config.plugins.forEach(plugin => {
        if (plugin.constructor.name === 'MiniCssExtractPlugin') {
          plugin.options.filename = 'static/css/layer_picker.css';
          plugin.options.chunkFilename = 'static/css/layer_picker.chunk.css';
        }
        if (plugin.constructor.name === 'ManifestPlugin') {
          plugin.generate = (seed, files, entrypoints) => {
            const manifestFiles = files.reduce((manifest, file) => {
              manifest[file.name] = file.path;
              return manifest;
            }, seed);
            const entrypointFiles = entrypoints.main.filter(
              fileName => !fileName.endsWith('.map')
            );
  
            return {
              files: manifestFiles,
              entrypoints: entrypointFiles,
            };
          };
        }
      });
    // }
  
    return config;
  };