<template>
  <div class="chat-panel">
    <!-- Welcome state -->
    <div v-if="!chat.hasMessages && !chat.streaming" class="welcome-state fade-in">
      <div class="welcome-icon">🩺</div>
      <h2>Explain <span class="topic-highlight">{{ topicTitle }}</span></h2>
      <p>Ask anything about this topic and I'll provide a structured, exam-ready explanation with textbook references.</p>

      <div class="quick-prompts">
        <span class="prompts-label">Quick prompts:</span>
        <div class="prompt-chips">
          <button
            v-for="prompt in quickPrompts"
            :key="prompt"
            class="prompt-chip"
            @click="sendQuick(prompt)"
          >{{ prompt }}</button>
        </div>
      </div>
    </div>

    <!-- Messages -->
    <div v-else class="messages-container" ref="messagesEl">
      <TransitionGroup name="message" tag="div" class="messages-list">
        <div
          v-for="(msg, i) in chat.messages"
          :key="i"
          class="message"
          :class="msg.role"
        >
          <div v-if="msg.role === 'user'" class="msg-user">
            <div class="msg-bubble user-bubble">{{ msg.content }}</div>
            <div class="msg-avatar user-avatar">You</div>
          </div>
          <div v-else-if="msg.role === 'assistant'" class="msg-assistant">
            <div class="msg-avatar ai-avatar">🩺</div>
            <div class="msg-bubble ai-bubble">
              <div class="markdown-content" v-html="renderMarkdown(msg.content)"></div>
            </div>
          </div>
          <div v-else-if="msg.role === 'error'" class="msg-error">
            <span>⚠️ {{ msg.content }}</span>
          </div>
        </div>
      </TransitionGroup>

      <!-- Streaming message -->
      <div v-if="chat.streaming" class="message assistant streaming-msg fade-in">
        <div class="msg-avatar ai-avatar">🩺</div>
        <div class="msg-bubble ai-bubble">
          <div v-if="chat.streamingContent" class="markdown-content cursor-blink" v-html="renderMarkdown(chat.streamingContent)"></div>
          <div v-else class="typing-indicator">
            <span></span><span></span><span></span>
          </div>
        </div>
      </div>
    </div>

    <!-- Input Bar -->
    <div class="input-bar">
      <div class="input-wrap">
        <textarea
          id="chat-input"
          v-model="userInput"
          class="input chat-textarea"
          :placeholder="`Ask about ${topicTitle}...`"
          :disabled="chat.streaming"
          @keydown.enter.exact.prevent="sendMessage"
          @keydown.enter.shift.exact="() => {}"
          rows="1"
          ref="inputEl"
          @input="autoResize"
        ></textarea>
        <button
          id="chat-send-btn"
          class="send-btn btn btn-primary"
          :disabled="!userInput.trim() || chat.streaming"
          @click="sendMessage"
        >
          <span v-if="chat.streaming" class="spinner" style="width:16px;height:16px"></span>
          <span v-else>↑</span>
        </button>
      </div>
      <div class="input-hint">Enter to send · Shift+Enter for new line</div>
    </div>
  </div>
</template>

<script setup>
import { ref, watch, nextTick, computed } from 'vue'
import { marked } from 'marked'
import { useChatStore } from '@/stores/chat'

const props = defineProps({
  topicId: String,
  topicTitle: String
})

const chat = useChatStore()
const userInput = ref('')
const messagesEl = ref(null)
const inputEl = ref(null)

const quickPrompts = computed(() => [
  `Explain ${props.topicTitle} comprehensively`,
  `What are the key clinical features?`,
  `How do I diagnose ${props.topicTitle}?`,
  `What is the management protocol?`,
  `Common NEXT exam questions on this topic`
])

function renderMarkdown(text) {
  if (!text) return ''
  marked.setOptions({ breaks: true })
  return marked.parse(text)
}

async function sendMessage() {
  const msg = userInput.value.trim()
  if (!msg || chat.streaming) return
  userInput.value = ''
  if (inputEl.value) { inputEl.value.style.height = 'auto' }

  await chat.sendMessage(props.topicId, msg)
}

function sendQuick(prompt) {
  userInput.value = prompt
  sendMessage()
}

function autoResize() {
  const el = inputEl.value
  if (!el) return
  el.style.height = 'auto'
  el.style.height = Math.min(el.scrollHeight, 160) + 'px'
}

// Scroll to bottom on new messages
watch(() => chat.messages.length, () => {
  nextTick(() => scrollBottom())
})
watch(() => chat.streamingContent, () => {
  nextTick(() => scrollBottom())
})

