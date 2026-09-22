import React, { useState, useEffect } from "react";
import {
  Send,
  Upload,
  X,
  FileText,
  CheckCircle2,
  AlertCircle,
  AlertTriangle,
  Sparkles,
  User,
  Mail,
  Link as LinkIcon,
  MessageSquare,
  Image as ImageIcon,
} from "lucide-react";

interface EvidenceFile {
  id: string;
  name: string;
  type: string;
  size: number;
  data: string;
  previewUrl: string;
}

interface ToastNotice {
  id: string;
  type: "success" | "error" | "warning";
  title: string;
  message: string;
}

export default function PublicTicketFormPage() {
  const [solicitante, setSolicitante] = useState("");
  const [email, setEmail] = useState("");
  const [listaFiltroUrl, setListaFiltroUrl] = useState("");
  const [problema, setProblema] = useState("");
  const [descricao, setDescricao] = useState("");
  const [evidencias, setEvidencias] = useState<EvidenceFile[]>([]);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [toast, setToast] = useState<ToastNotice | null>(null);

  const [createdTicket, setCreatedTicket] = useState<{
    id: string;
    identifier: string;
    name: string;
    project_name: string;
  } | null>(null);

  // Auto dismiss toast after 4.5s
  useEffect(() => {
    if (!toast) return;
    const timer = setTimeout(() => {
      setToast(null);
    }, 4500);
    return () => clearTimeout(timer);
  }, [toast]);

  const showToast = (type: "success" | "error" | "warning", title: string, message: string) => {
    setToast({
      id: Math.random().toString(36).substring(2, 9),
      type,
      title,
      message,
    });
  };

  const handleFileUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    if (!files) return;

    Array.from(files).forEach((file) => {
      if (file.size > 15 * 1024 * 1024) {
        showToast("warning", "Arquivo Muito Grande", `O arquivo ${file.name} excede o limite máximo de 15MB.`);
        return;
      }

      const reader = new FileReader();
      reader.addEventListener("load", (event) => {
        const result = event.target?.result as string;
        setEvidencias((prev) => [
          ...prev,
          {
            id: Math.random().toString(36).substring(2, 9),
            name: file.name,
            type: file.type,
            size: file.size,
            data: result,
            previewUrl: result,
          },
        ]);
      });
      reader.readAsDataURL(file);
    });

    e.target.value = "";
  };
  // Remove file from state
  const handleRemoveFile = (id: string) => {
    setEvidencias((prev) => prev.filter((item) => item.id !== id));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    // 1. Validation check for missing fields
    if (!solicitante.trim() || !email.trim() || !problema.trim() || !descricao.trim()) {
      showToast(
        "warning",
        "Campos Incompletos",
        "Por favor, preencha todos os campos obrigatórios (Solicitante, E-mail, Problema e Descrição)."
      );
      return;
    }

    setIsSubmitting(true);

    const apiBaseUrl =
      process.env.NEXT_PUBLIC_API_BASE_URL ||
      process.env.NEXT_PUBLIC_TICKET_API_URL ||
      (import.meta as any).env?.VITE_API_BASE_URL ||
      "";

    const projectId =
      process.env.NEXT_PUBLIC_PLANE_PROJECT_ID ||
      (import.meta as any).env?.VITE_PLANE_PROJECT_ID ||
      "c3615582-e0c3-450e-a46a-79abbc2a680d";

    try {
      const response = await fetch(`${apiBaseUrl}/api/v1/public/submit-ticket/`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          solicitante,
          email,
          lista_filtro: listaFiltroUrl,
          problema,
          descricao,
          project_id: projectId,
          evidencias: evidencias.map((ev) => ({
            name: ev.name,
            type: ev.type,
            data: ev.data,
          })),
        }),
      });

      const data = await response.json();

      if (!response.ok || !data.success) {
        throw new Error(data.error || "Erro ao registrar o ticket no sistema.");
      }

      setCreatedTicket(data.issue);
      showToast("success", "Ticket Enviado!", `O ticket ${data.issue.identifier} foi criado com sucesso no Plane.`);
    } catch (err: any) {
      showToast("error", "Falha no Envio", err.message || "Erro de conexão com o servidor Plane.");
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleResetForm = () => {
    setCreatedTicket(null);
    setSolicitante("");
    setEmail("");
    setListaFiltroUrl("");
    setProblema("");
    setDescricao("");
    setEvidencias([]);
    setToast(null);
  };

  return (
    <div className="selection:bg-indigo-500/20 font-sans relative flex h-screen w-full flex-col overflow-y-auto bg-[#1F2020] text-black antialiased">
      {/* Toast Notification Container (Toastify Style) */}
      {toast && (
        <div className="animate-in slide-in-from-top-3 fade-in fixed top-4 right-4 z-50 w-full max-w-md duration-200">
          <div
            className={`shadow-2xl relative flex items-start gap-3 overflow-hidden rounded-xl border bg-white p-4 ${
              toast.type === "success"
                ? "border-l-emerald-500 border-slate-200 border-l-4"
                : toast.type === "warning"
                  ? "border-l-amber-500 border-slate-200 border-l-4"
                  : "border-l-rose-500 border-slate-200 border-l-4"
            }`}
          >
            {/* Icon */}
            {toast.type === "success" && <CheckCircle2 className="text-emerald-600 mt-0.5 h-5 w-5 shrink-0" />}
            {toast.type === "warning" && <AlertTriangle className="text-amber-600 mt-0.5 h-5 w-5 shrink-0" />}
            {toast.type === "error" && <AlertCircle className="text-rose-600 mt-0.5 h-5 w-5 shrink-0" />}

            {/* Content */}
            <div className="flex-1 pr-4">
              <h4 className="font-extrabold text-sm tracking-tight text-black">{toast.title}</h4>
              <p className="text-xs text-slate-800 mt-0.5 leading-snug font-bold">{toast.message}</p>
            </div>

            {/* Close Button */}
            <button
              onClick={() => setToast(null)}
              className="text-slate-400 rounded-md p-1 transition-colors hover:text-black"
            >
              <X className="h-4 w-4" />
            </button>

            {/* Bottom Progress Bar */}
            <div
              className={`animate-progress absolute bottom-0 left-0 h-1 ${
                toast.type === "success" ? "bg-emerald-500" : toast.type === "warning" ? "bg-amber-500" : "bg-rose-500"
              }`}
              style={{ animationDuration: "4500ms" }}
            />
          </div>
        </div>
      )}

      {/* Top Header - White Background, Aligned Directly to Far Left Edge */}
      <header className="border-slate-300 shadow-xs sticky top-0 z-30 border-b bg-white px-4 py-3">
        <div className="flex items-center gap-2.5">
          <div className="bg-indigo-600 shadow-sm flex h-7 w-7 items-center justify-center rounded-md text-white">
            <Sparkles className="h-4 w-4" />
          </div>
          <h1 className="font-extrabold text-base tracking-tight text-black">Plane - Formulário de Tickets</h1>
        </div>
      </header>

      {/* Main Content Area - Google Forms Inspired Style */}
      <main className="mx-auto w-full max-w-2xl flex-1 px-4 py-8">
        {createdTicket ? (
          /* Success Screen Card */
          <div className="border-slate-300 shadow-xl my-6 overflow-hidden rounded-xl border bg-white text-center">
            <div className="bg-emerald-600 h-3 w-full" />
            <div className="p-8 sm:p-10">
              <div className="bg-emerald-100 border-emerald-300 text-emerald-700 shadow-sm mx-auto mb-5 flex h-16 w-16 items-center justify-center rounded-full border">
                <CheckCircle2 className="h-8 w-8" />
              </div>
              <h2 className="text-2xl font-extrabold mb-2 text-black">Ticket Criado com Sucesso!</h2>
              <p className="text-sm mx-auto mb-6 max-w-md font-semibold text-black">
                Sua solicitação foi salva e enviada para o projeto no Plane.
              </p>

              <div className="bg-slate-100 border-slate-300 mx-auto mb-8 max-w-sm rounded-lg border p-4 text-left">
                <div className="text-xs font-extrabold tracking-wider mb-1 text-black uppercase">
                  Identificador do Ticket
                </div>
                <div className="text-indigo-700 font-mono text-xl font-extrabold flex items-center justify-between">
                  <span>{createdTicket.identifier}</span>
                  <span className="text-xs font-sans font-extrabold bg-slate-300 rounded-md px-2.5 py-1 text-black">
                    {createdTicket.project_name}
                  </span>
                </div>
                <div className="text-sm border-slate-300 mt-3 truncate border-t pt-3 font-bold text-black">
                  {createdTicket.name}
                </div>
              </div>

              <button
                onClick={handleResetForm}
                className="font-extrabold text-sm shadow-md border-slate-700 mx-auto flex cursor-pointer items-center justify-center gap-2 rounded-lg border bg-[#1F2020] px-6 py-3 text-white transition-all duration-200 hover:bg-[#2D2E2E] active:scale-95"
              >
                <Sparkles className="text-indigo-400 h-4 w-4" />
                <span>Criar outro ticket</span>
              </button>
            </div>
          </div>
        ) : (
          /* Google Forms Style Layout */
          <div className="my-2 space-y-4">
            {/* Top Form Title Card */}
            <div className="border-slate-300 shadow-md overflow-hidden rounded-xl border bg-white">
              {/* Google Forms Top Color Accent Bar */}
              <div className="from-indigo-600 to-indigo-500 h-3 w-full bg-gradient-to-r" />
              <div className="p-6 sm:p-8">
                <h2 className="text-2xl sm:text-3xl font-extrabold flex items-center gap-2.5 tracking-tight text-black">
                  <FileText className="text-indigo-600 h-7 w-7" />
                  Novo Ticket de Solicitação
                </h2>
                <p className="text-sm mt-2 font-bold text-black">
                  Preencha todos os campos do formulário para registrar um problema ou chamado.
                </p>
              </div>
            </div>

            {/* Form Container Card */}
            <form
              onSubmit={handleSubmit}
              className="border-slate-300 shadow-md space-y-6 rounded-xl border bg-white p-6 sm:p-8"
            >
              {/* Solicitante */}
              <div>
                <label
                  htmlFor="solicitante"
                  className="text-sm font-extrabold mb-2 block flex items-center gap-1.5 text-black"
                >
                  <User className="text-indigo-600 h-4 w-4" /> Solicitante{" "}
                  <span style={{ color: "#dc2626" }} className="font-extrabold text-base ml-0.5">
                    *
                  </span>
                </label>
                <input
                  id="solicitante"
                  type="text"
                  placeholder="Seu nome completo"
                  value={solicitante}
                  onChange={(e) => setSolicitante(e.target.value)}
                  className="border-slate-300 text-sm placeholder:text-slate-500 focus:border-indigo-600 focus:ring-indigo-600/20 shadow-xs w-full rounded-lg border-2 bg-white px-4 py-2.5 font-bold text-black transition-all focus:ring-2 focus:outline-none"
                />
              </div>

              {/* E-mail do Usuário */}
              <div>
                <label
                  htmlFor="email"
                  className="text-sm font-extrabold mb-2 block flex items-center gap-1.5 text-black"
                >
                  <Mail className="text-indigo-600 h-4 w-4" /> E-mail do usuário{" "}
                  <span style={{ color: "#dc2626" }} className="font-extrabold text-base ml-0.5">
                    *
                  </span>
                </label>
                <input
                  id="email"
                  type="email"
                  placeholder="usuario@empresa.com"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  className="border-slate-300 text-sm placeholder:text-slate-500 focus:border-indigo-600 focus:ring-indigo-600/20 shadow-xs w-full rounded-lg border-2 bg-white px-4 py-2.5 font-bold text-black transition-all focus:ring-2 focus:outline-none"
                />
              </div>

              {/* Lista / Filtro (URL Input) */}
              <div>
                <label
                  htmlFor="lista_filtro_url"
                  className="text-sm font-extrabold mb-2 block flex items-center gap-1.5 text-black"
                >
                  <LinkIcon className="text-indigo-600 h-4 w-4" /> Lista / Filtro
                </label>
                <input
                  id="lista_filtro_url"
                  type="url"
                  placeholder="https://sua-empresa.com/pagina-ou-filtro"
                  value={listaFiltroUrl}
                  onChange={(e) => setListaFiltroUrl(e.target.value)}
                  className="border-slate-300 text-sm placeholder:text-slate-500 focus:border-indigo-600 focus:ring-indigo-600/20 shadow-xs w-full rounded-lg border-2 bg-white px-4 py-2.5 font-bold text-black transition-all focus:ring-2 focus:outline-none"
                />
              </div>

              {/* Problema */}
              <div>
                <label
                  htmlFor="problema"
                  className="text-sm font-extrabold mb-2 block flex items-center gap-1.5 text-black"
                >
                  <MessageSquare className="text-indigo-600 h-4 w-4" /> Problema{" "}
                  <span style={{ color: "#dc2626" }} className="font-extrabold text-base ml-0.5">
                    *
                  </span>
                </label>
                <input
                  id="problema"
                  type="text"
                  placeholder="Resumo breve do problema"
                  value={problema}
                  onChange={(e) => setProblema(e.target.value)}
                  className="border-slate-300 text-sm placeholder:text-slate-500 focus:border-indigo-600 focus:ring-indigo-600/20 shadow-xs w-full rounded-lg border-2 bg-white px-4 py-2.5 font-bold text-black transition-all focus:ring-2 focus:outline-none"
                />
              </div>

              {/* Descrição */}
              <div>
                <label
                  htmlFor="descricao"
                  className="text-sm font-extrabold mb-2 block flex items-center gap-1.5 text-black"
                >
                  <FileText className="text-indigo-600 h-4 w-4" /> Descrição{" "}
                  <span style={{ color: "#dc2626" }} className="font-extrabold text-base ml-0.5">
                    *
                  </span>
                </label>
                <textarea
                  id="descricao"
                  rows={4}
                  placeholder="Descreva o problema com o maior detalhamento possível..."
                  value={descricao}
                  onChange={(e) => setDescricao(e.target.value)}
                  className="border-slate-300 text-sm placeholder:text-slate-500 focus:border-indigo-600 focus:ring-indigo-600/20 shadow-xs w-full resize-y rounded-lg border-2 bg-white p-4 font-bold text-black transition-all focus:ring-2 focus:outline-none"
                />
              </div>

              {/* Evidências */}
              <div>
                <label
                  htmlFor="evidencias_upload"
                  className="text-sm font-extrabold mb-2 block flex items-center gap-1.5 text-black"
                >
                  <ImageIcon className="text-indigo-600 h-4 w-4" /> Evidências (Imagens / Vídeos)
                </label>

                {/* Dropzone */}
                <div className="border-slate-400 hover:border-indigo-600 bg-slate-50 hover:bg-indigo-50/50 group relative rounded-lg border-2 border-dashed p-6 text-center transition-all">
                  <input
                    id="evidencias_upload"
                    type="file"
                    multiple
                    accept="image/*,video/*"
                    onChange={handleFileUpload}
                    className="absolute inset-0 z-10 h-full w-full cursor-pointer opacity-0"
                  />
                  <div className="border-slate-300 group-hover:text-indigo-600 group-hover:border-indigo-400 shadow-xs mx-auto mb-2 flex h-10 w-10 items-center justify-center rounded-full border bg-white text-black transition-all">
                    <Upload className="h-5 w-5" />
                  </div>
                  <p className="text-sm font-extrabold text-black">Clique ou arraste arquivos para anexar</p>
                  <p className="text-xs mt-1 font-bold text-black">
                    Anexe prints, fotos ou vídeos (até 15MB por arquivo).
                  </p>
                </div>

                {/* File Previews */}
                {evidencias.length > 0 && (
                  <div className="mt-4 grid grid-cols-2 gap-3 sm:grid-cols-3">
                    {evidencias.map((item) => (
                      <div
                        key={item.id}
                        className="group bg-slate-100 border-slate-300 shadow-xs relative flex flex-col justify-between overflow-hidden rounded-lg border p-2"
                      >
                        <button
                          type="button"
                          onClick={() => handleRemoveFile(item.id)}
                          className="hover:text-rose-600 hover:bg-rose-50 border-slate-300 shadow-xs absolute top-1.5 right-1.5 z-20 rounded-full border bg-white p-1 text-black transition-all"
                        >
                          <X className="h-3.5 w-3.5" />
                        </button>

                        <div className="border-slate-300 mb-2 flex h-24 w-full items-center justify-center overflow-hidden rounded-md border bg-white">
                          {item.type.startsWith("image/") ? (
                            <img src={item.previewUrl} alt={item.name} className="h-full w-full object-cover" />
                          ) : item.type.startsWith("video/") ? (
                            <video src={item.previewUrl} className="h-full w-full object-cover">
                              <track kind="captions" />
                            </video>
                          ) : (
                            <FileText className="h-8 w-8 text-black" />
                          )}
                        </div>

                        <div className="px-1 pb-1">
                          <p className="text-xs font-extrabold truncate text-black">{item.name}</p>
                          <p className="text-[10px] font-bold text-black">{(item.size / 1024 / 1024).toFixed(2)} MB</p>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>

              {/* Submit Button */}
              <div className="flex justify-end pt-2">
                <button
                  type="submit"
                  disabled={isSubmitting}
                  className="font-extrabold text-sm shadow-md border-slate-700 flex w-full cursor-pointer items-center justify-center gap-2 rounded-lg border bg-[#1F2020] px-8 py-3 text-white transition-all duration-200 hover:bg-[#2D2E2E] active:scale-[0.99] disabled:cursor-not-allowed disabled:opacity-50 sm:w-auto"
                >
                  {isSubmitting ? (
                    <>
                      <div className="h-4 w-4 animate-spin rounded-full border-2 border-white/30 border-t-white" />
                      <span>Enviando...</span>
                    </>
                  ) : (
                    <>
                      <Send className="h-4 w-4" />
                      <span>Enviar Ticket</span>
                    </>
                  )}
                </button>
              </div>
            </form>
          </div>
        )}
      </main>

      {/* Footer */}
      <footer className="text-xs border-slate-800 border-t bg-[#1F2020] py-4 text-center font-bold text-white">
        Formulário integrado ao{" "}
        <a
          href="https://plane.speedio.com.br/speedio"
          target="_blank"
          rel="noopener noreferrer"
          className="font-extrabold hover:text-indigo-300 text-white underline transition-colors"
        >
          Plane
        </a>
      </footer>
    </div>
  );
}
