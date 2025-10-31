/**
 * Theme Switcher UI
 * Handles theme switching with session persistence
 */

class ThemeSwitcher {
  constructor() {
    this.currentTheme = null;
    this.themes = [];
    this.init();
  }

  async init() {
    await this.loadThemes();
    await this.loadCurrentTheme();
    this.setupEventListeners();
    console.log('[ThemeSwitcher] Initialized');
  }

  async loadThemes() {
    try {
      const response = await fetch('/api/theme/list');
      const data = await response.json();
      this.themes = data.themes;
    } catch (error) {
      console.error('[ThemeSwitcher] Error loading themes:', error);
      // Fallback themes
      this.themes = [
        { value: 'shadcn', name: 'Shadcn', description: 'Clean & Professional' },
        { value: 'cyberpunk', name: 'Cyberpunk', description: 'Neon & Matrix' },
        { value: 'military', name: 'Military C2', description: 'Tactical Command' }
      ];
    }
  }

  async loadCurrentTheme() {
    try {
      const response = await fetch('/api/theme');
      const data = await response.json();
      this.currentTheme = data.theme;
      this.updateUI();
    } catch (error) {
      console.error('[ThemeSwitcher] Error loading current theme:', error);
      this.currentTheme = 'shadcn';
    }
  }

  async switchTheme(themeValue) {
    if (themeValue === this.currentTheme) {
      console.log('[ThemeSwitcher] Already using theme:', themeValue);
      return;
    }

    try {
      const response = await fetch('/api/theme', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ theme: themeValue })
      });

      if (!response.ok) {
        throw new Error(`Theme switch failed: ${response.statusText}`);
      }

      const data = await response.json();

      if (data.success) {
        console.log('[ThemeSwitcher] Theme changed to:', data.name);

        // Show notification if available
        if (typeof Alpine !== 'undefined' && Alpine.store('notifications')) {
          Alpine.store('notifications').success(`Theme changed to ${data.name}`);
        }

        // Reload page to apply new theme
        setTimeout(() => {
          window.location.reload();
        }, 500);
      }
    } catch (error) {
      console.error('[ThemeSwitcher] Error switching theme:', error);

      // Show error notification
      if (typeof Alpine !== 'undefined' && Alpine.store('notifications')) {
        Alpine.store('notifications').error('Failed to switch theme');
      }
    }
  }

  updateUI() {
    // Update theme selector dropdown if exists
    const selector = document.getElementById('theme-selector');
    if (selector) {
      selector.value = this.currentTheme;
    }

    // Update any theme badges
    document.querySelectorAll('[data-theme-badge]').forEach(badge => {
      const theme = this.themes.find(t => t.value === this.currentTheme);
      if (theme) {
        badge.textContent = theme.name;
      }
    });
  }

  setupEventListeners() {
    // Theme selector dropdown
    const selector = document.getElementById('theme-selector');
    if (selector) {
      selector.addEventListener('change', (e) => {
        this.switchTheme(e.target.value);
      });
    }

    // Theme buttons (alternative UI)
    document.querySelectorAll('[data-theme-switch]').forEach(button => {
      button.addEventListener('click', (e) => {
        const themeValue = button.dataset.themeSwitch;
        this.switchTheme(themeValue);
      });
    });

    // Keyboard shortcut: Ctrl+Shift+T to toggle themes
    document.addEventListener('keydown', (e) => {
      if (e.ctrlKey && e.shiftKey && e.key === 'T') {
        e.preventDefault();
        this.cycleTheme();
      }
    });
  }

  cycleTheme() {
    const currentIndex = this.themes.findIndex(t => t.value === this.currentTheme);
    const nextIndex = (currentIndex + 1) % this.themes.length;
    const nextTheme = this.themes[nextIndex];
    this.switchTheme(nextTheme.value);
  }

  getThemeIcon(themeValue) {
    const icons = {
      'shadcn': 'bi-palette',
      'cyberpunk': 'bi-lightning',
      'military': 'bi-shield-shaded'
    };
    return icons[themeValue] || 'bi-palette';
  }

  getThemeColor(themeValue) {
    const colors = {
      'shadcn': '#e2e8f0',
      'cyberpunk': '#00ff00',
      'military': '#22c55e'
    };
    return colors[themeValue] || '#e2e8f0';
  }

  populateThemeSelector() {
    const selector = document.getElementById('theme-selector');
    if (!selector || selector.children.length > 0) return;

    this.themes.forEach(theme => {
      const option = document.createElement('option');
      option.value = theme.value;
      option.textContent = `${theme.name} - ${theme.description}`;
      if (theme.value === this.currentTheme) {
        option.selected = true;
      }
      selector.appendChild(option);
    });
  }

  createThemeSwitcherDropdown() {
    /**
     * Creates a theme switcher dropdown for injection into navbar
     * Returns HTML string
     */
    const options = this.themes.map(theme => `
      <option value="${theme.value}" ${theme.value === this.currentTheme ? 'selected' : ''}>
        ${theme.name} - ${theme.description}
      </option>
    `).join('');

    return `
      <div class="theme-switcher-container">
        <label for="theme-selector" class="text-muted small me-2">Theme:</label>
        <select id="theme-selector" class="form-select form-select-sm" style="width: auto; display: inline-block;">
          ${options}
        </select>
      </div>
    `;
  }

  createThemeSwitcherButtons() {
    /**
     * Creates theme switcher button group
     * Returns HTML string
     */
    const buttons = this.themes.map(theme => `
      <button
        class="btn btn-sm ${theme.value === this.currentTheme ? 'btn-primary' : 'btn-outline-secondary'}"
        data-theme-switch="${theme.value}"
        title="${theme.description}"
      >
        <i class="bi ${this.getThemeIcon(theme.value)}"></i>
        ${theme.name}
      </button>
    `).join('');

    return `
      <div class="btn-group btn-group-sm" role="group" aria-label="Theme switcher">
        ${buttons}
      </div>
    `;
  }
}

// Initialize theme switcher when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
  window.themeSwitcher = new ThemeSwitcher();
});

// Export for module usage
if (typeof module !== 'undefined' && module.exports) {
  module.exports = ThemeSwitcher;
}

console.log('[theme-switcher.js] Loaded');
