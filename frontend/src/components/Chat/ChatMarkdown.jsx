import React from 'react';
import { useChat } from '../../context/ChatContext';

/**
 * ChatMarkdown — Formats assistant responses with rich, theme-aware typography.
 */
export function ChatMarkdown({ content, customTheme }) {
  const { currentTheme } = useChat();
  const theme = customTheme || currentTheme;

  if (!content) return null;

  // Split into lines for structured block rendering
  const lines = content.split('\n');
  const elements = [];
  let currentList = [];
  let listType = null; // 'ul' | 'ol'

  const flushList = () => {
    if (currentList.length > 0) {
      if (listType === 'ul') {
        elements.push(
          <ul
            key={`ul-${elements.length}`}
            className={`my-2 pl-4 space-y-1 text-xs list-disc ${theme.mdList || 'text-slate-700 marker:text-sky-600'}`}
          >
            {currentList.map((item, idx) => (
              <li key={idx} className="leading-relaxed">
                {formatInline(item, theme)}
              </li>
            ))}
          </ul>
        );
      } else {
        elements.push(
          <ol
            key={`ol-${elements.length}`}
            className={`my-2 pl-4 space-y-1 text-xs list-decimal font-medium ${theme.mdList || 'text-slate-700 marker:text-sky-600'}`}
          >
            {currentList.map((item, idx) => (
              <li key={idx} className="leading-relaxed">
                {formatInline(item, theme)}
              </li>
            ))}
          </ol>
        );
      }
      currentList = [];
      listType = null;
    }
  };

  for (let i = 0; i < lines.length; i++) {
    const rawLine = lines[i];
    const trimmed = rawLine.trim();

    if (!trimmed) {
      flushList();
      continue;
    }

    // Header 3 or 4: ### Header
    if (trimmed.startsWith('### ')) {
      flushList();
      elements.push(
        <h4
          key={`h3-${i}`}
          className={`font-outfit font-bold text-xs sm:text-sm mt-2.5 mb-1 flex items-center gap-1.5 border-b pb-0.5 ${
            theme.mdH3 || 'text-sovereign-900 border-slate-200'
          }`}
        >
          {formatInline(trimmed.substring(4), theme)}
        </h4>
      );
      continue;
    }

    // Header 2: ## Header
    if (trimmed.startsWith('## ')) {
      flushList();
      elements.push(
        <h3
          key={`h2-${i}`}
          className={`font-outfit font-extrabold text-sm mt-3 mb-1.5 flex items-center gap-1.5 border-b pb-1 ${
            theme.mdH2 || 'text-sovereign-950 border-slate-300'
          }`}
        >
          {formatInline(trimmed.substring(3), theme)}
        </h3>
      );
      continue;
    }

    // Unordered list item: - item or * item
    if (trimmed.startsWith('- ') || trimmed.startsWith('* ')) {
      if (listType !== 'ul') {
        flushList();
        listType = 'ul';
      }
      currentList.push(trimmed.substring(2));
      continue;
    }

    // Ordered list item: 1. item
    const matchOrdered = trimmed.match(/^(\d+)\.\s+(.*)$/);
    if (matchOrdered) {
      if (listType !== 'ol') {
        flushList();
        listType = 'ol';
      }
      currentList.push(matchOrdered[2]);
      continue;
    }

    // Blockquote: > text
    if (trimmed.startsWith('> ')) {
      flushList();
      elements.push(
        <blockquote
          key={`quote-${i}`}
          className={`my-2 pl-3 border-l-2 py-1 pr-2 rounded-r text-xs italic ${
            theme.mdQuote || 'border-sky-500 bg-sky-50/60 text-slate-700'
          }`}
        >
          {formatInline(trimmed.substring(2), theme)}
        </blockquote>
      );
      continue;
    }

    // Standard paragraph line
    flushList();
    elements.push(
      <p
        key={`p-${i}`}
        className={`text-xs leading-relaxed my-1 ${
          theme.mdText || 'text-slate-800'
        }`}
      >
        {formatInline(trimmed, theme)}
      </p>
    );
  }

  flushList();

  return <div className={`space-y-1 ${theme.mdText || 'text-slate-800'}`}>{elements}</div>;
}

/**
 * Parses inline Markdown syntax: bold (**), italic (*), code (`), rupee amounts (₹)
 */
function formatInline(text, theme) {
  if (!text) return null;

  // Regex splitting on code blocks `code`, bold **bold**, and italic *italic*
  const tokens = [];
  let remainder = text;
  let keyIndex = 0;

  const regex = /(\*\*[^*]+\*\*|`[^`]+`|\*[^*]+\*)/g;
  let lastIndex = 0;
  let match;

  while ((match = regex.exec(remainder)) !== null) {
    if (match.index > lastIndex) {
      tokens.push(
        <span key={`text-${keyIndex++}`}>
          {remainder.substring(lastIndex, match.index)}
        </span>
      );
    }

    const matchedStr = match[0];
    if (matchedStr.startsWith('**') && matchedStr.endsWith('**')) {
      tokens.push(
        <strong
          key={`bold-${keyIndex++}`}
          className={`tracking-tight ${
            theme?.mdBold || 'font-bold text-slate-950'
          }`}
        >
          {matchedStr.slice(2, -2)}
        </strong>
      );
    } else if (matchedStr.startsWith('`') && matchedStr.endsWith('`')) {
      tokens.push(
        <code
          key={`code-${keyIndex++}`}
          className={`font-mono text-[11px] px-1.5 py-0.5 rounded ${
            theme?.mdCode || 'bg-slate-100 text-sovereign-800 border border-slate-200'
          }`}
        >
          {matchedStr.slice(1, -1)}
        </code>
      );
    } else if (matchedStr.startsWith('*') && matchedStr.endsWith('*')) {
      tokens.push(
        <em key={`em-${keyIndex++}`} className="italic opacity-90">
          {matchedStr.slice(1, -1)}
        </em>
      );
    }

    lastIndex = regex.lastIndex;
  }

  if (lastIndex < remainder.length) {
    tokens.push(
      <span key={`text-${keyIndex++}`}>
        {remainder.substring(lastIndex)}
      </span>
    );
  }

  return tokens.length > 0 ? tokens : text;
}
