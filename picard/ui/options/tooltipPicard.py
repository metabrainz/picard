## Test and Reference Code

import pygtk

pygtk.require('2.0')
import gtk



def create_arrow_button(arrow_type, shadow_type):
    button = gtk.Button()
    arrow = gtk.Arrow(arrow_type, shadow_type)
    button.add(arrow)
    button.show()
    arrow.show()
    return button


class Tooltips:
    def __init__(self):


        window = gtk.Window(gtk.WINDOW_TOPLEVEL)

        window.set_title("Tooltips")


        window.connect("destroy", lambda w: gtk.main_quit())


        window.set_border_width(10)


        box = gtk.HBox(False, 0)
        box.set_border_width(2)
        window.add(box)

        # create a tooltips object
        self.tooltips = gtk.Tooltips()




        box.show()

        button = create_arrow_button(gtk.ARROW_UP, gtk.SHADOW_IN)
        box.pack_start(button, False, False, 3)
        self.tooltips.set_tip(button, "In")

        button = create_arrow_button(gtk.ARROW_DOWN, gtk.SHADOW_OUT)
        box.pack_start(button, False, False, 3)
        self.tooltips.set_tip(button, "Out")

        button = create_arrow_button(gtk.ARROW_LEFT, gtk.SHADOW_ETCHED_IN)
        box.pack_start(button, False, False, 3)
        self.tooltips.set_tip(button, "In)

        button = create_arrow_button(gtk.ARROW_RIGHT, gtk.SHADOW_ETCHED_OUT)
        box.pack_start(button, False, False, 3)
        self.tooltips.set_tip(button, "Out")

        window.show()


def main():
    gtk.main()
    return 0


if __name__ == "__main__":
    tt = Tooltips()
    main()