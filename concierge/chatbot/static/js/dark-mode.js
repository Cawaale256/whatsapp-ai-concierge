/**
 * Dark Mode Toggle Script
 * Manages dark theme preference and applies it to the page
 */
document.addEventListener('DOMContentLoaded', function() {
  const darkModeToggle = document.getElementById('darkModeToggle');
  const body = document.body;

  // Check for saved dark mode preference
  const isDarkMode = localStorage.getItem('darkMode') === 'true';
  if (isDarkMode) {
    body.classList.add('dark-theme');
    if (darkModeToggle) {
      darkModeToggle.innerHTML = '<i class="bi bi-sun-fill"></i>';
    }
  }

  // Toggle dark mode on button click
  if (darkModeToggle) {
    darkModeToggle.addEventListener('click', function(e) {
      e.preventDefault();
      body.classList.toggle('dark-theme');
      const isNowDarkMode = body.classList.contains('dark-theme');
      localStorage.setItem('darkMode', isNowDarkMode);

      // Update icon
      if (isNowDarkMode) {
        darkModeToggle.innerHTML = '<i class="bi bi-sun-fill"></i>';
      } else {
        darkModeToggle.innerHTML = '<i class="bi bi-moon-fill"></i>';
      }
    });
  }
});
