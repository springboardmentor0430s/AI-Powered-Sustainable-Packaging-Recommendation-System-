import {
  requireAuthOrRedirect,
  sendChatMessage,
  logout,
  mountNavbarProfileChip,
  mountLogoutButton,
} from './api.js';

/*
 * Chat module with conversation threading.
 *
 * Fixes:
 * - Rebuild `history` when loading an existing thread (so follow-ups work after switching/reload).
 * - Send only last N history messages to backend (keeps requests small + fast).
 */

// DOM elements
const chatMessages = document.getElementById('chatMessages');
const chatForm = document.getElementById('chatForm');
const chatInput = document.getElementById('chatInput');
const chatClear = document.getElementById('chatClear');
const chatThreadsList = document.getElementById('chatThreadsList');
const newChatBtn = document.getElementById('newChatBtn');

// Storage keys
const THREADS_KEY = 'ecopackai_chat_threads';
const CURRENT_THREAD_KEY = 'ecopackai_chat_current_thread';

// Max history to send for context (keeps payload small)
const MAX_HISTORY_TO_SEND = 12;

let threads = [];
let currentThreadId = null;
let isSending = false;

// The current conversation history used for sending messages.
// Each entry: { role: 'user' | 'assistant', content: string }
let history = [];

// Voice mode state
let voiceEnabled = false;
let recognition = null;

function generateId() {
  return `${Date.now()}-${Math.random().toString(36).substr(2, 6)}`;
}

function saveThreads() {
  try {
    localStorage.setItem(THREADS_KEY, JSON.stringify(threads));
    if (currentThreadId) {
      localStorage.setItem(CURRENT_THREAD_KEY, String(currentThreadId));
    }
  } catch (err) {
    console.warn('Unable to save chat threads:', err);
  }
}

function loadThreads() {
  try {
    const raw = localStorage.getItem(THREADS_KEY);
    const cur = localStorage.getItem(CURRENT_THREAD_KEY);
    let loaded = [];
    if (raw) {
      const parsed = JSON.parse(raw);
      if (Array.isArray(parsed)) loaded = parsed;
    }
    threads = loaded;
    currentThreadId = cur || null;
  } catch (err) {
    console.warn('Unable to load chat threads:', err);
    threads = [];
    currentThreadId = null;
  }
}

function getThreadById(id) {
  return threads.find((t) => String(t.id) === String(id));
}

function ensureCurrentThread() {
  if (currentThreadId && getThreadById(currentThreadId)) return;
  if (threads.length) {
    currentThreadId = String(threads[0].id);
    return;
  }
  newChat();
}

function createMessageBubble(role, content) {
  const wrapper = document.createElement('div');
  wrapper.className = `chat-bubble ${role === 'user' ? 'chat-bubble-user' : 'chat-bubble-ai'}`;

  const label = document.createElement('div');
  label.className = 'chat-bubble-label';
  label.textContent = role === 'user' ? 'You' : 'EcoPackAI';

  const text = document.createElement('p');
  text.className = 'chat-bubble-text mb-0';
  text.textContent = content;

  wrapper.append(label, text);
  return wrapper;
}

function scrollToBottom() {
  if (chatMessages) {
    chatMessages.scrollTop = chatMessages.scrollHeight;
  }
}

function renderThreadsList() {
  if (!chatThreadsList) return;
  chatThreadsList.innerHTML = '';

  if (!threads.length) {
    const li = document.createElement('li');
    li.className = 'list-group-item text-muted';
    li.textContent = 'No chats yet.';
    chatThreadsList.appendChild(li);
    return;
  }

  threads.forEach((thread) => {
    const li = document.createElement('li');
    li.className = 'list-group-item p-0';

    const container = document.createElement('div');
    container.className = 'd-flex justify-content-between align-items-center';

    const button = document.createElement('button');
    button.type = 'button';
    button.className = 'list-group-item-action border-0 bg-transparent text-start flex-grow-1 py-2 px-3';
    button.style.whiteSpace = 'nowrap';
    button.style.overflow = 'hidden';
    button.style.textOverflow = 'ellipsis';
    button.setAttribute('data-thread-id', String(thread.id));
    button.setAttribute('aria-label', `Open chat: ${thread.title || 'Untitled'}`);
    button.textContent = thread.title || 'Untitled';

    if (String(thread.id) === String(currentThreadId)) {
      button.classList.add('fw-bold');
    }

    button.addEventListener('click', () => {
      selectThread(thread.id);
    });

    const delBtn = document.createElement('button');
    delBtn.type = 'button';
    delBtn.className = 'btn btn-sm btn-link text-danger px-2';
    delBtn.setAttribute('aria-label', `Delete chat: ${thread.title || 'Untitled'}`);
    delBtn.innerHTML = '<i class="bi bi-trash" aria-hidden="true"></i>';
    delBtn.addEventListener('click', (e) => {
      e.stopPropagation();
      deleteThread(thread.id);
    });

    container.append(button, delBtn);
    li.appendChild(container);
    chatThreadsList.appendChild(li);
  });
}

