
document.addEventListener('DOMContentLoaded', () => {
  document.querySelectorAll('a[href]').forEach((link) => {
    try {
      const url = new URL(link.href, window.location.href);

      if (url.hostname && url.hostname !== window.location.hostname) {
        link.target = '_blank';
        link.rel = 'noopener noreferrer';
      }
    } catch (error) {
      // Ignore invalid URLs and keep normal behavior
    }
  });
});

document.addEventListener('click', (event) => {
  const link = event.target.closest('a[href]');
  if (!link) return;

  const href = link.getAttribute('href') || '';

  if (
    href.startsWith('#') ||
    href.startsWith('mailto:') ||
    href.startsWith('tel:')
  ) {
    return;
  }

  try {
    const url = new URL(link.href, window.location.href);

    if (url.hostname && url.hostname !== window.location.hostname) {
      event.preventDefault();
      window.open(url.href, '_blank', 'noopener,noreferrer');
    }
  } catch (error) {
    // Ignore invalid URLs and let the browser handle them normally
  }
});
