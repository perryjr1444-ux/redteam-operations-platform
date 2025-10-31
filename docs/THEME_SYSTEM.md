[8m# Theme System Documentation

## Overview

The Red Team application features a comprehensive theme switching system that allows users to seamlessly switch between three professionally-designed themes:

1. **Shadcn** - Clean, minimal, professional (default)
2. **Cyberpunk** - Neon glow, matrix aesthetic
3. **Military C2** - Tactical command & control

All themes support dark mode and are optimized for the red team operations interface.

## Architecture

### Backend Components

**`app/theme.py`** - Theme management system
- `Theme` enum - Defines available themes (SHADCN, CYBERPUNK, MILITARY)
- `THEME_CONFIG` dict - Configuration for each theme (CSS files, fonts, colors)
- `ThemeManager` class - Handles theme selection and persistence
- `get_theme_context()` - Context processor for injecting theme data into templates

**`app/routes/theme.py`** - Theme API endpoints
- `GET /api/theme` - Get current active theme
- `GET /api/theme/list` - List all available themes
- `POST /api/theme` - Switch to a different theme
- `DELETE /api/theme` - Reset to default theme

### Frontend Components

**`static/js/theme-switcher.js`** - Theme switching UI
- `ThemeSwitcher` class - Manages theme switching on frontend
- Populates theme selector dropdown
- Handles theme change events
- Triggers page reload after theme switch
- Keyboard shortcut: `Ctrl+Shift+T` to cycle themes

**Base Templates**
- `templates/base_enhanced.html` - Enhanced UI with theme support
- `templates/base.html` - Standard UI with theme support

Both templates dynamically load:
- Theme-specific CSS files
- Theme-specific fonts
- Theme switcher dropdown in navbar

## Theme Configuration

Each theme defines:

```python
{
    "name": "Shadcn",
    "description": "Clean, minimal, professional",
    "css_files": [
        "/static/css/styles.css",
        "/static/css/shadcn-theme.css"
    ],
    "fonts": "https://fonts.googleapis.com/css2?family=Inter...",
    "dark_mode": True
}
```

### Shadcn Theme (Default)
- **Aesthetic**: Clean, minimal, professional
- **Colors**: HSL-based slate grays, subtle borders
- **Fonts**: Inter (body), JetBrains Mono (code)
- **CSS**: `shadcn-theme.css` (700 lines)
- **Design System**: Inspired by shadcn/ui

### Cyberpunk Theme
- **Aesthetic**: Neon glow, matrix-inspired
- **Colors**: Bright greens (#00ff00), hot pinks (#e91e63), cyber blues
- **Fonts**: Orbitron (headers), Roboto (body), JetBrains Mono (code)
- **CSS**: `cyberpunk.css` + `custom_theme.css`
- **Effects**: Text shadows, glows, animations

### Military C2 Theme
- **Aesthetic**: Tactical command & control
- **Colors**: Tactical greens, muted earth tones
- **Fonts**: Rajdhani (headers), Inter (body), JetBrains Mono (code)
- **CSS**: Tailwind-based (`islands-CJsyTXa3.css`)
- **Design**: Military-grade interface styling

## Usage

### User-Facing Theme Switching

Users can switch themes in two ways:

1. **Navbar Dropdown** - Select from theme dropdown in header
2. **Keyboard Shortcut** - Press `Ctrl+Shift+T` to cycle through themes

When a theme is selected:
1. POST request sent to `/api/theme` with theme value
2. Theme preference saved in cookie (1-year expiration)
3. Success notification displayed (if Alpine.js store available)
4. Page reloads to apply new theme

### Programmatic Theme Access

**Get current theme:**
```bash
curl http://localhost:8000/api/theme
```

Response:
```json
{
  "theme": "shadcn",
  "name": "Shadcn",
  "description": "Clean, minimal, professional",
  "dark_mode": true
}
```

**List all themes:**
```bash
curl http://localhost:8000/api/theme/list
```

**Switch theme:**
```bash
curl -X POST http://localhost:8000/api/theme \
  -H "Content-Type: application/json" \
  -d '{"theme": "cyberpunk"}'
```

**Reset to default:**
```bash
curl -X DELETE http://localhost:8000/api/theme
```

### Template Integration

All routes must include theme context for dynamic theme loading:

```python
from app.theme import get_theme_context

@router.get("/my-page")
async def my_page(request: Request):
    context = {"request": request, "page": "my_page"}
    context.update(get_theme_context(request))
    return templates.TemplateResponse("my_template.html", context)
```

Templates use theme data like this:

```html
<!-- Dynamic fonts -->
{% if theme and theme.fonts %}
<link href="{{ theme.fonts }}" rel="stylesheet">
{% endif %}

<!-- Dynamic CSS files -->
{% if theme and theme.css_files %}
  {% for css_file in theme.css_files %}
<link href="{{ css_file }}" rel="stylesheet">
  {% endfor %}
{% endif %}
```

## Theme Persistence

Themes are persisted using browser cookies:

- **Cookie Name**: `theme`
- **Valid Values**: `shadcn`, `cyberpunk`, `military`
- **Max Age**: 31,536,000 seconds (1 year)
- **HttpOnly**: False (accessible by JavaScript)
- **SameSite**: Lax

The theme manager checks for the theme in this priority:

1. **Session** (if session middleware enabled)
2. **Cookie** (fallback, always available)
3. **Config default** (settings.UI_THEME)
4. **Hardcoded fallback** (shadcn)

## Adding a New Theme

To add a new theme:

1. **Create theme CSS file** in `static/css/`
2. **Add theme to enum** in `app/theme.py`:
   ```python
   class Theme(str, Enum):
       SHADCN = "shadcn"
       CYBERPUNK = "cyberpunk"
       MILITARY = "military"
       YOUR_THEME = "yourtheme"  # Add here
   ```

3. **Add theme config** to `THEME_CONFIG`:
   ```python
   Theme.YOUR_THEME: {
       "name": "Your Theme Name",
       "description": "Brief description",
       "css_files": [
           "/static/css/styles.css",
           "/static/css/yourtheme.css"
       ],
       "fonts": "https://fonts.googleapis.com/...",
       "dark_mode": True
   }
   ```

4. **Update theme icons** in `static/js/theme-switcher.js`:
   ```javascript
   getThemeIcon(themeValue) {
       const icons = {
           'shadcn': 'bi-palette',
           'cyberpunk': 'bi-lightning',
           'military': 'bi-shield-shaded',
           'yourtheme': 'bi-star'  // Add here
       };
       return icons[themeValue] || 'bi-palette';
   }
   ```

5. **Test the new theme** on all pages to ensure consistency

## Development Guidelines

### Creating Theme CSS

When creating theme CSS, follow these patterns:

**Use HSL color variables:**
```css
:root {
  --background: 222.2 84% 4.9%;
  --foreground: 210 40% 98%;
  --primary: 217.2 91.2% 59.8%;
}

.card {
  background: hsl(var(--background));
  color: hsl(var(--foreground));
}
```

**Style all components consistently:**
- Cards
- Buttons
- Forms (inputs, selects, textareas)
- Badges
- Alerts
- Tables
- Navigation

**Ensure dark mode compatibility:**
- Use dark backgrounds
- Ensure sufficient contrast ratios (WCAG AA minimum)
- Test readability on all pages

### Testing Themes

Test themes across all pages:
- Dashboard (`/enhanced`)
- AI Agents (`/ai/dashboard`)
- Execution Monitor (`/execution/monitor`)
- Visualizer (`/execution/visualizer`)
- Health (`/health`)
- Exercises (`/exercises`)
- Templates (`/templates`)
- Metrics (`/metrics`)
- Attacks (`/attacks`)

Verify:
- ✓ All CSS loads correctly
- ✓ Fonts apply properly
- ✓ Colors are consistent
- ✓ No layout breakage
- ✓ Theme switcher works
- ✓ Keyboard shortcut works
- ✓ Theme persists across page reloads

## Troubleshooting

### Theme not applying after switch
- Check browser console for CSS loading errors
- Verify theme cookie is set (check browser DevTools > Application > Cookies)
- Ensure page reloaded after theme switch
- Clear browser cache if stale CSS persists

### Theme switcher not showing
- Ensure `static/js/theme-switcher.js` is included in template
- Check that `#theme-selector` element exists in navbar
- Verify JavaScript console for errors

### API endpoints returning 500 errors
- Check server logs for detailed error messages
- Ensure all routes have `get_theme_context(request)` called
- Verify theme enum values match in frontend and backend

### Theme not persisting
- Check that theme cookie has correct domain and path
- Verify cookie max-age is set properly
- Ensure cookie is not being blocked by browser settings

## Security Considerations

- Theme values are validated against enum before applying
- Cookie is set with SameSite=Lax to prevent CSRF
- No sensitive data stored in theme preferences
- CSS files served from static directory (no dynamic CSS injection)

## Performance

- **CSS Caching**: Theme CSS files are static and cacheable
- **Minimal JavaScript**: Theme switcher is lightweight (~250 lines)
- **No Render Blocking**: Theme detection happens server-side
- **Page Reload**: Required for theme switch to ensure all assets reload correctly

## Future Enhancements

Potential improvements:
- Session-based persistence (when session middleware added)
- Live theme switching without page reload
- Custom theme builder UI
- User-specific theme preferences in database
- Theme preview before applying
- Light mode variants for each theme
- Accessibility theme (high contrast)

## Related Files

- `app/theme.py` - Theme management system (150 lines)
- `app/routes/theme.py` - Theme API routes (158 lines)
- `static/js/theme-switcher.js` - Frontend switcher (230 lines)
- `static/css/shadcn-theme.css` - Shadcn theme styles (700 lines)
- `static/css/cyberpunk.css` - Cyberpunk theme styles
- `static/css/custom_theme.css` - Shared custom styles
- `templates/base_enhanced.html` - Enhanced base template with theme support
- `templates/base.html` - Standard base template with theme support
- `app/config.py` - Theme configuration settings

## Support

For issues or questions about the theme system:
1. Check server logs for errors
2. Test API endpoints directly with curl
3. Verify theme CSS files exist and load correctly
4. Ensure all routes include theme context
5. Review this documentation for configuration guidance
[0m