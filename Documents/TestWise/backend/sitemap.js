const { SitemapStream, streamToPromise } = require('sitemap');
const { Readable } = require('stream');

// Define all public pages
const pages = [
  { url: '/', changefreq: 'daily', priority: 1.0 },
  { url: '/features', changefreq: 'weekly', priority: 0.9 },
  { url: '/contact', changefreq: 'monthly', priority: 0.7 },
  { url: '/privacy', changefreq: 'monthly', priority: 0.5 },
  { url: '/voorwaarden', changefreq: 'monthly', priority: 0.5 },
  { url: '/login', changefreq: 'weekly', priority: 0.8 },
  { url: '/registreer', changefreq: 'weekly', priority: 0.8 },
];

async function generateSitemap() {
  const hostname = 'https://testwise.nl';

  // Create a stream to write to
  const stream = new SitemapStream({ hostname });

  // Return a promise that resolves with the XML string
  return streamToPromise(Readable.from(pages).pipe(stream))
    .then((data) => data.toString());
}

module.exports = { generateSitemap };
