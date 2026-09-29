const state = { activeSessionData: null, sending: false };
const elements = {
  sendBtn: document.querySelector("#send-btn"),
  chatForm: document.querySelector("#chat-form"),
  messageInput: document.querySelector("#message-input"),
  messageList: document.querySelector("#message-list"),
  chatStatus: document.querySelector("#chat-status"),
  messageTemplate: document.querySelector("#message-template"),
};

document.addEventListener("DOMContentLoaded", () => {
  elements.chatForm.addEventListener("submit", handleSendMessage);
  elements.messageInput.addEventListener("input", autoResizeTextarea);
  elements.messageInput.addEventListener("keydown", (event) => {
    if (event.key === "Enter" && !event.shiftKey) {
      event.preventDefault();
      elements.chatForm.requestSubmit();
    }
  });
  initialize();
});

async function initialize() {
  try {
    setStatus("正在准备第一道字谜...", true);
    const result = await request("/api/session");
    state.activeSessionData = result.data;
    renderMessages(result.data.message || []);
    if ((result.data.message || []).length === 0) {
      await sendMessage("开始出题", true);
    } else {
      setStatus("轮到你来猜了");
      updateComposerState();
      elements.messageInput.focus();
    }
  } catch (error) {
    setStatus(error.message || "准备会话失败");
  }
}

async function handleSendMessage(event) {
  event.preventDefault();
  const message = elements.messageInput.value.trim();
  if (message && !state.sending) await sendMessage(message);
}

async function sendMessage(message, isInitial = false) {
  if (!state.activeSessionData || state.sending) return;
  const draft = elements.messageInput.value;
  if (!isInitial) {
    elements.messageInput.value = "";
    autoResizeTextarea();
  }
  state.sending = true;
  updateComposerState();
  const currentMessages = state.activeSessionData?.message || [];
  const optimisticMessages = [...currentMessages, { role: "user", content: message }];
  renderMessages([
    ...(isInitial ? currentMessages : optimisticMessages),
    { role: "assistant", pending: true },
  ]);
  setStatus("出题人正在思考...", true);
  try {
    const result = await request("/api/chat", {
      method: "POST",
      body: JSON.stringify({ message }),
    });
    state.activeSessionData.message = [
      ...optimisticMessages,
      { role: "assistant", content: result.data },
    ];
    renderMessages(state.activeSessionData.message);
    setStatus("轮到你来猜了");
  } catch (error) {
    renderMessages(currentMessages);
    if (!isInitial) {
      elements.messageInput.value = draft;
      autoResizeTextarea();
    }
    setStatus(error.message || "发送消息失败");
  } finally {
    state.sending = false;
    updateComposerState();
    elements.messageInput.focus();
  }
}

function renderMessages(messages) {
  elements.messageList.innerHTML = "";
  if (!messages.length) {
    elements.messageList.innerHTML = '<div class="empty-state"><div class="empty-ink" aria-hidden="true"></div><p class="empty-title">正在出题</p><p class="empty-copy">请稍等，出题人马上就来。</p></div>';
    return;
  }
  messages.forEach((message) => {
    const node = elements.messageTemplate.content.firstElementChild.cloneNode(true);
    const isAssistant = message.role === "assistant";
    node.classList.add(isAssistant ? "assistant" : "user");
    node.insertAdjacentHTML(
      "afterbegin",
      `<img class="message-avatar" src="/static/images/${isAssistant ? "chutiren_avatar.png" : "user_avatar.png"}?v=20260929-avatars" alt="">`
    );
    node.querySelector(".message-role").textContent = isAssistant ? "出题人" : "我";
    const bubble = node.querySelector(".message-bubble");
    if (message.pending) {
      node.classList.add("pending");
      bubble.setAttribute("aria-label", "出题人正在输入");
      bubble.innerHTML = '<span class="typing-indicator" aria-hidden="true"><span></span><span></span><span></span></span>';
    } else {
      bubble.textContent = message.content || "";
    }
    elements.messageList.appendChild(node);
  });
  elements.messageList.scrollTop = elements.messageList.scrollHeight;
}

function updateComposerState() {
  elements.sendBtn.disabled = state.sending || !state.activeSessionData;
  elements.messageInput.disabled = state.sending || !state.activeSessionData;
}

function setStatus(message, loading = false) {
  elements.chatStatus.textContent = message;
  elements.chatStatus.classList.toggle("loading", loading);
}

function autoResizeTextarea() {
  elements.messageInput.style.height = "auto";
  elements.messageInput.style.height = `${Math.min(elements.messageInput.scrollHeight, 180)}px`;
}

async function request(url, options = {}) {
  const response = await fetch(url, {
    headers: { "Content-Type": "application/json", ...(options.headers || {}) },
    ...options,
  });
  const result = await response.json();
  if (!response.ok || result.code !== 200) throw new Error(result.message || "请求失败");
  return result;
}
