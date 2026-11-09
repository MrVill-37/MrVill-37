(() => {
  const reduceMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  if (reduceMotion || !('IntersectionObserver' in window)) return;

  const revealTargets = [
    '.about-section .section-heading',
    '.about-content',
    '.work-heading',
    '.project-card',
    '.closing-panel'
  ].flatMap((selector) => Array.from(document.querySelectorAll(selector)));

  revealTargets.forEach((element) => element.classList.add('reveal-ready'));
  const observer = new IntersectionObserver((entries, currentObserver) => {
    entries.forEach((entry) => {
      if (!entry.isIntersecting) return;
      entry.target.classList.add('is-visible');
      currentObserver.unobserve(entry.target);
    });
  }, { threshold: 0.12, rootMargin: '0px 0px -24px 0px' });

  revealTargets.forEach((element) => observer.observe(element));
})();
