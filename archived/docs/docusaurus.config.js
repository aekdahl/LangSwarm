module.exports = {
  onBrokenLinks: 'warn', // Change this to 'ignore' or 'error' if needed
  title: 'LangSwarm Docs',
  tagline: 'Documentation for LangSwarm',
  url: 'https://aekdahl.github.io',
  baseUrl: '/LangSwarm/',
  organizationName: 'aekdahl',
  projectName: 'LangSwarm',
  presets: [
    [
      'classic',
      {
        docs: {
          routeBasePath: '/',
          path: './docs',
        },
        theme: {
          customCss: require.resolve('./src/css/custom.css'),
        },
      },
    ],
  ],
  themeConfig: {
    navbar: {
      title: 'LangSwarm',
      items: [
        { to: 'docs/getting-started', label: 'Docs', position: 'left' },
        { href: 'https://github.com/aekdahl/LangSwarm', label: 'GitHub', position: 'right' },
      ],
    },
  }
};
