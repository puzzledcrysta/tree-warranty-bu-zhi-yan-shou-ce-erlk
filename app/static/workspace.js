import {query, readInput, encodeInput} from './api.js';
import {el, evidence, table} from './table.js';

const byId = id => document.getElementById(id);
const settings = JSON.parse(byId('settings').textContent);
const links = [...document.querySelectorAll('[data-module]')];
const body = byId('grid-data');
const alert = byId('notice');
const live = byId('state');
const action = document.querySelector('#source button[type=submit]');
const topExport = byId('export');
let selected = Object.hasOwn(settings.tabs, location.hash.slice(1)) ? location.hash.slice(1) : 'domain';
let result = null;
let inputs = {};
let reviewVersion = 0;
let adoptionNote = '';
let renderEpoch = 0;
let activeView = null;
const filter = byId('filter');
const differences = byId('differences');

function filterTable() {
  if (!activeView) return;
  const {columns, rows, stage} = activeView;
  const query = filter.value.trim().toLocaleLowerCase();
  const selected = rows.filter(row => {
    if (stage === 'reconcile' && differences.checked && row.code === 'MATCH') return false;
    return !query || [row.key,row.id,row.line,row.code,settings.reasons[row.code],row.detail,row.note,row.kind]
      .some(value => String(value ?? '').toLocaleLowerCase().includes(query));
  });
  byId('shown').textContent = `${selected.length} / ${rows.length}`;
  table(body, columns, selected);
}
filter.addEventListener('input', filterTable);
differences.addEventListener('change', filterTable);
const uploaded = new Map();

function notice(message, error = false) {
  alert.value = message;
  alert.classList.toggle('problem', error);
}

function tag(code) {
  return el('span', settings.reasons[code] || code, code === 'MATCH' ? 'state' : 'state problem');
}

function adoptControl(row) {
  // Only a same-revision conflict offers a source to trust; suppressed rows
  // and business rejections stay read-only.
  if (row.code !== 'REV_CONFLICT' || !result) return el('span', '—', 'empty');
  const cell = el('div');
  const note = el('input');
  note.type = 'text';
  note.maxLength = 500;
  note.placeholder = '复核意见';
  note.value = adoptionNote;
  note.addEventListener('input', () => { adoptionNote = note.value; });
  const button = el('button', '采信此份', 'btn');
  button.type = 'button';
  button.addEventListener('click', async () => {
    if (!note.value.trim()) {
      notice('采信原始底单须先填写复核意见', true);
      note.focus();
      return;
    }
    button.disabled = true;
    try {
      const reply = await query(`/api/adjudicate/${result.manifest.run_id}`, {
        key: row.key, revision: row.revision, line: row.line, digest: row.digest, note: note.value,
      });
      adoptionNote = '';
      setRun(reply.report);
      notice(`已采信第 ${row.line} 行原始底单，复算合格株数已更新`);
      await render();
    } catch (error) {
      notice(error.message, true);
      await render();
    } finally { button.disabled = false; }
  });
  cell.append(note, button);
  return cell;
}


function showEvidence(row) {
  const panel = byId('evidence-panel');
  const record = byId('evidence-key');
  const details = byId('signal');
  if (!row) {
    record.textContent = '';
    details.replaceChildren(el('p', '本批没有可采信记录', 'empty'));
    return;
  }
  record.textContent = row.key;
  const content = el('ol', undefined, panel.dataset.instrument);
  for (const item of row.proof) {
    const line = el('li');
    line.append(el('span', item.metric));
    line.append(el('strong', item.unit ? `${item.value} ${item.unit}` : item.value, 'measure'));
    content.append(line);
  }
  details.replaceChildren(content);
}

function inspect(row) {
  const button = el('button', '查看依据', 'btn');
  button.type = 'button';
  button.addEventListener('click', () => showEvidence(row));
  const raw = evidence('原始字段', row.raw);
  const cell = el('div');
  cell.append(button, raw);
  return cell;
}

function setRun(report) {
  result = report;
  byId('created').textContent = `${report.manifest.created.slice(0, 19).replace('T', ' ')} UTC`;
  showEvidence(report.accepted[0]);
  const id = result.manifest.run_id;
  byId('run-id').textContent = id.slice(0, 9);
  byId('run-id').title = id;
  topExport.hidden = false;
  topExport.href = `/api/export/${id}`;
  const values = {...result.counts, delta: result.book.delta, mismatched: result.book.mismatched};
  for (const cell of document.querySelectorAll('[data-count]')) cell.textContent = values[cell.dataset.count];
  live.textContent = `批次 ${id.slice(0, 9)} · ${result.balanced ? '记录已对齐' : '记录数不符'}`;
}

