# Prepare Merge - MO2 Plugin

Finds and enables the mods containing a selected list of plugins and their required masters. Then places the selected plugins at the end of the load order.

## Installation

Download the latest [release](https://github.com/ssauermann/mo2-plugins/releases/latest) and unzip it into your MO2 plugins folder.

The file structure should look like this:
`...\MO2\plugins\merge-plugins\*.py`

## Usage

1. Select your main profile where all your mods are enabled. Run `Prepare Merge` from the plugin menu and select this as the base profile for merge preparation by clicking on `Load active profile as base`. The virtual file system of this profile will be used to generate the plugin-to-mod mapping. Then close the window. (The mapping is stored persistently in the `plugins/data/merge-plugins` folder if you want to delete it for some reason)
2. Change to a new profile for creating the merge. (Copy your main profile instead of creating a fresh one to keep the mod order)
3. Run `Prepare Merge` again and select the plugins you want to merge by dragging them into the right list. Reorder the list to match your desired load order from top (low priority) to bottom (high priority). Finally click the `Prepare merge in active profile` button and close the window.
4. The mods that contain those plugins will be enabled and the plugins placed at the end of the load order. Additionally, masters of the active plugins will be enabled as well until there are no missing masters left.
5. Run tools like zEdit to generate the merge as usual.

## More Usage Info

Instead of searching plugins separately in the left table, you can import a list of plugins from your clipboard directly into the right list.

Copy a list of plugins separated by a new line into your clipboard and press the `Import entries from clipboard` button. Plugins that do not exist in the mapping table are ignored.


![Prepare Merge Example](https://user-images.githubusercontent.com/4701556/112555788-27c38500-8dc9-11eb-9100-f42622725122.gif)

## Development
Please report any bugs you find on Nexus or here on GitHub. Feel free to request additional features if you think some functionality is missing.

## Development Setup
Setup an environment for development by running `pipenv install --pre`
