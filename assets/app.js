// Keep bookmarked Docsify URLs such as /#/CrowdStrike/CQL/01-how-to-build-cql-queries.md working.
function redirectOldLink() {
  if (!location.hash.startsWith('#/')) return;
  const [raw, query = ''] = location.hash.slice(2).split('?');
  let route;
  try { route = decodeURIComponent(raw); } catch (_) { return; }
  const routes = JSON.parse(document.querySelector('#legacy-routes').textContent);
  const destination = routes[route] || routes[route + '.md'] || (route === 'README.md' ? routes['About/profile.md'] : null);
  if (destination) {
    const id = new URLSearchParams(query).get('id');
    location.replace(destination + (id ? '#' + encodeURIComponent(id) : ''));
  }
}
redirectOldLink();
window.addEventListener('hashchange', redirectOldLink);
const buttons = [...document.querySelectorAll('.folder')];
const cards = [...document.querySelectorAll('.card')];
const search = document.querySelector('#search');
let selected = '';
function filter() {
  let count = 0;
  const query = search.value.trim().toLowerCase();
  cards.forEach(card => {
    const visible = (!selected || card.dataset.folder === selected) && card.dataset.search.includes(query);
    card.hidden = !visible;
    if (visible) count++;
  });
  document.querySelector('#folder-title').textContent = selected || 'All notes';
  document.querySelector('#result-count').textContent = `${count} ${count === 1 ? 'note' : 'notes'} ${query ? 'found' : 'in your library'}`;
  document.querySelector('#empty').hidden = count > 0;
  buttons.forEach(button => {
    const active = button.dataset.folder === selected;
    button.classList.toggle('active', active);
    button.setAttribute('aria-pressed', String(active));
  });
}
buttons.forEach(button => button.addEventListener('click', () => {
  selected = button.dataset.folder;
  filter();
}));
search.addEventListener('input', filter);
filter();
