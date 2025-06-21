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
  docsSidebar: [
    'intro',
    'getting-started',
    'installation',
    'quick-start',
    {
      type: 'category',
      label: 'Connection Types',
      items: [
        'connections/overview',
        'connections/websocket',
        'connections/http',
        'connections/async-vs-sync',
      ],
    },
    {
      type: 'category',
      label: 'Core Methods',
      items: [
        'methods/overview',
        'methods/authentication',
      ],
    },
    {
      type: 'category',
      label: 'Data Types',
      items: [
        'data-types/index',
        'data-types/overview',
        'data-types/record-id',
      ],
    },
    {
      type: 'category',
      label: 'Examples',
      items: [
        'examples/basic-crud',
        'examples/data-types-examples',
        'examples/data-types-examples-part2',
        'examples/data-types-examples-part3',
        'examples/data-types-examples-part4',
        'examples/data-types-comprehensive-guide',
        'examples/pydantic-surrealdb-guide',
        {
          type: 'category',
          label: 'FastAPI Authentication',
          items: [
            'examples/fastapi-auth/index',
            'examples/fastapi-auth/auth-routes',
            'examples/fastapi-auth/user-crud',
            'examples/fastapi-auth/profile-management',
            'examples/fastapi-auth/advanced-queries',
            'examples/fastapi-auth/realtime',
            'examples/fastapi-auth/testing',
          ],
        },
      ],
    },
    {
      type: 'category',
      label: 'Authentication',
      items: [
        'authentication/overview',
        'authentication/basic-auth',
        'authentication/jwt-auth',
        'authentication/auth0',
        'authentication/github-sso',
        'authentication/custom-scopes',
      ],
    },
    {
      type: 'category',
      label: 'API Reference',
      items: [
        'api/connections',
      ],
    },
    'troubleshooting',
    'contributing',
  ],
};

export default sidebars;
