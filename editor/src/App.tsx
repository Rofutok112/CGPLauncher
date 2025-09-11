
import React, { useEffect, useState } from 'react';

type Game = {
  name: string;
  version: string;
  authors: string[];
  tags: string[];
  url: string;
  unityroomurl: string;
  githuburl: string;
  buildFile: string;
  description: string;
  image: string;
  markdown: string;
};

function isValidUrl(url: string) {
  if (!url) return false;
  try {
    new URL(url);
    return true;
  } catch {
    return false;
  }
}

function checkRequiredUrls(game: Game) {
  // 画像、MD以外のダウンロード、UnityRoom、GitHubの3つのURLのうち1つが必須
  const hasImage = !!game.image;
  const hasMd = game.markdown && game.markdown.endsWith('.md');
  const hasDownload = game.url && !game.url.endsWith('.md') && isValidUrl(game.url);
  const hasUnityRoom = game.unityroomurl && isValidUrl(game.unityroomurl) && game.unityroomurl.includes('unityroom.com');
  const hasGitHub = game.githuburl && isValidUrl(game.githuburl) && game.githuburl.includes('github.com');
  return hasImage || hasDownload || hasUnityRoom || hasGitHub;
}

const urlFields = [
  { key: 'url', label: 'ダウンロードURL' },
  { key: 'unityroomurl', label: 'UnityRoom URL' },
  { key: 'githuburl', label: 'GitHub URL' },
  { key: 'image', label: '画像URL' },
  { key: 'markdown', label: 'Markdown/説明URL' },
];

const LOCAL_STORAGE_KEY = 'games_json_edit';

