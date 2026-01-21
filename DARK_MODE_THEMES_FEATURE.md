# Dark Mode & Themes Feature 🌙

## Overview
The Dark Mode & Themes feature provides a comprehensive theming system with multiple theme options including light mode, dark mode, system-aware theming, and a special night mode for evening runners. The feature includes centralized theme management, user preferences, and consistent styling across all components.

## Features Implemented

### Theme System Architecture
- **ThemeContext** (`mobile/runcoach-mobile/contexts/ThemeContext.tsx`)
  - Centralized theme management with React Context
  - Multiple theme modes: Light, Dark, System, Night
  - Persistent theme preferences with AsyncStorage
  - System theme detection and automatic switching

### Theme Options

#### 🌞 Light Mode
- **Best for**: Daytime runs and bright environments
- **Colors**: Light backgrounds, dark text, vibrant accents
- **Benefits**: High contrast, easy readability in sunlight

#### 🌙 Dark Mode  
- **Best for**: Evening runs and low-light conditions
- **Colors**: Dark backgrounds, light text, muted accents
- **Benefits**: Reduces eye strain, saves battery on OLED screens

#### 📱 System Default
- **Best for**: Users who want automatic switching
- **Behavior**: Follows device system settings
- **Benefits**: Seamless integration with device preferences

#### 👁️ Night Mode (Special Feature)
- **Best for**: Early morning or late evening runs
- **Colors**: Red-tinted display to preserve night vision
- **Benefits**: Maintains night vision adaptation for safety

### User Interface Components

#### Theme Settings Screen (`mobile/runcoach-mobile/app/theme-settings.tsx`)
- **Theme Selection**: Visual theme picker with icons
- **Live Preview**: See how themes look in real-time
- **Theme Benefits**: Educational information about each theme
- **Running Tips**: Theme-specific recommendations

#### Dashboard Integration
- **Theme Toggle Button**: Quick theme switching in header
- **Settings Access**: Direct link to theme settings
- **Consistent Styling**: All components use theme system

### Technical Implementation

#### Theme Structure
```typescript
interface Theme {
  mode: ThemeMode;
  colors: {
    // Background colors
    background: string;
    surface: string;
    card: string;
    
    // Text colors
    text: string;
    textSecondary: string;
    textMuted: string;
    
    // Primary colors
    primary: string;
    primaryLight: string;
    primaryDark: string;
    
    // Accent colors
    accent: string;
    success: string;
    warning: string;
    error: string;
    info: string;
    
    // UI elements
    border: string;
    divider: string;
    shadow: string;
    overlay: string;
    
    // Status bar
    statusBar: 'light-content' | 'dark-content';
    
    // Weather-specific colors
    weatherCold: string;
    weatherWarm: string;
    weatherHot: string;
    weatherRain: string;
  };
  
  // Theme properties
  isDark: boolean;
  isNight: boolean;
  
  // Design tokens
  spacing: { xs: 4, sm: 8, md: 16, lg: 24, xl: 32 };
  borderRadius: { sm: 4, md: 8, lg: 12, xl: 16 };
  typography: { h1, h2, h3, body, caption };
}
```

#### Theme Usage Pattern
```typescript
// In components
const { theme, themeMode, setThemeMode, toggleTheme } = useTheme();

// Dynamic styles
const styles = createStyles(theme);

// Style function
const createStyles = (theme: Theme) => StyleSheet.create({
  container: {
    backgroundColor: theme.colors.background,
    padding: theme.spacing.md,
  },
  text: {
    color: theme.colors.text,
    fontSize: theme.typography.body.fontSize,
  },
});
```

### Color Palettes

#### Light Theme Colors
- **Background**: `#f5f5f5` (Light gray)
- **Surface**: `#ffffff` (White)
- **Primary**: `#6200EE` (Purple)
- **Text**: `#333333` (Dark gray)
- **Success**: `#4CAF50` (Green)

#### Dark Theme Colors
- **Background**: `#121212` (Very dark gray)
- **Surface**: `#1e1e1e` (Dark gray)
- **Primary**: `#bb86fc` (Light purple)
- **Text**: `#ffffff` (White)
- **Success**: `#4CAF50` (Green)

#### Night Mode Colors
- **Background**: `#0a0000` (Very dark red)
- **Surface**: `#1a0000` (Dark red)
- **Primary**: `#ff6666` (Red)
- **Text**: `#ff9999` (Light red)
- **Accent**: `#ff6666` (Red tinted)

### Component Integration

#### Updated Components
- **Main Dashboard** (`mobile/runcoach-mobile/app/(tabs)/index.tsx`)
  - Theme toggle button in header
  - Dynamic styling with theme system
  - Settings navigation

- **Weather Widget** (`mobile/runcoach-mobile/components/WeatherWidget.tsx`)
  - Theme-aware colors and styling
  - Dynamic icon colors
  - Consistent with app theme

