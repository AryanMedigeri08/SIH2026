import React from 'react';

/**
 * ChatMarkdown — Formats assistant responses with rich, readable typography.
 */
export function ChatMarkdown({ content }) {
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
          <ul key={`ul-${elements.length}`} className="my-2 pl-4 space-y-1 text-xs text-slate-200 list-disc marker:text-cyan-400">
            {currentList.map((item, idx) => (
              <li key={idx} className="leading-relaxed">
                {formatInline(item)}
              </li>
            ))}
          </ul>
        );
      } else {
        elements.push(
          <ol key={`ol-${elements.length}`} className="my-2 pl-4 space-y-1 text-xs text-slate-200 list-decimal marker:text-cyan-400 font-medium">
            {currentList.map((item, idx) => (
              <li key={idx} className="leading-relaxed">
                {formatInline(item)}
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
        <h4 key={`h3-${i}`} className="font-outfit font-bold text-sm text-cyan-300 mt-2.5 mb-1 flex items-center gap-1.5 border-b border-slate-700/50 pb-0.5">
          {formatInline(trimmed.substring(4))}
        </h4>
      );
      continue;
    }

    // Header 2: ## Header
    if (trimmed.startsWith('## ')) {
      flushList();
      elements.push(
        <h3 key={`h2-${i}`} className="font-outfit font-extrabold text-sm text-slate-100 mt-3 mb-1.5 flex items-center gap-1.5 border-b border-slate-700 pb-1">
          {formatInline(trimmed.substring(3))}
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
        <blockquote key={`quote-${i}`} className="my-2 pl-3 border-l-2 border-cyan-500 bg-slate-800/40 py-1 pr-2 rounded-r text-xs italic text-slate-300">
          {formatInline(trimmed.substring(2))}
        </blockquote>
      );
      continue;
    }

    // Standard paragraph line
    flushList();
    elements.push(
      <p key={`p-${i}`} className="text-xs text-slate-200 leading-relaxed my-1">
        {formatInline(trimmed)}
      </p>
    );
  }

  flushList();

  return <div className="space-y-1 text-slate-100">{elements}</div>;
}

/**
 * Parses inline Markdown syntax: bold (**), italic (*), code (`), rupee amounts (₹)
 */
function formatInline(text) {
  if (!text) return null;

  // Regex splitting on code blocks `code`, bold **bold**, and italic *italic*
  const tokens = [];
  let remainder = text;
  let keyIndex = 0;

  // Tokenize bold **...** and `...`
  const regex = /(\*\*[^*]+\*\*|`[^`]+`|\*[^*]+\*)/g;
  let lastIndex = 0;
  let match;

  while ((match = regex.exec(remainder)) !== null) {
    // Push preceding normal text
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
        <strong key={`bold-${keyIndex++}`} className="font-bold text-slate-100 tracking-wide">
          {matchedStr.slice(2, -2)}
        </strong>
      );
    } else if (matchedStr.startsWith('`') && matchedStr.endsWith('`')) {
      tokens.push(
        <code key={`code-${keyIndex++}`} className="font-mono text-[11px] bg-slate-800 text-cyan-300 px-1.5 py-0.5 rounded border border-slate-700">
          {matchedStr.slice(1, -1)}
        </code>
      );
    } else if (matchedStr.startsWith('*') && matchedStr.endsWith('*')) {
      tokens.push(
        <em key={`em-${keyIndex++}`} className="italic text-slate-300">
          {matchedStr.slice(1, -1)}
        </em>
      );
    }

    lastIndex = regex.lastIndex;
  }

  // Push trailing text
  if (lastIndex < remainder.length) {
    tokens.push(
      <span key={`text-${keyIndex++}`}>
        {remainder.substring(lastIndex)}
      </span>
    );
  }

  return tokens.length > 0 ? tokens : text;
}
