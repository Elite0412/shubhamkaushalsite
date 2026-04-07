document.addEventListener('DOMContentLoaded', () => {
  document.querySelectorAll('form[action*="/admin/delete/"]').forEach((form) => {
    form.addEventListener('submit', (e) => {
      if (!window.confirm('Delete this note?')) {
        e.preventDefault();
      }
    });
  });
});
