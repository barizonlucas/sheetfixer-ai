import { useState, useEffect } from 'react';
import pixImage from './assets/pix_qrcode.jpeg';

const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000/api";

const SLOGANS = {
  en: "Your question becomes a formula.",
  pt: "Sua dúvida vira fórmula.",
  es: "Tu duda se convierte en fórmula."
};

const LOADING_MESSAGES = {
  en: [
    "Analyzing your request...",
    "Mapping spreadsheet cells...",
    "Consulting the formula gods...",
    "Ekualizing the final code..."
  ],
  pt: [
    "Analisando seu pedido...",
    "Mapeando células da planilha...",
    "Consultando os deuses das fórmulas...",
    "Ekualizando a solução perfeita..."
  ],
  es: [
    "Analizando tu petición...",
    "Mapeando celdas de la hoja...",
    "Consultando a los dioses de las fórmulas...",
    "Ekualizando la solución perfecta..."
  ]
};

// Interpretador simples de Markdown para HTML
const formatMarkdown = (text) => {
  if (!text) return { __html: '' };
  
  let html = text
    // 1. Remove excesso de quebras de linha (3 ou mais viram apenas 2)
    .replace(/\n{3,}/g, '\n\n')
    // 2. Converte Negrito: **texto** para <strong>
    .replace(/\*\*(.*?)\*\*/g, '<strong class="text-white font-semibold">$1</strong>')
    // 3. Converte Código em Linha: `código` para <code> com visual de célula
    .replace(/`(.*?)`/g, '<code class="bg-blue-950/60 text-emerald-300 px-1.5 py-0.5 rounded font-mono text-xs shadow-sm">$1</code>');
    
  // 4. Converte Listas: linhas que começam com * ou -
  html = html.replace(/(?:^ *[-*]\s+.*(?:\r?\n|$))+/gm, (match) => {
      const listItems = match.trim().split(/\r?\n/).map(item => `<li class="ml-6 list-disc mb-1">${item.replace(/^ *[-*]\s+/, '')}</li>`).join('');
      return `<ul class="my-1">${listItems}</ul>`;
  });

  return { __html: html.trim() };
};

