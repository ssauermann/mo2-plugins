# Prepare Merge - MO2 Plugin

Finds and enables the mods containing a selected list of plugins and their required masters. Then places the selected plugins at the end of the load order.

## Installation

Download the latest [release](https://github.com/ssauermann/mo2-plugins/releases/latest) and unzip it into your MO2 plugins folder.

## Usage

1. Select your main profile where all your mods are enabled. Run `Prepare Merge` from the plugin menu and select this as the base profile for merge preparation by clicking on `Load active profile as base`. The virtual file system of this profile will be used to generate the plugin-to-mod mapping. Then close the window. (This mapping is only stored until MO2 is closed)
2. Change to a new profile for creating the merge.
3. Run `Prepare Merge` again and select the plugins you want to merge by dragging them into the right list. Reorder the list to match your desired load order from top (low priority) to bottom (high priority). Finally click the `Prepare merge in active profile` button and close the window.
4. The mods that contain those plugins will be enabled and the plugins placed at the end of the load order. Additionally, masters of the active plugins will be enabled as well until there are no missing masters left.
5. Run tools like zEdit to generate the merge as usual.

![Prepare Merge Example](https://user-images.githubusercontent.com/4701556/112555788-27c38500-8dc9-11eb-9100-f42622725122.gif)

## Development Setup
Setup an environment for development by running `pipenv install --pre`
