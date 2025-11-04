// API Configuration
// Set window.API_URL in config.js or it defaults to localhost
const API_URL = window.API_URL || 'http://localhost:8000';

// State
let conversationHistory = JSON.parse(localStorage.getItem('conversationHistory') || '[]');
let expandedIndex = null; // Track which conversation is expanded

// DOM Elements
const queryInput = document.getElementById('queryInput');
const searchBtn = document.getElementById('searchBtn');
const loading = document.getElementById('loading');
const errorDiv = document.getElementById('error');
const answerSection = document.getElementById('answerSection');
const answerDiv = document.getElementById('answer');
const citationsDiv = document.getElementById('citations');
const historyDiv = document.getElementById('history');

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    renderHistory();
    
    // Enter key support
    queryInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            handleQuery();
        }
    });
    
    // Make sure we start in new query view
    document.getElementById('newQueryView').classList.remove('hidden');
    document.getElementById('expandedView').classList.add('hidden');
});

// Handle query
async function handleQuery() {
    const query = queryInput.value.trim();
    if (!query) return;

    // Disable input and show loading
    queryInput.disabled = true;
    searchBtn.disabled = true;
    loading.classList.remove('hidden');
    errorDiv.classList.add('hidden');
    answerSection.classList.add('hidden');

    try {
        const response = await fetch(`${API_URL}/query`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ query }),
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const data = await response.json();
        
        // Save to history
        const qaEntry = {
            question: query,
            answer: data.answer,
            sources: data.sources,
            timestamp: new Date().toISOString(),
        };
        conversationHistory.unshift(qaEntry);
        // Keep only last 10
        if (conversationHistory.length > 10) {
            conversationHistory = conversationHistory.slice(0, 10);
        }
        localStorage.setItem('conversationHistory', JSON.stringify(conversationHistory));
        renderHistory();

        // Display answer (make sure we're in new query view)
        document.getElementById('newQueryView').classList.remove('hidden');
        document.getElementById('expandedView').classList.add('hidden');
        displayAnswer(data.answer, data.sources, false);
        queryInput.value = '';

    } catch (err) {
        errorDiv.textContent = `Error: ${err.message}. Make sure the API is running at ${API_URL}`;
        errorDiv.classList.remove('hidden');
    } finally {
        queryInput.disabled = false;
        searchBtn.disabled = false;
        loading.classList.add('hidden');
    }
}

// Display answer with citations
function displayAnswer(answer, sources, isExpanded = false) {
    const prefix = isExpanded ? 'expanded-' : '';
    const answerElement = isExpanded ? document.getElementById('expandedAnswer') : answerDiv;
    const citationsElement = isExpanded ? document.getElementById('expandedCitations') : citationsDiv;
    
    // Build citation mapping
    const citationToIndex = {};
    sources.forEach((src, idx) => {
        const i = idx + 1;
        const m = src.metadata || {};
        const title = m.title || m.filename || '';
        const page = m.page_number;
        
        if (page) {
            citationToIndex[`[${title}, p. ${page}]`] = i;
            citationToIndex[`[${title}, p.${page}]`] = i;
        }
        citationToIndex[`[${title}]`] = i;
    });

    // Replace citations with clickable links
    let displayAnswerText = answer;
    const citationPattern = /\[[^\]]+?\]/g;
    
    displayAnswerText = displayAnswerText.replace(citationPattern, (match) => {
        // Try to find matching citation
        for (const [key, num] of Object.entries(citationToIndex)) {
            if (key === match || match.includes(key.replace(/[\[\]]/g, ''))) {
                const citationId = isExpanded ? `cite-hist-${expandedIndex}-${num}` : `cite-new-${num}`;
                return `<a href="#${citationId}" class="citation-link" onclick="scrollToCitation(${num}, ${isExpanded}, ${expandedIndex || 0}); return false;">${match}</a>`;
            }
        }
        return match;
    });

    answerElement.innerHTML = displayAnswerText;
    
    if (!isExpanded) {
        answerSection.classList.remove('hidden');
    }

    // Display citations
    citationsElement.innerHTML = '';
    sources.forEach((src, idx) => {
        const i = idx + 1;
        const m = src.metadata || {};
        const title = m.title || m.filename || '';
        const page = m.page_number;
        const sourceText = src.text || '';
        
        const citationEl = document.createElement('div');
        citationEl.id = isExpanded ? `cite-hist-${expandedIndex}-${i}` : `cite-new-${i}`;
        citationEl.className = 'citation';
        
        const preview = bestSnippet(answer, sourceText, 140);
        
        citationEl.innerHTML = `
            <div class="citation-header">
                <strong>[${i}]</strong> ${escapeHtml(title)}${page ? `, p. ${page}` : ''}
            </div>
            <div class="citation-preview">${escapeHtml(preview)}</div>
            <button class="citation-toggle" onclick="toggleCitation(${i}, ${isExpanded})">
                View full source
            </button>
            <div class="citation-full" id="citation-full-${isExpanded ? 'hist' : 'new'}-${i}">
                ${escapeHtml(sourceText).replace(/\n/g, '<br>')}
            </div>
        `;
        
        citationsElement.appendChild(citationEl);
    });
}