export default function App() {
  const [lang, setLang] = useState('pt');
  const [translations, setTranslations] = useState({});
  const [config, setConfig] = useState({});
  
  const [tool, setTool] = useState('Excel');
  const [problem, setProblem] = useState('');
  
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [result, setResult] = useState(null);
  const [isSidebarOpen, setSidebarOpen] = useState(false);
  const [loadingStep, setLoadingStep] = useState(0);

  useEffect(() => {
    fetch(`${API_URL}/config`)
      .then(res => res.json())
      .then(data => setConfig(data))
      .catch(err => console.error("Erro ao carregar configs:", err));
  }, []);

  useEffect(() => {
    fetch(`${API_URL}/locales/${lang}`)
      .then(res => res.json())
      .then(data => setTranslations(data))
      .catch(err => console.error("Erro ao carregar traduções:", err));
  }, [lang]);

  // Efeito para rotacionar as mensagens de loading enquanto carrega
  useEffect(() => {
    let interval;
    if (loading) {
      setLoadingStep(0); // Reseta para a primeira mensagem
      interval = setInterval(() => {
        setLoadingStep(prev => prev + 1);
      }, 2500); // Troca a mensagem a cada 2.5s
    }
    return () => clearInterval(interval);
  }, [loading]);

  const t = (key, fallback) => translations[key] || fallback;

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!problem.trim()) {
      setError(t("warning_msg", "Descreva o problema primeiro."));
      return;
    }
    setError('');
    setLoading(true);
    setResult(null);

    try {
      const res = await fetch(`${API_URL}/generate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ problem, tool, lang_code: lang })
      });
      const data = await res.json();
      
      if (!res.ok) throw new Error(data.detail || "Erro de API");
      setResult(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleExportExcel = async () => {
    if (!result || !result.sample_data) return;
    
    try {
      const res = await fetch(`${API_URL}/export-excel`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ sample_data: result.sample_data })
      });
      
      if (!res.ok) throw new Error(t("error_exporting", "Erro ao gerar arquivo Excel"));
      
      const blob = await res.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = 'ekual_exemplo.xlsx';
      document.body.appendChild(a);
      a.click();
      a.remove();
      window.URL.revokeObjectURL(url);
    } catch (err) {
      alert(err.message);
    }
  };

  return (
    <div className="flex min-h-screen">
      {/* Sidebar */}
      <aside className={`bg-slate-900 text-slate-300 w-64 flex-shrink-0 flex flex-col p-4 fixed top-0 md:sticky h-screen overflow-y-auto transition-transform duration-300 z-50 ${isSidebarOpen ? 'translate-x-0' : '-translate-x-full md:translate-x-0'}`}>
        <div className="text-2xl font-bold text-white mb-8">
          Ekual <span className="text-coral-500">🟰</span>
        </div>

        <nav className="flex-grow">
          <h3 className="text-sm font-semibold text-slate-500 uppercase mb-2">Idioma</h3>
          <ul className="space-y-1">
            {['en', 'pt', 'es'].map(l => (
              <li key={l}>
                <button onClick={() => setLang(l)} className={`w-full text-left flex items-center p-2 rounded-lg ${lang === l ? 'bg-slate-800 font-bold' : 'hover:bg-slate-800'}`}>
                  {l === 'en' ? '🇬🇧 English' : l === 'pt' ? '🇧🇷 Português' : '🇪🇸 Español'}
                </button>
              </li>
            ))}
          </ul>
        </nav>

        <div className="mt-auto pt-8">
          <h3 className="text-sm font-semibold text-slate-500 uppercase mb-2">Apoie o projeto</h3>
          {lang === 'pt' ? (
             <div className="p-4 bg-slate-800 rounded-lg text-center">
                <p className="text-sm text-slate-300 font-bold mb-2">Pix (Brasil):</p>
                <img src={pixImage} alt="QR Code Pix" className="w-full max-w-[150px] mx-auto rounded-lg shadow-md mb-3" />
             </div>
          ) : (
             <div className="text-center">
                <a href={config.bmc_link || "#"} target="_blank" rel="noreferrer" className="inline-block">
                  <img src="https://cdn.buymeacoffee.com/buttons/v2/default-yellow.png" alt="Buy Me A Coffee" className="h-10 w-auto rounded" />
                </a>
             </div>
          )}
        </div>
      </aside>

      {/* Main Content */}
      <main className="flex-1 p-4 md:p-8 overflow-y-auto w-full">
        <div className="max-w-3xl mx-auto">
          <div className="md:hidden flex justify-between items-center mb-6">
            <div className="text-2xl font-bold text-white">Ekual <span className="text-coral-500">🟰</span></div>
            <button onClick={() => setSidebarOpen(!isSidebarOpen)} className="text-white text-2xl"><i className="fas fa-bars"></i></button>
          </div>

          <header className="text-center mb-10 mt-8">
            <h1 className="text-5xl md:text-6xl font-extrabold text-white">Eku<span className="text-coral-500">a</span>l</h1>
            <p className="mt-3 text-lg text-slate-400">{SLOGANS[lang]}</p>
          </header>

          <div className="bg-slate-900 p-6 md:p-8 rounded-xl shadow-2xl">
            <form onSubmit={handleSubmit}>
              <div className="mb-6">
                <label className="block text-sm font-medium text-slate-300 mb-2">{t("tool_selector_label", "Ferramenta:")}</label>
                <select value={tool} onChange={(e) => setTool(e.target.value)} className="w-full bg-slate-800 border-2 border-slate-700 text-white rounded-lg px-4 py-3 focus:outline-none focus:ring-2 focus:ring-emerald-600">
                  <option>Excel</option>
                  <option>Google Sheets</option>
                  <option>VBA</option>
                  <option>Google Apps Script</option>
                </select>
              </div>

              <div className="mb-6">
                <label className="block text-sm font-medium text-slate-300 mb-2">{t("problem_description_label", "Descreva o problema:")}</label>
                <textarea value={problem} onChange={(e) => setProblem(e.target.value)} rows="6" className="w-full bg-slate-800 border-2 border-slate-700 text-white rounded-lg px-4 py-3 focus:outline-none focus:ring-2 focus:ring-emerald-600" placeholder={t("problem_placeholder", "Ex: Somar coluna A...")}></textarea>
                {error && <p className="text-red-500 text-sm mt-2">{error}</p>}
              </div>

              <button disabled={loading} type="submit" className="w-full bg-emerald-600 text-white font-bold py-3 px-4 rounded-lg shadow-lg hover:bg-emerald-700 transition-all disabled:opacity-50">
                {loading ? t("spinner_msg", "Processando...") : t("generate_solution_button", "✨ Ekualizar")}
              </button>
            </form>
          </div>

          {/* Creative Loading Feedback */}
          {loading && (
            <div className="mt-8 flex flex-col items-center justify-center py-10 bg-slate-900/50 rounded-xl border border-emerald-500/20 shadow-inner animate-fade-in">
               <div className="text-5xl animate-bounce mb-6 text-coral-500 drop-shadow-lg">🟰</div>
               <p className="text-emerald-400 font-medium text-lg animate-pulse text-center px-4">
                 {LOADING_MESSAGES[lang][loadingStep % LOADING_MESSAGES[lang].length]}
               </p>
            </div>
          )}

          {result && (
            <div className="mt-8 animate-fade-in">
               <div className="bg-emerald-900/40 border border-emerald-600 p-4 rounded-lg mb-6 text-emerald-400 font-bold">
                  {t("success_msg", "✅ Solução Encontrada!")}
               </div>

               <h3 className="font-bold text-white mb-2">{t("code_label", "Fórmula / Código")}:</h3>
               <div className="bg-slate-950 p-4 rounded-lg mb-6 overflow-x-auto relative group">
                 <code className="text-coral-400 font-mono text-sm whitespace-pre-wrap break-all">{result.code}</code>
               </div>

               {result.sample_data && result.sample_data.length > 0 && (
                 <div className="mb-6">
                   <button onClick={handleExportExcel} className="bg-emerald-600 hover:bg-emerald-700 text-white font-bold py-2 px-4 rounded-lg shadow-lg flex items-center justify-center gap-2 w-full sm:w-auto transition-all">
                     <i className="fas fa-file-excel"></i> {t("download_button", "📥 Baixar Planilha de Exemplo")}
                   </button>
                   <p className="text-xs text-slate-400 mt-2">
                     {t("download_tip", "💡 Dica: Se as fórmulas não carregarem automaticamente no Google Sheets, tente atualizar a página ou clicar na célula da fórmula.")}
                   </p>
                 </div>
               )}

               <div className="bg-blue-900/30 border-l-4 border-blue-500 p-4 rounded-lg mb-6">
                  <span className="block mb-3 text-base text-blue-100">💡 <strong>Explicação:</strong></span>
                  <div 
                    className="text-blue-100 text-sm leading-relaxed whitespace-pre-wrap"
                    dangerouslySetInnerHTML={formatMarkdown(result.explanation)}
                  />
               </div>

               <details className="bg-slate-800 rounded-lg mb-6 cursor-pointer">
                  <summary className="p-4 font-bold text-white outline-none">📝 {t("tips_label", "Passo a passo")}</summary>
                  <ul className="p-4 pt-0 list-disc list-inside text-slate-300 text-sm space-y-2">
                    {(result.tips || []).map((tip, idx) => <li key={idx}>{tip}</li>)}
                  </ul>
               </details>
            </div>
          )}
        </div>
      </main>
    </div>
  );
}