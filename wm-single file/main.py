import Xlib.display
from Xlib import X, XK
from Xlib.ext import randr
from Xlib.protocol import event

import logging

logging.basicConfig(level=logging.DEBUG)

class Workspace:
    def __init__(self, display, screen, id):
        self.display = display
        self.screen = screen
        self.id = id
        self.windows = []

    def add_window(self, window):
        self.windows.append(window)

    def remove_window(self, window):
        self.windows.remove(window)

    def get_windows(self):
        return self.windows


class WindowManager:
    def __init__(self):
        self.display = Xlib.display.Display()
        self.screen = self.display.screen()
        self.root = self.screen.root
        self.root.change_attributes(event_mask=X.SubstructureNotifyMask)
        self.workspaces = [Workspace(self.display, self.screen, 0)]
        self.current_workspace = 0
        self.key_symbols = self.display.get_keyboard_mapping()
        self.mod_mask = X.Mod4Mask

    def run(self):
        self.update_screens()
        self.grab_keys()
        self.display.pending_events()
        while True:
            self.handle_event()

    def update_screens(self):
        res = randr.get_screen_resources(self.root)
        for output in res.outputs:
            out_info = randr.get_output_info(self.root, output, 0)
            crtc = out_info.crtc
            if not crtc:
                continue
            crtc_info = randr.get_crtc_info(self.root, crtc, 0)
            screen = self.find_screen(crtc_info.x, crtc_info.y, crtc_info.width, crtc_info.height)
            if not screen:
                screen = self.add_screen(crtc_info.x, crtc_info.y, crtc_info.width, crtc_info.height)
        self.remove_unused_screens()

    def add_screen(self, x, y, width, height):
        screen = Workspace(self.display, self.screen, len(self.workspaces))
        self.workspaces.append(screen)
        return screen

    def remove_unused_screens(self):
        self.workspaces = [w for w in self.workspaces if w.get_windows()]

    def find_screen(self, x, y, width, height):
        for screen in self.workspaces:
            if screen.id == self.current_workspace:
                continue
            if (screen.screen.width_in_pixels, screen.screen.height_in_pixels) == (width, height) and \
               (screen.screen.x, screen.screen.y) == (x, y):
                return screen
        return None

    def handle_event(self):
        event = self.display.next_event()
        if event.type == X.MapRequest:
            self.handle_map_request(event)
        elif event.type == X.DestroyNotify:
            self.handle_destroy_notify(event)
        elif event.type == X.KeyPress:
            self.handle_key_press(event)

    def handle_map_request(self, event):
        window = event.window
        window.map()
        screen = self.workspaces[self.current_workspace]
        screen.add_window(window)

    def handle_destroy_notify(self, event):
        window = event.window
        for screen in self.workspaces:
            if window in screen.get_windows():
                screen.remove_window(window)
                break

    def handle_key_press(self, event):
        keysym = self.display.keycode_to_keysym(event.detail, 0)
        if keysym == XK.XK_q:
            self.display.close()
        elif keysym == XK.XK_space:
            self.current_workspace = (self.current_workspace + 1) % len(self.workspaces)
            self.show_current_workspace()
       
