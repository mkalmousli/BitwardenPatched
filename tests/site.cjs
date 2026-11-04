// Run after generating work/local-site. Uses installed Chromium and Playwright.
const assert = require('node:assert/strict');
const fs = require('node:fs/promises');
const http = require('node:http');
const path = require('node:path');
const {chromium} = require('playwright');
const root = path.resolve(__dirname, '../work/local-site');
const types = {'.js': 'text/javascript', '.json': 'application/json', '.css': 'text/css'};
const server = http.createServer(async (req, res) => {
  const file = path.resolve(root, '.' + new URL(req.url, 'http://localhost').pathname);
  if (!file.startsWith(root + '/') && file !== root) return res.writeHead(403).end();
  const target = file === root ? path.join(root, 'index.html') : file;
  try {
    res.setHeader('Content-Type', types[path.extname(target)] || 'text/html');
    res.end(await fs.readFile(target));
  } catch { res.writeHead(404).end(); }
});

(async () => {
  await new Promise(resolve => server.listen(0, '127.0.0.1', resolve));
  const browser = await chromium.launch({
    executablePath: process.env.CHROMIUM_PATH || '/usr/bin/chromium',
    headless: true, args: ['--no-sandbox']
  });
  try {
    for (const mode of ['api-unavailable', 'api-pending', 'missing-targets', 'metadata-unavailable']) {
      const page = await browser.newPage();
      const errors = [];
      page.on('pageerror', error => errors.push(error.message));
      await page.route('https://api.github.com/**', route => mode === 'api-pending'
        ? undefined : route.fulfill({status: 403, body: '{}'}));
      if (mode === 'missing-targets') await page.route('**/data/versions.json', route =>
        route.fulfill({json: {android: [], desktop: []}}));
      if (mode === 'metadata-unavailable') await page.route('**/data/versions.json', route =>
        route.fulfill({status: 404, body: 'not found'}));
      await page.goto(`http://127.0.0.1:${server.address().port}/`, {waitUntil: 'domcontentloaded'});
      if (mode.startsWith('api-')) {
        await page.locator('#dl details').first().waitFor();
        assert(await page.locator('#dl details').count() > 0);
        const links = await page.locator('#dl table a').evaluateAll(as => as.map(a => a.href));
        assert(links.length > 0 && links.every(url => url.includes('github.com/') && url.includes('/releases/download/')));
        assert.equal(await page.locator('symbol#icon-dl').count(), 1);
        await page.getByRole('tab', {name: 'Linux', exact: true}).click();
      } else if (mode === 'missing-targets') {
        await page.getByText('No releases yet.', {exact: true}).waitFor();
      } else {
        await page.locator('#dl a').waitFor();
        assert((await page.locator('#dl a').getAttribute('href')).endsWith('/releases'));
      }
      assert.deepEqual(errors, []);
      await page.close();
      console.log(`PASS ${mode}`);
    }
  } finally { await browser.close(); server.close(); }
})().catch(error => { console.error(error); server.close(); process.exitCode = 1; });
