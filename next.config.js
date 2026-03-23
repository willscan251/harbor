/** @type {import('next').NextConfig} */
const nextConfig = {
  // Support subdomain routing for portal vs staff
  async rewrites() {
    return {
      beforeFiles: [
        // portal.thescanlandgroup.com → /portal routes
        {
          source: '/:path*',
          has: [{ type: 'host', value: 'portal.thescanlandgroup.com' }],
          destination: '/portal/:path*',
        },
      ],
      afterFiles: [],
      fallback: [],
    }
  },
}

module.exports = nextConfig