// Scroll to citation
function scrollToCitation(num, isExpanded = false, histIndex = null) {
    const citationId = isExpanded ? `cite-hist-${histIndex}-${num}` : `cite-new-${num}`;
    const citationEl = document.getElementById(citationId);
    if (citationEl) {
        citationEl.scrollIntoView({ behavior: 'smooth', block: 'center' });
        citationEl.classList.add('highlight');
        setTimeout(() => {
            citationEl.classList.remove('highlight');
        }, 2000);
    }
}

// Toggle citation full text
function toggleCitation(num, isExpanded = false) {
    const prefix = isExpanded ? 'hist' : 'new';
    const fullEl = document.getElementById(`citation-full-${prefix}-${num}`);
    const toggleBtn = fullEl.previousElementSibling;
    
    if (fullEl.classList.contains('show')) {
        fullEl.classList.remove('show');
        toggleBtn.textContent = 'View full source';
    } else {
        fullEl.classList.add('show');
        toggleBtn.textContent = 'Hide full source';
    }
}

// Best snippet function (simplified version)
function bestSnippet(answerText, sourceText, maxLen = 140) {
    try {
        const sentences = sourceText.split(/[.!?]+\s+/).filter(s => s.trim());
        if (!sentences.length) {
            return sourceText.length > maxLen ? sourceText.substring(0, maxLen) + '...' : sourceText;
        }

        const answerWords = new Set(answerText.toLowerCase().match(/\w+/g) || []);
        let best = sentences[0];
        let bestScore = 0;

        sentences.forEach(sent => {
            const sentWords = new Set(sent.toLowerCase().match(/\w+/g) || []);
            const intersection = new Set([...answerWords].filter(w => sentWords.has(w)));
            const union = new Set([...answerWords, ...sentWords]);
            const score = union.size > 0 ? intersection.size / union.size : 0;
            
            if (score > bestScore) {
                bestScore = score;
                best = sent;
            }
        });

        return best.length > maxLen ? best.substring(0, maxLen) + '...' : best;
    } catch (e) {
        return sourceText.length > maxLen ? sourceText.substring(0, maxLen) + '...' : sourceText;
    }
}

// Render history (showing last 3, reversed)
function renderHistory() {
    if (conversationHistory.length === 0) {
        historyDiv.innerHTML = '<div class="history-empty">No previous questions yet</div>';
        return;
    }

    // Show last 3, reversed (most recent first)
    const recentHistory = conversationHistory.slice(-3).reverse();
    
    historyDiv.innerHTML = recentHistory.map((qa, displayIdx) => {
        // Calculate actual index in full history (from end)
        const actualIdx = conversationHistory.length - 1 - displayIdx;
        const question = qa.question.length > 80 ? qa.question.substring(0, 80) + '...' : qa.question;
        return `
            <div class="history-item-wrapper">
                <button class="history-item" onclick="loadHistoryItem(${actualIdx})">
                    <div class="history-item-question">Q: ${escapeHtml(question)}</div>
                </button>
                <button class="history-delete-btn" onclick="deleteHistoryItem(${actualIdx}, event)" title="Delete this conversation">
                    🗑️
                </button>
            </div>
        `;
    }).join('');
}

// Load history item (expanded view)
function loadHistoryItem(idx) {
    expandedIndex = idx;
    const qa = conversationHistory[idx];
    
    // Hide new query view, show expanded view
    document.getElementById('newQueryView').classList.add('hidden');
    document.getElementById('expandedView').classList.remove('hidden');
    
    // Display question
    document.getElementById('expandedQuestion').textContent = qa.question;
    
    // Display answer and citations
    displayAnswer(qa.answer, qa.sources, true);
    
    // Update delete button
    document.getElementById('expandedDeleteBtn').setAttribute('data-index', idx);
}

// Back to new query
function backToNewQuery() {
    expandedIndex = null;
    document.getElementById('newQueryView').classList.remove('hidden');
    document.getElementById('expandedView').classList.add('hidden');
    answerSection.classList.add('hidden');
}

// Delete history item
function deleteHistoryItem(idx, event) {
    event.stopPropagation();
    if (confirm('Delete this conversation?')) {
        conversationHistory.splice(idx, 1);
        localStorage.setItem('conversationHistory', JSON.stringify(conversationHistory));
        
        // If we deleted the expanded item, go back to new query
        if (expandedIndex === idx) {
            backToNewQuery();
        } else if (expandedIndex !== null && expandedIndex > idx) {
            // Adjust expanded index if we deleted something before it
            expandedIndex--;
        }
        
        renderHistory();
    }
}

// Delete expanded conversation
function deleteExpandedConversation() {
    const idx = expandedIndex;
    if (idx !== null && idx !== undefined && confirm('Delete this conversation?')) {
        conversationHistory.splice(idx, 1);
        localStorage.setItem('conversationHistory', JSON.stringify(conversationHistory));
        backToNewQuery();
        renderHistory();
    }
}

// Escape HTML
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

