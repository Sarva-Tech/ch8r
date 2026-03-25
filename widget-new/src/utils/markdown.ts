import MarkdownIt from 'markdown-it';
import hljs from 'highlight.js';

const md = new MarkdownIt({
  breaks: true,
  linkify: true,
  typographer: true,
  html: true,
  highlight: function (str: string, lang: string) {
    if (lang && hljs.getLanguage(lang)) {
      try {
        return hljs.highlight(str, { language: lang }).value;
      } catch (__) {}
    }
    return '';
  }
});

export function preprocessMarkdown(text: string): string {
  let processed = text;

  const protectedTexts: string[] = [];

  processed = processed.replace(/```[^`]+```/g, (match) => {
    const placeholder = `__PROTECTED_${protectedTexts.length}__`;
    protectedTexts.push(match);
    return placeholder;
  });

  processed = processed.replace(/`[^`]+`/g, (match) => {
    const placeholder = `__PROTECTED_${protectedTexts.length}__`;
    protectedTexts.push(match);
    return placeholder;
  });

  processed = processed.replace(/\*\*([^*]+)\*\*/g, (match, content) => {
    const placeholder = `__PROTECTED_${protectedTexts.length}__`;
    protectedTexts.push(`**${content}**`);
    return placeholder;
  });

  processed = processed.replace(/\b\w+-\w+\b/g, (match) => {
    const placeholder = `__PROTECTED_${protectedTexts.length}__`;
    protectedTexts.push(match);
    return placeholder;
  });

  processed = processed.replace(/:\s*-\s*/g, ':\n\n- ');

  processed = processed.replace(/([.!?])\s*-\s*/g, '$1\n\n- ');

  processed = processed.replace(/([a-z.!?])\s*-\s*/g, '$1\n\n- ');

  protectedTexts.forEach((content, index) => {
    processed = processed.replace(`__PROTECTED_${index}__`, content);
  });
  
  return processed;
}

export function renderMarkdown(text: string): string {
  const processed = preprocessMarkdown(text);
  return md.render(processed);
}