async function render() {
  const ticket = ++renderEpoch;
  const stage = selected;
  byId('phase').textContent = settings.tabs[stage];
  byId('review').hidden = true;
  for (const link of links) {
    if (link.dataset.module === stage) link.setAttribute('aria-current', 'page');
    else link.removeAttribute('aria-current');
  }
  if (!result) return;
  const id = result.manifest.run_id;
  const raw = row => evidence('来源字段', row.raw);
  const key = [settings.key, 'key'];
  const line = ['行号', 'line', 'num'];
  try {
    let view, rows;
    if (stage === 'domain') {
      view = [key, [`应付养护款 · ${settings.unit}`, 'amount', 'num'], line, ['明细依据', inspect]];
      rows = result.accepted;
    } else if (stage === 'quality') {
      view = [key, line, ['判定', row => tag(row.code)], ['说明', 'detail'], ['字段', raw], ['采信', adoptControl]];
      rows = [...result.quarantine, ...result.suppressed].sort((a,b) => a.line-b.line);
    } else if (stage === 'reconcile') {
      view = [key, ['实际', 'amount', 'num'], ['外部账', 'reference', 'num'], ['差值', 'delta', 'num'], ['外部行', 'book_line', 'num'], ['结论', row => tag(row.code)]];
      rows = [...result.book.rows].sort((a,b) => Number(a.code === 'MATCH') - Number(b.code === 'MATCH'));
    } else if (stage === 'intake') {
      const intake = await query('/api/intake', inputs);
      view = [line, ['分类', 'kind'], ['字段', raw]];
      rows = [...intake.rows.map(row => ({...row,kind:'完整记录'})), ...intake.rejected.map(row => ({...row,kind:'坏行'})),
              ...intake.blank_lines.map(line => ({line,kind:'空白行',raw:[]})),
              ...intake.header_lines.map(line => ({line,kind:'重复表头',raw:[]}))].sort((a,b) => a.line-b.line);
    } else if (stage === 'contract') {
      const contract = await query('/api/contract', inputs);
      view = [key, line, ['修订', 'revision', 'num'], ['来源时刻 UTC', 'time'], ['字段', row => evidence('归一值', Object.entries(row.fields).map(([k,v]) => `${k} · ${v}`))]];
      rows = contract.accepted;
    } else if (stage === 'runs') {
      const runs = await query('/api/runs');
      view = [['指纹','id'], ['创建 UTC','created'], ['操作', row => {
        const current = row.id === id;
        const button = el('button',current ? '复算当前批' : '打开此批','btn');
        button.addEventListener('click', async () => {
          button.disabled = true;
          try {
            if (current) {
              setRun(await query(`/api/runs/${id}/replay`, {}));
              notice('复算已核对');
            } else {
              const [past, original] = await Promise.all([
                query(`/api/runs/${row.id}`), query(`/api/runs/${row.id}/source`),
              ]);
              inputs = original;
              setRun(past);
              notice('已打开历史批次');
              await render();
            }
          }
          catch (error) { notice(error.message, true); }
          finally { button.disabled = false; }
        });
        return button;
      }]];
      rows = runs;
    } else {
      const timeline = await query(`/api/review/${id}`);
      view = [['版本','version','num'], ['结论','decision'], ['对象','key'], ['底单行', row => row.line ? `${row.line} 行 · 修订 ${row.revision}` : '—'],
              ['复核意见','note'], ['登记 UTC','changed']];
      rows = timeline;
      if (ticket === renderEpoch) {
        reviewVersion = timeline[0]?.version || 0;
        byId('review').hidden = false;
      }
    }
    if (ticket === renderEpoch) {
      if (activeView?.stage !== stage) filter.value = '';
      activeView = {stage, columns: view, rows};
      byId('tools').hidden = false;
      byId('only-differences').hidden = stage !== 'reconcile';
      filterTable();
    }
  } catch (error) {
    if (ticket === renderEpoch) notice(error.message, true);
  }
}

window.addEventListener('hashchange', () => {
  selected = Object.hasOwn(settings.tabs, location.hash.slice(1)) ? location.hash.slice(1) : 'domain';
  render();
});
byId('sample').addEventListener('click', async () => {
  const paths = ['shift', 'external'];
  try {
    const responses = await Promise.all(paths.map(name => fetch(`/api/samples/${name}`)));
    if (responses.some(item => !item.ok)) throw Error('样例暂时不可用');
    const files = await Promise.all(responses.map(item => item.arrayBuffer()));
    for (const [index,name] of ['source','book'].entries()) {
      const decoded = new TextDecoder('utf-8').decode(files[index]);
      byId(`${name}-csv`).value = decoded;
      uploaded.set(name,{text:byId(`${name}-csv`).value,bytes:files[index]});
    }
    byId('source-file').value = '';
    byId('book-file').value = '';
    document.querySelector('#source details').open = true;
    notice('样例已载入');
  } catch (error) { notice(error.message, true); }
});
for (const name of ['source','book']) {
  byId(`${name}-file`).addEventListener('change', async event => {
    const file = event.target.files[0];
    if (!file) return;
    action.disabled = true;
    try {
      const [text,bytes] = await readInput(file);
      byId(`${name}-csv`).value = text;
      uploaded.set(name,{text:byId(`${name}-csv`).value,bytes});
      notice(`已读取 ${file.name}`);
    } catch (error) {
      event.target.value = '';
      notice(error.message, true);
    } finally { action.disabled = false; }
  });
}
byId('source').addEventListener('submit', async event => {
  event.preventDefault();
  const candidate = {};
  for (const [control,name] of [['source','data'],['book','book']]) {
    const text = byId(`${control}-csv`).value;
    const original = uploaded.get(control);
    if (original && text === original.text) candidate[`${name}_base64`] = encodeInput(original.bytes);
    else if (text.length || original) candidate[name] = text;
  }
  action.disabled = true;
  ++renderEpoch;
  notice('计算中');
  try {
    const report = await query('/api/runs', candidate);
    inputs = candidate;
    setRun(report);
    notice('批次已计算');
    await render();
  } catch (error) { notice(error.message, true); }
  finally { action.disabled = false; }
});
byId('review').addEventListener('submit', async event => {
  event.preventDefault();
  const id = result.manifest.run_id;
  const note = byId('review-note');
  try {
    await query(`/api/review/${id}`, {version: reviewVersion, decision: byId('decision').value, note: note.value});
    notice('复核已登记');
    note.value = '';
    await render();
  } catch (error) {
    notice(error.message, true);
    if (error.status === 409) await render();
  }
});
render();
