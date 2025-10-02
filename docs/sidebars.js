module.exports = {
  docs: [
    // Quick Start Section
    {
      type: 'category',
      label: '🚀 Getting Started',
      collapsed: false,
      items: [
        'README',
        {
          type: 'category',
          label: 'Quick Setup',
          items: [
            'getting-started/installation/README',
            'getting-started/quickstart/README',
            'getting-started/first-project/README',
          ],
        },
      ],
    },

    // User Guides - Most Important Section
    {
      type: 'category',
      label: '📚 User Guides',
      collapsed: false,
      items: [
        {
          type: 'category',
          label: 'Configuration',
          items: [
            'user-guides/configuration/README',
            'user-guides/configuration/single-file',
            'user-guides/configuration/multi-file',
            'user-guides/configuration/environment-detection',
          ],
        },
        {
          type: 'category',
          label: 'Agents',
          items: [
            'user-guides/agents/README',
            'user-guides/agents/response-modes',
            'user-guides/agents/workflows-vs-agents',
            'user-guides/agents/providers',
          ],
        },
        {
          type: 'category',
          label: 'Workflows',
          items: [
            'user-guides/workflows/README',
            'user-guides/workflows/yaml-compatibility/README',
          ],
        },
        {
          type: 'category',
          label: 'Tools',
          items: [
            'user-guides/tools/intent-based-calls',
            'user-guides/tools/tool-chaining',
            'user-guides/tools/mcp/README',
          ],
        },
        {
          type: 'category',
          label: 'Memory & Sessions',
          items: [
            'user-guides/memory/README',
            'user-guides/sessions/README',
            'user-guides/vector-stores/README',
          ],
        },
        'user-guides/token-tracking-integration-guide',
        'user-guides/observability/README',
      ],
    },

    // Tools Documentation
    {
      type: 'category',
      label: '🛠️ Tools',
      collapsed: true,
      items: [
        'tools/README',
        {
          type: 'category',
          label: 'MCP Tools',
          items: [
            'tools/mcp/overview/README',
            'tools/mcp/development/README',
            'tools/mcp/examples/README',
            'tools/mcp/migration/README',
          ],
        },
        'tools/builtin/README',
        'tools/development/README',
        'tools/unified-system/README',
      ],
    },

    // Examples & Tutorials
    {
      type: 'category',
      label: '💡 Examples',
      collapsed: true,
      items: [
        'examples/tutorials/README',
        'examples/use-cases/README',
        'examples/templates/README',
        'examples/best-practices/README',
        'examples/configuration/README',
        'examples/sessions/README',
        'examples/vector-stores/README',
      ],
    },

    // Developer Resources
    {
      type: 'category',
      label: '🔧 Developer Guides',
      collapsed: true,
      items: [
        'developer-guides/contributing/README',
        'developer-guides/architecture/README',
        'developer-guides/testing/README',
        {
          type: 'category',
          label: 'Debugging',
          items: [
            'developer-guides/debugging/README',
            'developer-guides/debugging/quick-start/README',
            'developer-guides/debugging/configuration/setup',
            'developer-guides/debugging/test-cases/bigquery-tool',
            'developer-guides/debugging/tracing-system/README',
          ],
        },
        {
          type: 'category',
          label: 'Extending LangSwarm',
          items: [
            'developer-guides/extending/agent-providers/README',
            'developer-guides/extending/configuration/README',
            'developer-guides/extending/error-system/README',
            'developer-guides/extending/sessions/README',
            'developer-guides/extending/tool-adapters/README',
            'developer-guides/extending/tool-development/README',
            'developer-guides/extending/vector-stores/README',
            'developer-guides/extending/workflow-patterns/README',
          ],
        },
        'developer-guides/monitoring/README',
        'developer-guides/observability/README',
      ],
    },

    // API Reference
    {
      type: 'category',
      label: '📖 API Reference',
      collapsed: true,
      items: [
        'api-reference/agents/README',
        'api-reference/configuration/README',
        'api-reference/core/errors/README',
        'api-reference/memory/README',
        'api-reference/observability/README',
        'api-reference/sessions/README',
        'api-reference/vector-stores/README',
        'api-reference/workflows/README',
      ],
    },

    // Architecture
    {
      type: 'category',
      label: '🏗️ Architecture',
      collapsed: true,
      items: [
        'architecture/dual-interface-architecture',
        'architecture/enhanced-pipeline-factory',
        'architecture/unified-pipeline-system',
      ],
    },

    // Deployment
    {
      type: 'category',
      label: '🚀 Deployment',
      collapsed: true,
      items: [
        'deployment/local/README',
        'deployment/cloud/README',
        'deployment/enterprise/README',
        'deployment/scaling/README',
      ],
    },

    // Migration & Troubleshooting
    {
      type: 'category',
      label: '🔄 Migration',
      collapsed: true,
      items: [
        {
          type: 'category',
          label: 'V1 to V2 Migration',
          items: [
            'migration/v1-to-v2/agent-migration/README',
            'migration/v1-to-v2/configuration/README',
            'migration/v1-to-v2/error-migration/README',
            'migration/v1-to-v2/memory-migration/README',
            'migration/v1-to-v2/sessions/README',
            'migration/v1-to-v2/tool-migration/README',
            'migration/v1-to-v2/workflow-migration/README',
          ],
        },
        'migration/dependency-cleanup/README',
      ],
    },

    {
      type: 'category',
      label: '🔍 Troubleshooting',
      collapsed: true,
      items: [
        'troubleshooting/common-issues/README',
        'troubleshooting/debugging/README',
        'troubleshooting/error-handling/README',
        'troubleshooting/faq/README',
        'troubleshooting/performance/README',
      ],
    },

    // Specialized Topics
    {
      type: 'category',
      label: '📋 Reference',
      collapsed: true,
      items: [
        'features/token-tracking-overview',
        'features/token-tracking-system',
        'mcp/standard-protocol-implementation',
        'mcp/intent-based-mcp-extension',
        'observability/debug-implementation-plan',
        'observability/debug-tracing-specification',
        'security/MOCK_AUDIT_REPORT',
      ],
    },

    // Community & Support
    {
      type: 'category',
      label: '🤝 Community',
      collapsed: true,
      items: [
        'community/contributing/README',
        'community/roadmap/README',
        'community/changelog/README',
        'community/support/README',
      ],
    },
  ],
};
