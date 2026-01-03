#!/usr/bin/env python3
"""
Middle Mouse Button Stage Manager Controller
Drag left/right while holding middle mouse button to navigate Stage Manager spaces
Menu bar app with enable/disable and startup options
"""

import rumps
from pynput import mouse
from pynput.mouse import Button
import subprocess
import threading
import os
import sys
import plistlib
from pathlib import Path


class StageManagerController:
    def __init__(self):
        self.middle_pressed = False
        self.start_x = 0
        self.start_y = 0
        self.triggered = False
        self.threshold = 50
        self.enabled = True
        self.listener = None
        self.permissions_shown = False

    def on_click(self, x, y, button, pressed):
        if not self.enabled:
            return

        if button == Button.middle:
            if pressed:
                self.middle_pressed = True
                self.start_x = x
                self.start_y = y
                self.triggered = False
            else:
                self.middle_pressed = False
                self.triggered = False

    def on_move(self, x, y):
        if not self.enabled or self.middle_pressed is False or self.triggered:
            return

        dx = x - self.start_x

        if abs(dx) > self.threshold:
            # Show permissions reminder on first gesture
            if not self.permissions_shown:
                self.show_permissions_reminder()
                self.permissions_shown = True

            if dx > 0:
                self.trigger_stage_manager('left')
            else:
                self.trigger_stage_manager('right')

            self.triggered = True

    def trigger_stage_manager(self, direction):
        key_code = "123" if direction == 'left' else "124"

        applescript = f'''
        tell application "System Events"
            key code {key_code} using control down
        end tell
        '''

        subprocess.run(['osascript', '-e', applescript],
                       check=False,
                       stdout=subprocess.DEVNULL,
                       stderr=subprocess.DEVNULL)

    def start(self):
        if self.listener is None:
            self.listener = mouse.Listener(
                on_click=self.on_click,
                on_move=self.on_move
            )
            self.listener.start()

    def stop(self):
        if self.listener:
            self.listener.stop()
            self.listener = None

    def show_permissions_reminder(self):
        """Show macOS-style alert about required permissions"""
        script = '''
        display alert "Permissions Required" message "Switch Stages requires both Input Monitoring and Accessibility permissions to function properly.

If the app isn't working:
1. Open System Settings
2. Go to Privacy & Security
3. Enable Switch Stages in both:
   • Input Monitoring
   • Accessibility

You may need to restart the app after granting permissions." as informational buttons {"OK", "Open Settings"} default button "OK"
        '''
        try:
            result = subprocess.run(['osascript', '-e', script],
                                    capture_output=True,
                                    text=True)
            if 'Open Settings' in result.stdout:
                subprocess.run(
                    ['open', 'x-apple.systempreferences:com.apple.preference.security?Privacy_Accessibility'])
        except:
            pass


