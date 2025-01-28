# Button Box

Button Box is a dynamically generated app that displays preconfigured buttons that can send messages in AC Chat. This is useful to configure chat based commands to UI buttons

## Usage
in apps/python/button_box edit the buttons.config file and follow instructions there.

To add a new button add an entry on a new line. The text on the left side of the pipe character `|` is the text on the button. The right side is the message that will be sent.
```
#button_name|chatmsg
VSC|VSC In Effect!
LOL|(clown)
```

