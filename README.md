# homeassistant-vt100

A simple VT-100 frontend for Home Assistant, to be run with an actual VT-100 (or compatible) terminal that is attached via serial. Requires a Home Assistant installation running somewhere, a Long-Lived Access Token issued from your profile on Home Assistant, and a configuration file containing the desired layout for the dashboards you want to display. Currently this only supports `switch`, `sensor` and `binary_sensor` entity types as well as a few virtual layout elements. It allows for live update and toggle control of switches as well as live update display for sensors. I recommend using a Raspberry Pi or a Rock Pi S with a USB-to-serial adapter to drive your VT-100 using this code.

## How To Run This

First, make sure your dependencies are set up:

```
python3 -m pip install -r requirements.txt --upgrade
```

Then, run it like the following:

```
python3 dashboard.py --config config.yaml
```

Don't forget to edit your config file to customize it for your own setup!

## Navigation and Interaction

Navigating between dashboards that you've configured can be achieved with the `<` and `>` keys, much like the `top` terminal application. Alternatively, you can type `next` or `n` and press enter to go to the next dashboard, or `previous`, `prev` or `p` and press enter to go to the previous dashboard. Typing `exit` and pressing enter will shut down the monitoring program and reset the terminal. If the current dashboard has switches displayed on it, you can type `toggle <switch>` and press enter to toggle that switch on or off. This accepts both exact names as well as partial names of switches as long as the partial name resolves to a single switch. Alternatively, you can use the up and down arrows to select the switch you want to toggle and press enter with a blank input in order to toggle the switch. If you've enabled the help tab, you can also type `help` to fast-travel to the help screen which shows basic commands.

## Config File Documentation

The `config.yaml` sample configuration can be edited or copied to make a configuration file that you are happy with. It has a variety of options, some of which you must configure and some of which you can tweak only if you want to mess with options.

### Home Assistant Options

The URL should be the access URL that you type into a browser in order to connect to your Home Assistant installation. It should start with `http://` or `https://` but you can choose to use the internal or external URL as long as the device running this software can connect to it through the local network. If you place the device on a separate network, then you should use the public URL. The token is a Long-Lived Access Token that you have generated to authorize this software to connect to your Home Assistant installation. You can generate one by going to your profile in a web browser and scrolling to the bottom.

Optionally, a monitoring server can be opened that will allow you to periodically check that your device is up and running properly. You can use this if you want to monitor a Raspberry Pi/Rock Pi S being driven off of a flaky wifi connection. If you want this, set enabled to "true" under the Home Assistant monitoring section. If you wish to change the port as well, you can do so by editing the port. Note that the port must be between 1 and 65535. If you are on a unix system then ports below 1024 require root access to use.

## Terminal Options

Ths port should be the actual serial device that your terminal is connected to. On Linux this is often `/dev/ttyUSB0` or `/dev/ttyACM0`. I think that it should be the same under OSX. On Windows, you will want to use `COM0` or similar, based on what COM port your terminal is attached to. The baud rate specified should match the configuration on your VT-100 itself. I recommend keeping it at 9600 baud as terminals can become somewhat lossy at higher data rates.

## General Options

The name option allows you to customize the header with something unique to your setup. This does not need to be changed if you don't care. The show help option allows you to enable or disable help display. If enabled, a `Help` tab will be added to the end of your dashboards that can be reached either by moving to it using normal navigation commands or by typing `help` and pressing enter. If you disable help display, the `help` command will also be disabled.

## Layout Options

The layout section allows you to specify dashboards and their contents. It is a very simple syntax that only allows for sequential listing of entities to be displayed. Each dashboard in the layout list includes the name of the dashboard which will be displayed in the tab section at the top. It also includes an entities list which allows you to add zero or more entities to that dashboard. The entities you list here should be valid Entity IDs as found in your Home Assistant setup. You can find these Entity IDs in the Settings->Devices and Services->Entities panel under the "Entity ID" column on your Home Assistant instance. Any switch, sensor or binary sensor entity type can be displayed on a panel.

You can also provide a few virtual entity types in order to customize the layout slightly. The `<hr>` virtual entity causes a newline and horizontal rule to be displayed. This is handy for separating sections out. The `<label this is a caption>` virtual entity caues a new line and the text "this is a caption" to be displayed. This is handy for captioning separate sections or adding text descriptions to various parts of your dashboards. Note that you can include your own text instead of the above sample text, or you can include a blank `<label>` to add a blank line.

## Example Config File

```
homeassistant:
  url: https://my.homeassistant.url.com/
  token: really-long-token-string-i-copied-from-home-assistant
terminal:
  port: /dev/ttyUSB0
  baud: 9600
general:
  name: My Lovely Home Assistant Dashboard
  show_help: True
layout:
  - name: Overview
    entities:
     - <label Environment>
     - sensor.upstairs_temperature
     - sensor.downstairs_temperature
     - <hr>
     - <label Power>
     - sensor.watts_total
  - name: Lights
    entities:
     - <label Upstairs>
     - switch.bedroom_lights
     - switch.office_lights
     - <hr>
     - <label Downstairs>
     - switch.kitchen_lights
     - switch.living_room_lights
     - switch.entry_lights
```
