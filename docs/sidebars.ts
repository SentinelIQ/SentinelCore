import type {SidebarsConfig} from '@docusaurus/plugin-content-docs';

// This runs in Node.js - Don't use client-side code here (browser APIs, JSX...)

/**
 * Creating a sidebar enables you to:
 - create an ordered group of docs
 - render a sidebar for each doc of that group
 - provide next/previous navigation

 The sidebars can be generated from the filesystem, or explicitly defined here.

 Create as many sidebars as you want.
 */
const sidebars: SidebarsConfig = {
  sentinelIQSidebar: [
    {
      type: 'doc',
      id: 'index',
      label: 'Introduction',
    },
    {
      type: 'doc',
      id: 'features',
      label: 'Features Overview',
    },
    {
      type: 'category',
      label: 'Learn',
      items: [
        'learn/index',
        'learn/django-drf-fundamentals',
      ],
    },
    {
      type: 'category',
      label: 'Tutorial',
      items: [
        'tutorial/intro',
        'tutorial/modular-architecture',
        'tutorial/core-components',
        'tutorial/response-handling',
        'tutorial/rbac-basics',
        'tutorial/error-handling',
        'tutorial/audit-logging',
      ],
    },
    {
      type: 'category',
      label: 'Dependencies & Setup',
      items: [
        'dependencies/poetry',
        'dependencies/docker',
        'dependencies/project-structure',
      ],
    },
    {
      type: 'category',
      label: 'Advanced Security',
      items: [
        'advanced/rbac-advanced',
      ],
    },
    {
      type: 'category',
      label: 'How-To Guides',
      items: [
        'how-to/creating-apps',
      ],
    },
    {
      type: 'category',
      label: 'API Reference',
      items: [
        'reference/api-core',
        'reference/audit-logs',
        'reference/response-format',
      ],
    },
    {
      type: 'doc',
      id: 'release-notes',
      label: 'Release Notes',
    },
  ],
};

export default sidebars;