function updateThreadTitle(thread) {
  const firstUserMsg = (thread.messages || []).find((m) => m.role === 'user');
  if (firstUserMsg && firstUserMsg.content) {
    const trimmed = firstUserMsg.content.trim().split(/\s+/).slice(0, 8).join(' ');
    thread.title = trimmed.length > 0 ? trimmed : thread.title;
  }
  if (!thread.title) {
    const d = new Date(thread.createdAt || Date.now());
    thread.title = d.toLocaleString(undefined, { month: 'short', day: 'numeric' });
  }
}

function rebuildHistoryFromThread(thread) {
  // IMPORTANT: This fixes missing context after switching threads/reload.
  history = [];
  if (!thread || !Array.isArray(thread.messages)) return;
  for (const m of thread.messages) {
    if (!m || !m.role || !m.content) continue;
    if (m.role !== 'user' && m.role !== 'assistant') continue;
    history.push({ role: m.role, content: m.content });
  }
}

function loadThreadMessages(thread) {
  if (!thread) return;

  chatMessages.innerHTML = '';

  // Render messages WITHOUT mutating storage/history through appendMessage(persist=false)
  if (Array.isArray(thread.messages) && thread.messages.length) {
    thread.messages.forEach((msg) => {
      const bubble = createMessageBubble(msg.role, msg.content);
      chatMessages.appendChild(bubble);
    });
  } else {
    const bubble = createMessageBubble(
      'assistant',
      'Hi! Ask me about sustainable materials, cost savings, CO₂ trade-offs, or how to export reports.'
    );
    chatMessages.appendChild(bubble);
  }

  // Rebuild in-memory history so backend gets real context on next send
  rebuildHistoryFromThread(thread);

  scrollToBottom();
}

function selectThread(id) {
  const thread = getThreadById(id);
  if (!thread) return;
  currentThreadId = String(thread.id);
  loadThreadMessages(thread);
  renderThreadsList();
  saveThreads();
}

function newChat() {
  const id = generateId();
  const createdAt = new Date().toISOString();
  const thread = {
    id,
    title: 'New chat',
    messages: [],
    createdAt,
  };
  threads.unshift(thread);
  currentThreadId = id;
  renderThreadsList();
  loadThreadMessages(thread);
  saveThreads();
}

function deleteThread(id) {
  const idx = threads.findIndex((t) => String(t.id) === String(id));
  if (idx === -1) return;

  threads.splice(idx, 1);

  if (String(currentThreadId) === String(id)) {
    if (threads.length) {
      currentThreadId = threads[0].id;
      loadThreadMessages(threads[0]);
    } else {
      newChat();
      return;
    }
  }

  renderThreadsList();
  saveThreads();
}

function appendMessage(role, content, persist = true) {
  const bubble = createMessageBubble(role, content);
  chatMessages.appendChild(bubble);
  scrollToBottom();

  // Speech synthesis for assistant
  if (role === 'assistant' && voiceEnabled && typeof window !== 'undefined' && 'speechSynthesis' in window) {
    try {
      window.speechSynthesis.cancel();
      const utter = new SpeechSynthesisUtterance(String(content));
      utter.lang = 'en-US';
      window.speechSynthesis.speak(utter);
    } catch (err) {
      console.warn('Speech synthesis failed:', err);
    }
  }

  if (persist) {
    const thread = getThreadById(currentThreadId);
    if (thread) {
      thread.messages = thread.messages || [];
      thread.messages.push({ role, content });
      updateThreadTitle(thread);
      saveThreads();
    }
    history.push({ role, content });
  }
}

