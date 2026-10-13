// Render existing Mermaid notes, retaining the source if a diagram is invalid.
(async () => {
  const codes = [...document.querySelectorAll('code.language-mermaid')];
  if (!codes.length || typeof mermaid === 'undefined') return;
  mermaid.initialize({startOnLoad:false, securityLevel:'strict', theme:'neutral', suppressErrorRendering:true});
  for (const [i, code] of codes.entries()) {
    try {
      const {svg, bindFunctions} = await mermaid.render(`note-diagram-${i}`, code.textContent);
      const block = document.createElement('div');
      block.className = 'diagram';
      block.innerHTML = svg;
      code.parentElement.replaceWith(block);
      bindFunctions?.(block);
    } catch (_) {
      const label = document.createElement('p');
      label.className = 'diagram-fallback';
      label.textContent = 'Diagram source (could not render automatically):';
      code.parentElement.before(label);
    }
  }
})();