const App: React.FC = () => {
  const [games, setGames] = useState<Game[]>([]);
  const [error, setError] = useState<string>('');
  const [success, setSuccess] = useState<string>('');
  const [open, setOpen] = useState<boolean[]>([]); // 折り畳み状態

  useEffect(() => {
    // まずlocalStorageから、なければpublic/games.jsonから
    const local = localStorage.getItem(LOCAL_STORAGE_KEY);
    if (local) {
      const arr = JSON.parse(local);
      setGames(arr);
      setOpen(arr.map(() => false));
    } else {
      fetch('games.json')
        .then(res => res.json())
        .then(arr => {
          setGames(arr);
          setOpen(arr.map(() => false));
        })
        .catch(() => setError('games.jsonの読み込みに失敗しました'));
    }
  }, []);

  const handleChange = (idx: number, key: keyof Game, value: string) => {
    setGames(games => {
      const newGames = [...games];
      if (key === 'authors' || key === 'tags') {
        (newGames[idx][key] as any) = value.split(',').map(s => s.trim());
      } else {
        (newGames[idx][key] as any) = value;
      }
      return newGames;
    });
  };

  const handleAdd = () => {
    const empty: Game = {
      name: '',
      version: '',
      authors: [''],
      tags: [''],
      url: '',
      unityroomurl: '',
      githuburl: '',
      buildFile: '',
      description: '',
      image: '',
      markdown: ''
    };
    setGames(games => [...games, empty]);
    setOpen(open => [...open, true]);
  };

  const handleToggle = (idx: number) => {
    setOpen(open => open.map((v, i) => i === idx ? !v : v));
  };

  const handleSave = () => {
    // バリデーション
    for (const [i, g] of games.entries()) {
      if (!checkRequiredUrls(g)) {
        setError(`${i+1}番目のゲームで必須URLが不足しています`);
        setSuccess('');
        return;
      }
      for (const field of urlFields) {
        if (g[field.key as keyof Game] && !isValidUrl(g[field.key as keyof Game] as string) && field.key !== 'markdown' && field.key !== 'image') {
          setError(`${i+1}番目の${field.label}が不正なURLです`);
          setSuccess('');
          return;
        }
      }
    }
    localStorage.setItem(LOCAL_STORAGE_KEY, JSON.stringify(games, null, 2));
    setSuccess('保存しました (localStorage)');
    setError('');
  };

  return (
    <div style={{ maxWidth: 900, margin: '0 auto', fontFamily: 'sans-serif', background: '#111', color: '#fff', minHeight: '100vh', paddingBottom: 40 }}>
      <h2 style={{ color: '#fff' }}>games.json 編集ツール</h2>
      {error && <div style={{ color: '#ff6666' }}>{error}</div>}
      {success && <div style={{ color: '#66ff66' }}>{success}</div>}
      <div style={{ fontSize: 13, color: '#bbb' }}>※編集内容はlocalStorageに保存されます。必要に応じて手動でgames.jsonにコピーしてください。</div>
      <hr style={{ borderColor: '#333' }} />
      <button onClick={handleAdd} style={{ fontSize: 16, padding: '4px 16px', marginBottom: 16, background: '#222', color: '#fff', border: '1px solid #444', borderRadius: 4 }}>＋ゲーム追加</button>
      {games.map((game, idx) => (
        <div key={idx} style={{ border: '1px solid #333', borderRadius: 8, padding: 8, marginBottom: 12, background: '#222' }}>
          <div style={{ display: 'flex', alignItems: 'center', cursor: 'pointer' }} onClick={() => handleToggle(idx)}>
            <span style={{ fontWeight: 'bold', fontSize: 16, color: '#fff' }}>{game.name || '(タイトル未入力)'}</span>
            <span style={{ marginLeft: 8, color: '#aaa', fontSize: 13 }}>{open[idx] ? '▼' : '▶'}</span>
            <span style={{ marginLeft: 16, fontSize: 12, color: '#888' }}>（クリックで展開/折り畳み）</span>
          </div>
          {open[idx] && (
            <div style={{ marginTop: 8 }}>
              <div><b>タイトル</b>: <input value={game.name} onChange={e => handleChange(idx, 'name', e.target.value)} style={{ width: 200, color: '#111', background: '#fff', border: '1px solid #444', borderRadius: 3 }} /></div>
              <div>バージョン: <input value={game.version} onChange={e => handleChange(idx, 'version', e.target.value)} style={{ width: 100, color: '#111', background: '#fff', border: '1px solid #444', borderRadius: 3 }} /></div>
              <div>作者: <input value={game.authors.join(', ')} onChange={e => handleChange(idx, 'authors', e.target.value)} style={{ width: 200, color: '#111', background: '#fff', border: '1px solid #444', borderRadius: 3 }} placeholder="カンマ区切り" /></div>
              <div>タグ: <input value={game.tags.join(', ')} onChange={e => handleChange(idx, 'tags', e.target.value)} style={{ width: 200, color: '#111', background: '#fff', border: '1px solid #444', borderRadius: 3 }} placeholder="#タグ, #タグ" /></div>
              <div>説明: <input value={game.description} onChange={e => handleChange(idx, 'description', e.target.value)} style={{ width: 400, color: '#111', background: '#fff', border: '1px solid #444', borderRadius: 3 }} /></div>
              <div>ビルドファイル: <input value={game.buildFile} onChange={e => handleChange(idx, 'buildFile', e.target.value)} style={{ width: 200, color: '#111', background: '#fff', border: '1px solid #444', borderRadius: 3 }} /></div>
              {urlFields.map(f => (
                <div key={f.key}>
                  {f.label}: <input value={game[f.key as keyof Game] as string} onChange={e => handleChange(idx, f.key as keyof Game, e.target.value)} style={{ width: 400, color: '#111', background: '#fff', border: '1px solid #444', borderRadius: 3 }} />
                  {game[f.key as keyof Game] && (f.key === 'url' || f.key === 'unityroomurl' || f.key === 'githuburl' || f.key === 'image' || f.key === 'markdown') && (
                    isValidUrl(game[f.key as keyof Game] as string)
                      ? <span style={{ color: '#66ff66', marginLeft: 8 }}>✔</span>
                      : <span style={{ color: '#ff6666', marginLeft: 8 }}>×</span>
                  )}
                </div>
              ))}
              {!checkRequiredUrls(game) && <div style={{ color: '#ff6666' }}>※画像、ダウンロード、UnityRoom、GitHubのいずれかのURLが必要です</div>}
            </div>
          )}
        </div>
      ))}
      <button onClick={handleSave} style={{ fontSize: 18, padding: '6px 24px', background: '#333', color: '#fff', border: '1px solid #666', borderRadius: 4 }}>保存</button>
    </div>
  );
};

export default App;