- **App Layout** (`mobile/runcoach-mobile/app/_layout.tsx`)
  - Theme provider integration
  - Navigation theme synchronization
  - Status bar styling

### User Experience Features

#### Theme Switching
- **Quick Toggle**: Tap theme icon to cycle through modes
- **Settings Screen**: Detailed theme selection with preview
- **System Integration**: Automatic switching based on device settings

#### Visual Feedback
- **Theme Icons**: Different icons for each theme mode
  - ☀️ Light mode: `sunny` icon
  - 🌙 Dark mode: `moon` icon  
  - 👁️ Night mode: `eye` icon
  - 📱 System: `phone-portrait` icon

#### Persistence
- **User Preferences**: Theme choice saved to device storage
- **App Restart**: Theme persists across app sessions
- **System Changes**: Responds to device theme changes

### Running-Specific Benefits

#### Light Mode Benefits
- **Daytime Visibility**: High contrast for bright conditions
- **Safety**: Easy to read in sunlight
- **Battery**: Standard power consumption

#### Dark Mode Benefits
- **Eye Strain**: Reduced strain in low light
- **Battery Life**: OLED power savings
- **Night Comfort**: Easier on eyes in darkness

#### Night Mode Benefits
- **Night Vision**: Red light preserves night adaptation
- **Safety**: Maintains ability to see surroundings
- **Early Runs**: Perfect for pre-dawn training

### Accessibility Features

#### High Contrast
- **Text Readability**: Strong contrast ratios
- **Color Blind Friendly**: Not relying solely on color
- **Large Touch Targets**: Easy theme switching

#### System Integration
- **Accessibility Settings**: Respects system preferences
- **Reduced Motion**: Smooth transitions
- **Screen Reader**: Proper labeling

### Performance Optimizations

#### Efficient Rendering
- **Context Optimization**: Minimal re-renders
- **Style Caching**: Efficient style creation
- **Memory Management**: Proper cleanup

#### Battery Considerations
- **OLED Optimization**: True black backgrounds in dark mode
- **Reduced Brightness**: Night mode uses darker colors
- **Efficient Updates**: Only update when theme changes

## Setup Instructions

### Installation
1. **Theme Provider**: Wrap app in ThemeProvider
2. **Component Updates**: Use `useTheme()` hook in components
3. **Style Functions**: Convert static styles to theme functions

### Usage Examples

#### Basic Theme Usage
```typescript
import { useTheme } from '../contexts/ThemeContext';

function MyComponent() {
  const { theme } = useTheme();
  
  const styles = StyleSheet.create({
    container: {
      backgroundColor: theme.colors.surface,
      padding: theme.spacing.md,
    },
    text: {
      color: theme.colors.text,
      fontSize: theme.typography.body.fontSize,
    },
  });
  
  return (
    <View style={styles.container}>
      <Text style={styles.text}>Themed content</Text>
    </View>
  );
}
```

#### Theme Switching
```typescript
const { themeMode, setThemeMode, toggleTheme } = useTheme();

// Set specific theme
setThemeMode('dark');

// Toggle through themes
toggleTheme();

// Check current theme
if (theme.isDark) {
  // Dark theme specific logic
}
```

## Future Enhancements

### Additional Themes
- **High Contrast**: Enhanced accessibility theme
- **Colorful**: Vibrant theme for motivation
- **Minimal**: Clean, distraction-free theme
- **Custom**: User-defined color schemes

### Advanced Features
- **Automatic Switching**: Time-based theme changes
- **Location Aware**: Theme based on sunrise/sunset
- **Activity Based**: Different themes for different workout types
- **Seasonal Themes**: Themes that change with seasons

### Integration Features
- **Wearable Sync**: Theme sync with smartwatches
- **Social Sharing**: Share theme preferences
- **Coach Integration**: Recommended themes for training
- **Performance Analytics**: Theme usage analytics

## Files Created/Modified

### New Files
- `mobile/runcoach-mobile/contexts/ThemeContext.tsx`
- `mobile/runcoach-mobile/app/theme-settings.tsx`

### Modified Files
- `mobile/runcoach-mobile/app/_layout.tsx` - Theme provider integration
- `mobile/runcoach-mobile/app/(tabs)/index.tsx` - Theme toggle and styling
- `mobile/runcoach-mobile/components/WeatherWidget.tsx` - Theme support

## Theme Configuration

### Default Theme Settings
- **System Default**: Follows device settings
- **Automatic Persistence**: Saves user preference
- **Smooth Transitions**: Animated theme changes
- **Consistent Styling**: All components themed

### Customization Options
- **Color Overrides**: Modify specific colors
- **Spacing Adjustments**: Custom spacing values
- **Typography**: Font size and weight customization
- **Border Radius**: Consistent corner rounding

The Dark Mode & Themes feature is now fully implemented, providing users with a personalized and comfortable viewing experience for all their running activities, whether it's a bright morning jog or a late-night training session! 🌙✨