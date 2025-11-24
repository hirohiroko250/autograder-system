// Enhance Django admin UI interactions
(function () {
  const DAY_LABELS = ['日', '月', '火', '水', '木', '金', '土'];

  function updateCalendarLabels() {
    document.querySelectorAll('.calendarbox table.calendar').forEach((calendar) => {
      const headerCells = calendar.querySelectorAll('thead tr:last-child th');
      headerCells.forEach((th, index) => {
        if (DAY_LABELS[index]) {
          th.textContent = DAY_LABELS[index];
          th.classList.remove('is-saturday', 'is-sunday');
          if (index === 0) th.classList.add('is-sunday');
          if (index === 6) th.classList.add('is-saturday');
        }
      });

      calendar.querySelectorAll('tbody tr').forEach((row) => {
        row.querySelectorAll('td').forEach((td, index) => {
          td.classList.remove('is-saturday', 'is-sunday');
          if (td.classList.contains('noday')) return;
          if (index === 0) td.classList.add('is-sunday');
          if (index === 6) td.classList.add('is-saturday');
        });
      });
    });
  }

  document.addEventListener('DOMContentLoaded', () => {
    updateCalendarLabels();

    // React to pop-up calendar interactions
    document.body.addEventListener('click', (event) => {
      const target = event.target;
      if (target instanceof HTMLElement && target.closest('.calendarbox') && target.tagName === 'A') {
        requestAnimationFrame(updateCalendarLabels);
      }
    });
  });
})();
