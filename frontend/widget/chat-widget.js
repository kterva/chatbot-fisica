// Widget de chat mínimo. Solo habla con el backend propio (API_URL); nunca con el
// proveedor LLM directamente y nunca maneja API keys.
(function () {
  "use strict";

  // Ruta relativa: asume que nginx sirve el widget y proxea /api/ al backend bajo
  // el mismo dominio. Si el widget se embebe en un dominio distinto al del backend
  // (ej. WordPress en otro host), cambiar por la URL absoluta pública del backend.
  const API_URL = "/api/chat";

  const messagesEl = document.getElementById("fisica-chat-messages");
  const formEl = document.getElementById("fisica-chat-form");
  const inputEl = document.getElementById("fisica-chat-input");
  const submitEl = document.getElementById("fisica-chat-submit");
  const versionEl = document.getElementById("fisica-version");

  // Solo relevante en la página standalone (ver chat-widget.html); si el widget se
  // embebe sin ese elemento, esto simplemente no hace nada. Si el fetch falla, se
  // deja el texto estático que ya tiene el elemento en el HTML.
  if (versionEl) {
    fetch("/version")
      .then((response) => response.json())
      .then((data) => {
        if (data.version) {
          versionEl.textContent = data.version;
        }
      })
      .catch(() => {});
  }

  // Delimitadores que le pedimos al asistente en el system prompt. Se listan
  // explícitamente porque el config por defecto de auto-render no incluye "$...$"
  // (para no confundir con signos de dólar en texto común) — acá no hay ese riesgo,
  // el bot solo habla de Física.
  const KATEX_DELIMITERS = [
    { left: "$$", right: "$$", display: true },
    { left: "\\[", right: "\\]", display: true },
    { left: "$", right: "$", display: false },
    { left: "\\(", right: "\\)", display: false },
  ];

  function renderMath(el) {
    // Si el script de KaTeX no cargó (ej. sin conexión al CDN), se deja el texto
    // plano con la notación LaTeX tal cual: sigue siendo legible, solo no se
    // renderiza como fórmula.
    if (typeof renderMathInElement !== "function") {
      return;
    }
    try {
      renderMathInElement(el, {
        delimiters: KATEX_DELIMITERS,
        throwOnError: false,
      });
    } catch (error) {
      // No interrumpir el chat por un error de renderizado de una fórmula puntual.
    }
  }

  function appendMessage(role, text) {
    const messageEl = document.createElement("div");
    messageEl.className = "fisica-chat-message fisica-chat-message--" + role;
    messageEl.textContent = text; // textContent evita inyección de HTML/XSS
    messagesEl.appendChild(messageEl);
    messagesEl.scrollTop = messagesEl.scrollHeight;
    return messageEl;
  }

  async function sendQuestion(question) {
    const response = await fetch(API_URL, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ question }),
    });

    if (response.status === 429) {
      throw new Error("Demasiadas preguntas seguidas. Espera un momento e intenta de nuevo.");
    }
    if (!response.ok) {
      throw new Error("No se pudo obtener respuesta del asistente. Intenta nuevamente.");
    }

    const data = await response.json();
    return data.answer;
  }

  formEl.addEventListener("submit", async function (event) {
    event.preventDefault();

    const question = inputEl.value.trim();
    if (!question) {
      return;
    }

    appendMessage("user", question);
    inputEl.value = "";
    inputEl.disabled = true;
    submitEl.disabled = true;

    const pendingEl = appendMessage("assistant", "Pensando...");

    try {
      const answer = await sendQuestion(question);
      pendingEl.textContent = answer;
      renderMath(pendingEl);
    } catch (error) {
      pendingEl.textContent = error.message;
      pendingEl.classList.add("fisica-chat-message--error");
    } finally {
      inputEl.disabled = false;
      submitEl.disabled = false;
      inputEl.focus();
    }
  });
})();
