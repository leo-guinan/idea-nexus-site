(() => {
  const shell = document.getElementById('marvin-shell');
  if (!shell) return;
  const toggle = document.getElementById('marvin-toggle');
  const panel = document.getElementById('marvin-panel');
  const close = document.getElementById('marvin-close');
  const form = document.getElementById('marvin-form');
  const input = document.getElementById('marvin-input');
  const messages = document.getElementById('marvin-messages');
  const voiceButton = document.getElementById('marvin-voice');
  const voiceSurface = document.getElementById('marvin-voice-surface');
  const voiceStatus = document.getElementById('marvin-voice-status');
  let knowledge = null;
  let conversation = null;
  let Conversation = null;

  const normalize = (text) => text.toLowerCase().replace(/[^a-z0-9\s]/g, ' ');
  const page = {
    title: document.body.dataset.pageTitle || 'this page',
    kind: document.body.dataset.pageKind || 'page',
    summary: document.body.dataset.pageSummary || '',
    url: document.body.dataset.pageUrl || '/'
  };

  function openPanel() {
    panel.hidden = false;
    toggle.setAttribute('aria-expanded', 'true');
    input.focus();
  }
  function closePanel() {
    panel.hidden = true;
    toggle.setAttribute('aria-expanded', 'false');
  }
  function addMessage(text, role, source) {
    const item = document.createElement('div');
    item.className = `marvin-message marvin-message--${role}`;
    item.textContent = text;
    if (source) {
      const link = document.createElement('a');
      link.href = source.url;
      link.textContent = `Source: ${source.label}`;
      link.className = 'marvin-source';
      item.appendChild(document.createElement('br'));
      item.appendChild(link);
    }
    messages.appendChild(item);
    messages.scrollTop = messages.scrollHeight;
  }
  function answer(question) {
    if (!knowledge) return {text: 'Marvin is still reading the public knowledge base. Try again in a moment.'};
    const query = normalize(question);
    if (/(what is this|this page|summarize|summary|about this)/.test(query)) {
      return {text: `${page.title} is a ${page.kind} page. ${page.summary}`, source: {url: page.url, label: page.title}};
    }
    const terms = new Set(query.split(/\s+/).filter(Boolean));
    let best = null;
    let bestScore = 0;
    for (const entry of knowledge.entries) {
      let score = 0;
      for (const topic of entry.topics) {
        const topicTerms = normalize(topic).split(/\s+/);
        score += topicTerms.every(term => terms.has(term)) ? 3 : topicTerms.some(term => terms.has(term)) ? 1 : 0;
      }
      if (query.includes(normalize(entry.id))) score += 2;
      if (score > bestScore) { best = entry; bestScore = score; }
    }
    if (!best || bestScore < 1) return {text: knowledge.fallback};
    return {text: best.answer, source: {url: best.source, label: best.label}};
  }
  async function loadKnowledge() {
    try {
      const response = await fetch('/marvin.json', {cache: 'no-store'});
      knowledge = await response.json();
    } catch (_) {
      knowledge = {entries: [], fallback: 'The public knowledge base is unavailable. The page is still readable; the machine is the part having a bad day.'};
    }
  }
  function setVoiceStatus(text) {
    voiceSurface.hidden = false;
    voiceStatus.textContent = text;
  }
  async function startVoiceAgent() {
    if (!knowledge || !knowledge.agent_id) {
      voiceButton.textContent = 'Voice guide is not configured';
      voiceButton.disabled = true;
      return;
    }
    voiceButton.disabled = true;
    setVoiceStatus('Requesting microphone access…');
    try {
      await navigator.mediaDevices.getUserMedia({audio: true});
      if (!Conversation) {
        ({Conversation} = await import('https://esm.sh/@elevenlabs/client@latest'));
      }
      conversation = await Conversation.startSession({
        agentId: knowledge.agent_id,
        connectionType: 'webrtc',
        onConnect: () => { voiceButton.disabled = false; voiceButton.textContent = 'End voice session'; setVoiceStatus('Connected · Marvin is listening.'); },
        onDisconnect: () => { conversation = null; voiceButton.disabled = false; voiceButton.textContent = 'Talk with Marvin'; setVoiceStatus('Voice session ended.'); },
        onError: () => { conversation = null; voiceButton.disabled = false; voiceButton.textContent = 'Talk with Marvin'; setVoiceStatus('Voice session unavailable. Text Marvin is still here.'); },
        onModeChange: (mode) => setVoiceStatus(mode.mode === 'speaking' ? 'Marvin is speaking.' : 'Listening.'),
        onMessage: (message) => {
          if (message && message.message && message.source === 'agent') addMessage(message.message, 'assistant');
        }
      });
    } catch (error) {
      conversation = null;
      voiceButton.disabled = false;
      voiceButton.textContent = 'Talk with Marvin';
      setVoiceStatus(error?.name === 'NotAllowedError' ? 'Microphone access was declined. Text Marvin is still here.' : 'Voice session unavailable. Text Marvin is still here.');
    }
  }
  async function toggleVoiceAgent() {
    if (conversation) {
      await conversation.endSession();
      return;
    }
    await startVoiceAgent();
  }
  toggle.addEventListener('click', () => panel.hidden ? openPanel() : closePanel());
  close.addEventListener('click', closePanel);
  voiceButton.addEventListener('click', toggleVoiceAgent);
  form.addEventListener('submit', (event) => {
    event.preventDefault();
    const question = input.value.trim();
    if (!question) return;
    addMessage(question, 'user');
    input.value = '';
    const result = answer(question);
    window.setTimeout(() => addMessage(result.text, 'assistant', result.source), 120);
  });
  loadKnowledge();
})();
