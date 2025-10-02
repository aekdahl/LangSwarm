module.exports = {
  onBrokenLinks: 'warn',
  title: 'LangSwarm Documentation',
  tagline: 'Build powerful multi-agent AI systems in 30 seconds, not hours',
  url: 'https://aekdahl.github.io',
  baseUrl: '/LangSwarm/',
  organizationName: 'aekdahl',
  projectName: 'LangSwarm',
  favicon: 'img/favicon.ico',
  
  presets: [
    [
      'classic',
      {
        docs: {
          routeBasePath: '/',
          path: './docs',
          sidebarPath: require.resolve('./sidebars.js'),
          editUrl: 'https://github.com/aekdahl/LangSwarm/edit/main/docs/',
          showLastUpdateAuthor: true,
          showLastUpdateTime: true,
          breadcrumbs: true,
        },
        theme: {
          customCss: require.resolve('./src/css/custom.css'),
        },
      },
    ],
  ],
  
  themeConfig: {
    // Enhanced navbar with better organization
    navbar: {
      title: 'LangSwarm',
      logo: {
        alt: 'LangSwarm Logo',
        src: 'img/logo.svg',
      },
      items: [
        {
          type: 'doc',
          docId: 'README',
          position: 'left',
          label: '🏠 Home',
        },
        {
          type: 'doc',
          docId: 'getting-started/quickstart/README',
          position: 'left',
          label: '⚡ Quick Start',
        },
        {
          type: 'dropdown',
          label: '📚 Guides',
          position: 'left',
          items: [
            {
              type: 'doc',
              docId: 'user-guides/configuration/README',
              label: 'Configuration',
            },
            {
              type: 'doc',
              docId: 'user-guides/agents/README',
              label: 'Agents',
            },
            {
              type: 'doc',
              docId: 'user-guides/workflows/README',
              label: 'Workflows',
            },
            {
              type: 'doc',
              docId: 'tools/README',
              label: 'Tools',
            },
          ],
        },
        {
          type: 'dropdown',
          label: '🔧 Developers',
          position: 'left',
          items: [
            {
              type: 'doc',
              docId: 'developer-guides/contributing/README',
              label: 'Contributing',
            },
            {
              type: 'doc',
              docId: 'api-reference/agents/README',
              label: 'API Reference',
            },
            {
              type: 'doc',
              docId: 'developer-guides/debugging/README',
              label: 'Debugging',
            },
          ],
        },
        {
          href: 'https://github.com/aekdahl/LangSwarm',
          label: 'GitHub',
          position: 'right',
        },
        {
          href: 'https://github.com/aekdahl/LangSwarm/issues',
          label: 'Support',
          position: 'right',
        },
      ],
    },
    
    // Footer with useful links
    footer: {
      style: 'dark',
      links: [
        {
          title: 'Getting Started',
          items: [
            {
              label: 'Quick Start',
              to: '/getting-started/quickstart/README',
            },
            {
              label: 'Installation',
              to: '/getting-started/installation/README',
            },
            {
              label: 'First Project',
              to: '/getting-started/first-project/README',
            },
          ],
        },
        {
          title: 'User Guides',
          items: [
            {
              label: 'Configuration',
              to: '/user-guides/configuration/README',
            },
            {
              label: 'Agents',
              to: '/user-guides/agents/README',
            },
            {
              label: 'Tools',
              to: '/tools/README',
            },
          ],
        },
        {
          title: 'Community',
          items: [
            {
              label: 'GitHub',
              href: 'https://github.com/aekdahl/LangSwarm',
            },
            {
              label: 'Issues',
              href: 'https://github.com/aekdahl/LangSwarm/issues',
            },
            {
              label: 'Discussions',
              href: 'https://github.com/aekdahl/LangSwarm/discussions',
            },
          ],
        },
      ],
      copyright: `Copyright © ${new Date().getFullYear()} LangSwarm. Built with Docusaurus.`,
    },
    
    // Search functionality
    algolia: {
      appId: 'YOUR_APP_ID',
      apiKey: 'YOUR_SEARCH_API_KEY',
      indexName: 'langswarm',
      contextualSearch: true,
      searchParameters: {},
      searchPagePath: 'search',
    },
    
    // Color mode
    colorMode: {
      defaultMode: 'light',
      disableSwitch: false,
      respectPrefersColorScheme: true,
    },
    
    // Table of contents
    tableOfContents: {
      minHeadingLevel: 2,
      maxHeadingLevel: 4,
    },
  },
  
  // Plugins for enhanced functionality
  plugins: [
    [
      '@docusaurus/plugin-content-docs',
      {
        id: 'community',
        path: 'community',
        routeBasePath: 'community',
        sidebarPath: require.resolve('./sidebars.js'),
      },
    ],
  ],
};
