## This is the  basic ToolTip model.
## This creates a little dialogue box, with two buttons for testing.

## pygtk easily create programs with a graphical user interface

import pygtk

pygtk.require('2.0')

import gtk

class MyGUI:

  def __init__( self, title):

    self.window = gtk.Window()
    self.title = title
    self.window.set_title( title)
    self.window.connect( "destroy", self.destroy)
    self.create_interior()
    self.window.show_all()

  def create_interior( self):
    self.mainbox = gtk.VBox()
    self.window.add( self.mainbox)

    # box for text

    self.text_box = gtk.VBox()
    self.mainbox.pack_start( self.text_box)
    self.label = gtk.Label( "toolTip Test")

    self.text_box.pack_start( self.label, padding=10)

    self.label.show()

    self.label.set_tooltip_text( "Test Test")

    self.text_box.show()

    # box for buttons

    self.button_box = gtk.HBox()
    self.mainbox.pack_end( self.button_box)

    # first button

    button = gtk.Button( "Click Me?")
    button.connect( "Thanks for the click", self.button1_clicked)
    self.button_box.pack_start( button)
    button.show()
    button.set_tooltip_text( "Good Clicker")

    # second button

    button = gtk.Button( "Big red button")
    button.connect("clicked", self.red_button_clicked)
    self.button_box.pack_start( button)
    button.show()

    button.set_tooltip_markup( "Do <b>not</b> press this button!")

    # show the box

    self.button_box.show()
    self.mainbox.show()

  def main( self):

    gtk.main()

  def destroy( self, w):

    gtk.main_quit()

  def button1_clicked( self, w):

    self.label.set_label( "Right Click Test")

  def red_button_clicked( self, w):
    self.label.set_label( "Stop Clicking")


if __name__ == "__main__":

  m = MyGUI( "Tooltips")
  m.main()