function scrollBottom() {
  const el = messagesEl.value
  if (el) el.scrollTop = el.scrollHeight
}

// Reset when topic changes
watch(() => props.topicId, () => {
  chat.reset()
})
</script>

<style scoped>
.chat-panel {
  display: flex;
  flex-direction: column;
  height: 100%;
  overflow: hidden;
}

/* Welcome */
.welcome-state {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  text-align: center;
  padding: 48px 32px;
  gap: 16px;
}
.welcome-icon { font-size: 3rem; filter: drop-shadow(0 0 16px rgba(20,184,166,0.5)); }
.welcome-state h2 { font-size: 1.5rem; font-weight: 700; }
.topic-highlight { color: var(--teal-400); }
.welcome-state p { color: var(--text-secondary); max-width: 400px; font-size: 0.9rem; }

.quick-prompts { width: 100%; max-width: 500px; }
.prompts-label { font-size: 0.75rem; color: var(--text-muted); text-transform: uppercase; letter-spacing: 0.08em; font-weight: 600; display: block; margin-bottom: 10px; }
.prompt-chips { display: flex; flex-wrap: wrap; gap: 8px; justify-content: center; }
.prompt-chip {
  padding: 7px 14px;
  background: var(--bg-input);
  border: 1px solid var(--border-default);
  border-radius: 999px;
  color: var(--text-secondary);
  font-size: 0.8rem;
  cursor: pointer;
  transition: var(--transition);
}
.prompt-chip:hover { border-color: var(--teal-500); color: var(--teal-400); background: rgba(20,184,166,0.08); }

/* Messages */
.messages-container {
  flex: 1;
  overflow-y: auto;
  padding: 24px;
  display: flex;
  flex-direction: column;
}
.messages-list { display: flex; flex-direction: column; gap: 20px; }

.message { animation: fadeInUp 0.3s ease; }

.msg-user { display: flex; align-items: flex-start; gap: 12px; justify-content: flex-end; }
.msg-assistant { display: flex; align-items: flex-start; gap: 12px; }
.msg-error {
  background: rgba(239,68,68,0.1);
  border: 1px solid rgba(239,68,68,0.3);
  border-radius: var(--radius-md);
  padding: 12px 16px;
  font-size: 0.875rem;
  color: var(--red-400);
}

.msg-avatar {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  font-size: 0.75rem;
  font-weight: 700;
}
.user-avatar { background: var(--blue-600); color: #fff; }
.ai-avatar { background: rgba(20,184,166,0.15); font-size: 1.1rem; border: 1px solid rgba(20,184,166,0.3); }

.msg-bubble {
  max-width: 75%;
  border-radius: var(--radius-lg);
  padding: 14px 18px;
  font-size: 0.875rem;
  line-height: 1.7;
}
.user-bubble {
  background: var(--blue-600);
  color: #fff;
  border-bottom-right-radius: 4px;
}
.ai-bubble {
  background: var(--bg-card);
  border: 1px solid var(--border-default);
  border-bottom-left-radius: 4px;
  width: 100%;
  max-width: 100%;
}

.streaming-msg .msg-bubble { animation: pulse-glow 2s infinite; }

/* Typing indicator */
.typing-indicator { display: flex; gap: 4px; align-items: center; padding: 4px 0; }
.typing-indicator span {
  width: 7px; height: 7px;
  background: var(--teal-400);
  border-radius: 50%;
  animation: typing-bounce 1.2s infinite ease-in-out;
}
.typing-indicator span:nth-child(2) { animation-delay: 0.2s; }
.typing-indicator span:nth-child(3) { animation-delay: 0.4s; }
@keyframes typing-bounce {
  0%, 80%, 100% { transform: translateY(0); opacity: 0.4; }
  40% { transform: translateY(-6px); opacity: 1; }
}

/* Input bar */
.input-bar {
  border-top: 1px solid var(--border-default);
  padding: 16px 24px;
  background: var(--bg-secondary);
}
.input-wrap { display: flex; gap: 12px; align-items: flex-end; }
.chat-textarea {
  flex: 1;
  resize: none;
  min-height: 44px;
  max-height: 160px;
  font-size: 0.9rem;
  padding: 10px 16px;
  line-height: 1.5;
  overflow-y: auto;
}
.send-btn {
  width: 44px;
  height: 44px;
  padding: 0;
  border-radius: 50%;
  font-size: 1.1rem;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}
.input-hint { font-size: 0.7rem; color: var(--text-muted); margin-top: 6px; text-align: right; }

/* Transitions */
.message-enter-active { animation: fadeInUp 0.3s ease; }
.message-leave-active { animation: fadeIn 0.2s ease reverse; }
</style>
