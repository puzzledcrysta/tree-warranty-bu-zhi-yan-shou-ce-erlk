export async function query(path, body) {
  const options = body === undefined ? {} : {
    method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify(body),
  };
  const response = await fetch(path, options);
  if (!response.ok) {
    const problem = await response.json();
    const error = Error(typeof problem.detail === 'string' ? problem.detail : '字段或文件有误');
    error.status = response.status;
    throw error;
  }
  return response.json();
}

export async function readInput(file) {
  if (file.size > 131072) throw Error('文件超出 128 KiB');
  const bytes = await file.arrayBuffer();
  try {
    return [new TextDecoder('utf-8', {fatal: true}).decode(bytes), bytes];
  } catch {
    try {
      return [new TextDecoder('gb18030', {fatal: true}).decode(bytes), bytes];
    } catch {
      throw Error('文件应使用 UTF-8 或 GB18030');
    }
  }
}

export function encodeInput(bytes) {
  const view = new Uint8Array(bytes);
  let binary = '';
  for (let index = 0; index < view.length; index += 8192) {
    binary += String.fromCharCode(...view.subarray(index, index + 8192));
  }
  return btoa(binary);
}