function setSendingState(sending) {
  isSending = sending;
  if (chatInput) chatInput.disabled = sending;
  const sendBtn = chatForm?.querySelector('button[type="submit"]');
  if (sendBtn) sendBtn.disabled = sending;
  if (chatClear) chatClear.disabled = sending;
  if (newChatBtn) newChatBtn.disabled = sending;

  if (chatThreadsList) {
    chatThreadsList.querySelectorAll('button').forEach((btn) => {
      btn.disabled = sending;
    });
  }
}

async function sendMessage(question) {
  ensureCurrentThread();

  appendMessage('user', question);
  setSendingState(true);

  try {
    // Send last N messages only
    const historyToSend = history.slice(-MAX_HISTORY_TO_SEND);

    const data = await sendChatMessage(question, historyToSend);
    const answer = data?.answer || 'I was unable to find an answer right now.';
    appendMessage('assistant', answer);
  } catch (error) {
    const msg = String(error?.message || error);
    if (msg.includes('401') || msg.toLowerCase().includes('invalid') || msg.toLowerCase().includes('expired')) {
      appendMessage('assistant', 'Your session expired. Please log in again.', false);
      logout();
      window.location.href = 'login.html';
      return;
    }
    appendMessage('assistant', 'Sorry, I could not process that question. Please try again.', false);
    console.error('Chat error:', error);
  } finally {
    setSendingState(false);
  }
}

function clearCurrentChat() {
  const thread = getThreadById(currentThreadId);
  if (thread) {
    thread.messages = [];
    saveThreads();
  }
  history = [];
  chatMessages.innerHTML = '';
  appendMessage('assistant', 'Chat cleared. You can start with a new question.', true);
  chatInput.value = '';
  chatInput.focus();
}

document.addEventListener('DOMContentLoaded', () => {
  if (!requireAuthOrRedirect()) return;

  mountNavbarProfileChip();
  mountLogoutButton();

  loadThreads();

  if (!threads.length) {
    newChat();
  } else {
    const cur = currentThreadId && getThreadById(currentThreadId);
    if (cur) {
      loadThreadMessages(cur);
    } else {
      currentThreadId = threads[0].id;
      loadThreadMessages(threads[0]);
    }
    renderThreadsList();
    saveThreads();
  }

  chatForm.addEventListener('submit', (event) => {
    event.preventDefault();
    if (isSending) return;
    const question = chatInput.value.trim();
    if (!question) {
      chatInput.focus();
      return;
    }
    chatInput.value = '';
    sendMessage(question);
  });

  if (chatClear) {
    chatClear.addEventListener('click', () => {
      clearCurrentChat();
    });
  }

  if (newChatBtn) {
    newChatBtn.addEventListener('click', () => {
      if (isSending) return;
      newChat();
    });
  }

  // Voice output toggle
  const voiceToggle = document.getElementById('voiceToggleBtn');
  if (voiceToggle) {
    voiceToggle.addEventListener('click', () => {
      voiceEnabled = !voiceEnabled;
      voiceToggle.setAttribute('aria-pressed', String(voiceEnabled));
      const icon = voiceToggle.querySelector('i');
      if (icon) {
        icon.className = voiceEnabled ? 'bi bi-volume-up me-2' : 'bi bi-volume-mute me-2';
      }
    });
  }

  // Voice input: speech recognition
  const voiceBtn = document.getElementById('voiceInputBtn');
  if (voiceBtn) {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (SpeechRecognition) {
      recognition = new SpeechRecognition();
      recognition.lang = 'en-US';
      recognition.interimResults = false;
      recognition.maxAlternatives = 1;

      recognition.onresult = (event) => {
        try {
          const transcript = event.results[0][0].transcript.trim();
          if (transcript) {
            chatInput.value = '';
            sendMessage(transcript);
          }
        } catch (err) {
          console.warn('Voice transcription error:', err);
        }
      };

      recognition.onerror = (event) => {
        console.warn('Speech recognition error:', event.error);
      };

      voiceBtn.addEventListener('click', () => {
        if (isSending) return;
        try {
          recognition.start();
        } catch (err) {
          console.warn('Speech recognition start failed:', err);
        }
      });
    } else {
      voiceBtn.disabled = true;
      voiceBtn.setAttribute('title', 'Voice input is not supported in this browser.');
    }
  }
});