class StageManagerMenuBar(rumps.App):
    def __init__(self):
        # Load icon preference
        self.icon_choice = self.load_icon_preference()

        # Determine the correct path for the icon
        if getattr(sys, 'frozen', False):
            # Running as compiled .app
            bundle_dir = os.path.dirname(os.path.dirname(os.path.dirname(sys.executable)))
            icon_path = os.path.join(bundle_dir, 'Contents', 'Resources', self.icon_choice)
        else:
            # Running as script
            script_dir = os.path.dirname(os.path.abspath(__file__))
            icon_path = os.path.join(script_dir, self.icon_choice)

        # Use icon if it exists, otherwise use title
        if os.path.exists(icon_path):
            super().__init__("", icon=icon_path, quit_button=None)
        else:
            super().__init__("SM", quit_button=None)

        self.controller = StageManagerController()
        self.controller.start()

        # Create menu items
        self.enabled_item = rumps.MenuItem("Enabled", callback=self.toggle_enabled)
        self.enabled_item.state = True

        self.startup_item = rumps.MenuItem("Launch at Startup", callback=self.toggle_startup)
        self.startup_item.state = self.is_startup_enabled()

        # Icon selection submenu
        self.icon_menu1 = rumps.MenuItem("Icon 1", callback=self.set_icon1)
        self.icon_menu2 = rumps.MenuItem("Icon 2", callback=self.set_icon2)
        self.update_icon_checkmarks()

        self.menu = [
            self.enabled_item,
            rumps.separator,
            self.startup_item,
            rumps.separator,
            ["Menu Bar Icon", [self.icon_menu1, self.icon_menu2]],
            rumps.separator,
            rumps.MenuItem("Quit", callback=self.quit_app)
        ]

    def toggle_enabled(self, sender):
        sender.state = not sender.state
        self.controller.enabled = sender.state

    def toggle_startup(self, sender):
        if sender.state:
            self.disable_startup()
            sender.state = False
        else:
            self.enable_startup()
            sender.state = True

    def load_icon_preference(self):
        """Load saved icon preference, default to menu.png"""
        prefs_path = os.path.expanduser("~/.stagemanager_icon_pref")
        if os.path.exists(prefs_path):
            try:
                with open(prefs_path, 'r') as f:
                    return f.read().strip()
            except:
                pass
        return "menu.png"

    def save_icon_preference(self, icon_name):
        """Save icon preference"""
        prefs_path = os.path.expanduser("~/.stagemanager_icon_pref")
        try:
            with open(prefs_path, 'w') as f:
                f.write(icon_name)
        except:
            pass

    def update_icon_checkmarks(self):
        """Update checkmarks on icon menu items"""
        self.icon_menu1.state = (self.icon_choice == "menu.png")
        self.icon_menu2.state = (self.icon_choice == "menu2.png")

    def set_icon1(self, sender):
        """Switch to menu.png"""
        self.icon_choice = "menu.png"
        self.save_icon_preference(self.icon_choice)
        self.update_icon_checkmarks()
        self.update_icon()

    def set_icon2(self, sender):
        """Switch to menu2.png"""
        self.icon_choice = "menu2.png"
        self.save_icon_preference(self.icon_choice)
        self.update_icon_checkmarks()
        self.update_icon()

    def update_icon(self):
        """Update the menu bar icon"""
        if getattr(sys, 'frozen', False):
            bundle_dir = os.path.dirname(os.path.dirname(os.path.dirname(sys.executable)))
            icon_path = os.path.join(bundle_dir, 'Contents', 'Resources', self.icon_choice)
        else:
            script_dir = os.path.dirname(os.path.abspath(__file__))
            icon_path = os.path.join(script_dir, self.icon_choice)

        if os.path.exists(icon_path):
            self.icon = icon_path

    def get_plist_path(self):
        return os.path.expanduser("~/Library/LaunchAgents/com.stagemanager.controller.plist")

    def get_app_path(self):
        """Get the correct path whether running as .app or script"""
        if getattr(sys, 'frozen', False):
            # Running as compiled .app - return the .app bundle path
            return os.path.dirname(os.path.dirname(os.path.dirname(sys.executable)))
        else:
            # Running as script
            return os.path.abspath(__file__)

    def is_startup_enabled(self):
        return os.path.exists(self.get_plist_path())

    def enable_startup(self):
        app_path = self.get_app_path()

        if getattr(sys, 'frozen', False):
            # Use 'open' command for .app bundles
            plist_content = {
                'Label': 'com.stagemanager.controller',
                'ProgramArguments': ['/usr/bin/open', '-a', app_path],
                'RunAtLoad': True,
                'KeepAlive': False,
                'StandardOutPath': '/tmp/stagemanager.log',
                'StandardErrorPath': '/tmp/stagemanager.log'
            }
        else:
            # Use python executable for script
            python_path = sys.executable
            plist_content = {
                'Label': 'com.stagemanager.controller',
                'ProgramArguments': [python_path, app_path],
                'RunAtLoad': True,
                'KeepAlive': False,
                'StandardOutPath': '/tmp/stagemanager.log',
                'StandardErrorPath': '/tmp/stagemanager.log'
            }

        plist_path = self.get_plist_path()

        # Create LaunchAgents directory if it doesn't exist
        os.makedirs(os.path.dirname(plist_path), exist_ok=True)

        # Write plist file
        with open(plist_path, 'wb') as f:
            plistlib.dump(plist_content, f)

        # Load the launch agent
        subprocess.run(['launchctl', 'load', plist_path],
                       stdout=subprocess.DEVNULL,
                       stderr=subprocess.DEVNULL)

    def disable_startup(self):
        plist_path = self.get_plist_path()

        if os.path.exists(plist_path):
            # Unload the launch agent
            subprocess.run(['launchctl', 'unload', plist_path],
                           stdout=subprocess.DEVNULL,
                           stderr=subprocess.DEVNULL)

            # Remove the plist file
            os.remove(plist_path)

    def quit_app(self, _):
        self.controller.stop()
        rumps.quit_application()


if __name__ == "__main__":
    app = StageManagerMenuBar()
    app.run()