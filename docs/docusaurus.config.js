// @ts-check
// Note: type annotations allow type checking and IDEs autocompletion

const {themes} = require('prism-react-renderer');
const lightTheme = themes.github;
const darkTheme = themes.dracula;

/** @type {import('@docusaurus/types').Config} */
const config = {
  title: 'SentinelIQ Documentation',
  tagline: 'Enterprise-grade Security Platform',
  favicon: 'img/favicon.ico',

  // Set the production url of your site here
  url: 'https://sentineliq.com',
  // Set the /<baseUrl>/ pathname under which your site is served
  // For GitHub pages deployment, it is often '/<projectName>/'
  baseUrl: '/docs/',

  // GitHub pages deployment config.
  // If you aren't using GitHub pages, you don't need these.
  organizationName: 'sentineliq', // Usually your GitHub org/user name.
  projectName: 'sentineliq', // Usually your repo name.

  onBrokenLinks: 'throw',
  onBrokenMarkdownLinks: 'warn',

  // Even if you don't use internalization, you can use this field to set useful
  // metadata like html lang. For example, if your site is Chinese, you may want
  // to replace "en" with "zh-Hans".
  i18n: {
    defaultLocale: 'en',
    locales: ['en'],
  },

  presets: [
    [
      'classic',
      /** @type {import('@docusaurus/preset-classic').Options} */
      ({
        docs: {
          sidebarPath: require.resolve('./sidebars.js'),
          routeBasePath: '/',
          // Please change this to your repo.
          // Remove this to remove the "edit this page" links.
          editUrl:
            'https://github.com/sentineliq/sentineliq/tree/main/docs/',
        },
        blog: false,
        theme: {
          customCss: require.resolve('./src/css/custom.css'),
        },
      }),
    ],
  ],

  themeConfig:
    /** @type {import('@docusaurus/preset-classic').ThemeConfig} */
    ({
      // Replace with your project's social card
      image: 'img/sentineliq-social-card.jpg',
      navbar: {
        title: 'SentinelIQ',
        logo: {
          alt: 'SentinelIQ Logo',
          src: 'img/logo/light.svg',
          srcDark: 'img/logo/dark.svg',
        },
        items: [
          {
            type: 'docSidebar',
            sidebarId: 'sentinelIQSidebar',
            position: 'left',
            label: 'Docs',
          },
          {
            href: 'https://github.com/sentineliq/sentineliq',
            label: 'GitHub',
            position: 'right',
          },
        ],
      },
      footer: {
        style: 'dark',
        links: [
          {
            title: 'Docs',
            items: [
              {
                label: 'Introduction',
                to: '/',
              },
              {
                label: 'Features',
                to: '/features',
              },
              {
                label: 'API Reference',
                to: '/reference/api-core',
              },
            ],
          },
          {
            title: 'Community',
            items: [
              {
                label: 'Stack Overflow',
                href: 'https://stackoverflow.com/questions/tagged/sentineliq',
              },
              {
                label: 'Discord',
                href: 'https://discord.gg/sentineliq',
              },
              {
                label: 'Twitter',
                href: 'https://twitter.com/sentineliq',
              },
            ],
          },
          {
            title: 'More',
            items: [
              {
                label: 'GitHub',
                href: 'https://github.com/sentineliq/sentineliq',
              },
            ],
          },
        ],
        copyright: `Copyright © ${new Date().getFullYear()} SentinelIQ. Built with Docusaurus.`,
      },
      prism: {
        theme: lightTheme,
        darkTheme: darkTheme,
      },
      colorMode: {
        defaultMode: 'dark',
        disableSwitch: false,
        respectPrefersColorScheme: true,
      },
      metadata: [
        {name: 'keywords', content: 'sentineliq, security, api, django, rest, framework, enterprise'},
      ],
    }),
};

module.exports = config; 