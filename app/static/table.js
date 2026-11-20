export function el(tag, text, className) {
  const node = document.createElement(tag);
  if (text !== undefined && text !== null) node.textContent = text;
  if (className) node.className = className;
  return node;
}

export function evidence(title, items) {
  const root = el('details');
  root.append(el('summary', title));
  const list = el('ul');
  items.filter(item => item !== '').forEach(item => list.append(el('li', item)));
  root.append(list);
  return root;
}

export function table(target, columns, rows) {
  if (!rows.length) {
    target.replaceChildren(el('p', '当前没有记录', 'empty'));
    return;
  }
  const root = el('table');
  const top = el('tr');
  for (const [label, , mode] of columns) {
    const title = el('th', label, mode);
    title.scope = 'col';
    top.append(title);
  }
  const head = el('thead');
  head.append(top);
  const body = el('tbody');
  for (const data of rows) {
    const row = el('tr');
    for (const [, get, mode] of columns) {
      const value = typeof get === 'string' ? data[get] : get(data);
      const node = el('td', undefined, mode);
      if (value instanceof Node) node.append(value);
      else node.textContent = value === null || value === undefined || value === '' ? '—' : value;
      row.append(node);
    }
    body.append(row);
  }
  root.append(head, body);
  target.replaceChildren(root);
}
