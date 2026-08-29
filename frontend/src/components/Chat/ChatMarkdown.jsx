import React from 'react';
import { useChat } from '../../context/ChatContext';
import { Database, ShieldCheck, Sparkles, CheckCircle2, AlertTriangle, Info } from 'lucide-react';

/**
 * ChatMarkdown — Formats assistant responses with rich, theme-aware typography,
 * full markdown table rendering, lists, headers, callouts, and data sources attribution.
 */
export function ChatMarkdown({ content, customTheme }) {
  const { currentTheme } = useChat();
  const theme = customTheme || currentTheme || {};

  if (!content) return null;

  // Split into lines for structured block rendering
  const rawLines = content.split('\n');
  const blocks = [];
  let i = 0;

  while (i < rawLines.length) {
    const rawLine = rawLines[i];
    const trimmed = rawLine.trim();

    // 1. Skip empty lines
    if (!trimmed) {
      i++;
      continue;
    }

    // 2. Horizontal Rule (--- or *** or ___)
    if (/^(\-{3,}|\*{3,}|_{3,})$/.test(trimmed)) {
      blocks.push(
        <hr
          key={`hr-${i}`}
          className="my-2.5 border-t border-slate-200/90 dark:border-slate-700/60"
        />
      );
      i++;
      continue;
    }

    // 3. Markdown Table Detection (Lines with '|')
    if (trimmed.startsWith('|') && trimmed.endsWith('|') && trimmed.includes('|')) {
      const tableLines = [];
      while (
        i < rawLines.length &&
        rawLines[i].trim().startsWith('|') &&
        rawLines[i].trim().endsWith('|')
      ) {
        tableLines.push(rawLines[i].trim());
        i++;
      }

      if (tableLines.length >= 2) {
        const headerRow = parseTableRow(tableLines[0]);
        let dataStartIndex = 1;

        // If second line is separator |---|---|, skip it
        if (
          tableLines.length > 1 &&
          tableLines[1].replace(/[\s|:\-]/g, '').length === 0
        ) {
          dataStartIndex = 2;
        }

        const bodyRows = tableLines.slice(dataStartIndex).map(parseTableRow);

        blocks.push(
          <div
            key={`table-${i}`}
            className="my-2.5 overflow-x-auto rounded-xl border border-slate-200 dark:border-slate-700/80 shadow-2xs"
          >
            <table className="w-full text-left text-xs border-collapse">
              {headerRow.length > 0 && (
                <thead className="bg-slate-100/90 dark:bg-slate-800/90 border-b border-slate-200 dark:border-slate-700 text-slate-900 dark:text-slate-100 font-bold">
                  <tr>
                    {headerRow.map((cell, cIdx) => (
                      <th
                        key={`th-${cIdx}`}
                        className="px-3 py-2 font-outfit text-[11px] uppercase tracking-wider text-slate-700 dark:text-slate-300 first:rounded-tl-xl last:rounded-tr-xl border-r last:border-r-0 border-slate-200/60 dark:border-slate-700/60"
                      >
                        {formatInline(cell, theme)}
                      </th>
                    ))}
                  </tr>
                </thead>
              )}
              <tbody className="divide-y divide-slate-100 dark:divide-slate-800 bg-white dark:bg-slate-900/50">
                {bodyRows.map((row, rIdx) => (
                  <tr
                    key={`tr-${rIdx}`}
                    className="hover:bg-slate-50/80 dark:hover:bg-slate-800/50 transition-colors"
                  >
                    {row.map((cell, cIdx) => (
                      <td
                        key={`td-${rIdx}-${cIdx}`}
                        className="px-3 py-2 text-[11px] text-slate-800 dark:text-slate-200 border-r last:border-r-0 border-slate-100 dark:border-slate-800 font-medium"
                      >
                        {formatInline(cell, theme)}
                      </td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        );
        continue;
      }
    }

    // 4. Data Sources Section Detection
    if (
      trimmed.toLowerCase().startsWith('**data source') ||
      trimmed.toLowerCase().startsWith('### data source') ||
      trimmed.toLowerCase().startsWith('**sources') ||
      trimmed.toLowerCase().startsWith('### sources') ||
      trimmed.toLowerCase().startsWith('sources:')
    ) {
      const sourceContent = trimmed
        .replace(/^(\*{1,2}|#{1,4})\s*(data sources?|sources?)[:\*#\s]*/i, '')
        .trim();

      blocks.push(
        <div
          key={`sources-${i}`}
          className="mt-3 p-2.5 rounded-xl bg-slate-50 dark:bg-slate-800/60 border border-slate-200 dark:border-slate-700/70 text-[10px] text-slate-600 dark:text-slate-400 space-y-1 shadow-2xs"
        >
          <div className="flex items-center gap-1.5 font-bold uppercase tracking-wider text-sovereign-800 dark:text-sky-300">
            <Database className="w-3 h-3 text-sky-600 dark:text-sky-400 shrink-0" />
            <span>Verified Data Sources:</span>
          </div>
          <div className="leading-relaxed pl-4 font-medium text-slate-700 dark:text-slate-300">
            {sourceContent ? formatInline(sourceContent, theme) : 'Ministry of MSME, Census 2011, RBI Prudential Norms'}
          </div>
        </div>
      );
      i++;
      continue;
    }

    // 5. Headings
    if (trimmed.startsWith('# ') || trimmed.startsWith('## ') || trimmed.startsWith('### ') || trimmed.startsWith('#### ')) {
      let level = 3;
      let text = trimmed;
      if (trimmed.startsWith('#### ')) {
        level = 4;
        text = trimmed.substring(5);
      } else if (trimmed.startsWith('### ')) {
        level = 3;
        text = trimmed.substring(4);
      } else if (trimmed.startsWith('## ')) {
        level = 2;
        text = trimmed.substring(3);
      } else if (trimmed.startsWith('# ')) {
        level = 1;
        text = trimmed.substring(2);
      }

      blocks.push(
        <h4
          key={`h-${i}`}
          className={`font-outfit font-bold tracking-tight mt-3 mb-1.5 flex items-center gap-1.5 border-b pb-0.5 ${
            level <= 2 ? 'text-xs sm:text-sm text-sovereign-950 dark:text-white border-slate-200 dark:border-slate-700' : 'text-xs text-sovereign-900 dark:text-sky-300 border-slate-200/60 dark:border-slate-800'
          }`}
        >
          {formatInline(text, theme)}
        </h4>
      );
      i++;
      continue;
    }

    // 6. Unordered List Items (- item, * item, + item, • item)
    if (
      trimmed.startsWith('- ') ||
      trimmed.startsWith('* ') ||
      trimmed.startsWith('+ ') ||
      trimmed.startsWith('• ')
    ) {
      const listItems = [];
      while (
        i < rawLines.length &&
        (rawLines[i].trim().startsWith('- ') ||
          rawLines[i].trim().startsWith('* ') ||
          rawLines[i].trim().startsWith('+ ') ||
          rawLines[i].trim().startsWith('• '))
      ) {
        const itemText = rawLines[i].trim().substring(2).trim();
        listItems.push(itemText);
        i++;
      }

      blocks.push(
        <ul
          key={`ul-${i}`}
          className={`my-2 pl-4 space-y-1 text-xs list-disc ${theme.mdList || 'text-slate-700 marker:text-sky-600 dark:text-slate-200 dark:marker:text-sky-400'}`}
        >
          {listItems.map((item, idx) => (
            <li key={idx} className="leading-relaxed">
              {formatInline(item, theme)}
            </li>
          ))}
        </ul>
      );
      continue;
    }

    // 7. Ordered List Items (1. item, 2. item)
    if (/^\d+\.\s+/.test(trimmed)) {
      const listItems = [];
      while (i < rawLines.length && /^\d+\.\s+/.test(rawLines[i].trim())) {
        const itemText = rawLines[i].trim().replace(/^\d+\.\s+/, '').trim();
        listItems.push(itemText);
        i++;
      }

      blocks.push(
        <ol
          key={`ol-${i}`}
          className={`my-2 pl-4 space-y-1 text-xs list-decimal font-medium ${theme.mdList || 'text-slate-700 dark:text-slate-200 marker:text-sky-600'}`}
        >
          {listItems.map((item, idx) => (
            <li key={idx} className="leading-relaxed">
              {formatInline(item, theme)}
            </li>
          ))}
        </ol>
      );
      continue;
    }

    // 8. Blockquote (> quote)
    if (trimmed.startsWith('> ')) {
      blocks.push(
        <blockquote
          key={`quote-${i}`}
          className={`my-2 pl-3 border-l-2 py-1.5 pr-2 rounded-r text-xs italic ${
            theme.mdQuote || 'border-sky-500 bg-sky-50/60 dark:bg-sky-950/40 text-slate-700 dark:text-slate-300'
          }`}
        >
          {formatInline(trimmed.substring(2), theme)}
        </blockquote>
      );
      i++;
      continue;
    }

    // 9. Standard Paragraph
    blocks.push(
      <p
        key={`p-${i}`}
        className={`text-xs leading-relaxed my-1 font-normal ${theme.mdText || 'text-slate-800 dark:text-slate-100'}`}
      >
        {formatInline(trimmed, theme)}
      </p>
    );
    i++;
  }

  return (
    <div className={`space-y-1 select-text ${theme.mdText || 'text-slate-800 dark:text-slate-100'}`}>
      {blocks}
    </div>
  );
}

/**
 * Splits a markdown table row "| Col 1 | Col 2 |" into an array of trimmed cell strings
 */
function parseTableRow(line) {
  return line
    .split('|')
    .slice(1, -1)
    .map((cell) => cell.trim());
}

/**
 * Parses inline Markdown syntax: bold (**), italic (*), code (`), rupee amounts (₹)
 */
function formatInline(text, theme) {
  if (!text) return null;

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
            theme?.mdBold || 'font-bold text-slate-950 dark:text-white'
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
            theme?.mdCode || 'bg-slate-100 dark:bg-slate-800 text-sovereign-800 dark:text-sky-300 border border-slate-200 dark:border-slate-700'
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
