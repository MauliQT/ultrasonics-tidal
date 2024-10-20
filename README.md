![](https://raw.githubusercontent.com/XDGFX/ultrasonics/master/ultrasonics/static/images/logo.svg)

> ## Update 2024
> **ultrasonics** is is up and running again, now with Tidal and working.
>
> The offical api is offline and had some issues with ease of installation, especially regarding redirect-uri's this has been fixed  [**ultrasonics-api**](https://github.com/MauliQT/ultrasonics-api-self-hosted). 
>
> To use **ultrasonics** at its full potential i urge you to set up your own [**ultrasonics-api**](https://github.com/MauliQT/ultrasonics-api-self-hosted) instance alongside **ultrasonics**, and keys for any online services you want to sync with. The instructions are all available over on that repo!

---

- [Overview](#overview)
- [Installation](#installation)
  - [(Docker)]
- [Applets](#applets)
    - [Inputs](#inputs)
    - [Modifiers (Optional)](#modifiers-optional)
    - [Outputs](#outputs)
    - [Triggers](#triggers)
- [Plugins](#plugins)
- [Playlists Mode vs Songs Mode](#playlists-mode-vs-songs-mode)
- [Contributing](#contributing)
  - [Writing Your Own Plugin](#writing-your-own-plugin)
  - [Improving ultrasonics Source Code](#improving-ultrasonics-source-code)


# Overview

Welcome to **ultrasonics**!

**ultrasonics** is a tool designed to help you take control of your music library and music playlists. Gone are the days of having your playlists scattered across three different services, or being limited to using one service because you don't have the time to manually curate multiple copies of the same playlist.

**ultrasonics** uses plugins to interact with your favourite services. This means that functionality can be added by simply installing a new plugin. Each plugin may provide compatibility with a service, e.g. the official Spotify plugin links up to... well, Spotify of course. Other plugins provide additional functionality, such as merging playlists from more than one source.

The overview of all included plugins can be found at [documentation incomplete].

# Installation

## (Docker)

The official **ultrasonics** image is located at [xdgfx/ultrasonics](https://hub.docker.com/r/xdgfx/ultrasonics). You can pull and run it manually, or stick it in your `docker-compose.yml` file. !This is the old **ultrasonics** image which isn't working properly and doesnt have tidal integration.

The tidal **ultrasonics** image is located at [mauliqt/ultrasonics](https://github.com/MauliQT/ultrasonics-api-self-hosted). You can pull it manually, or stick it in your `docker-compose.yml`

```yaml
version: "3.7"
services:
  ultrasonics:
    image: mauliqt/ultrasonics:1.1
    container_name: ultrasonics
    restart: unless-stopped

    ports:
      - 5000:5000

    volumes:
      - /path/to/config:/config
      - /path/to/plugins:/plugins  # Used for third-party plugins

    environment:
      - PUID=${PUID}
      - PGID=${PGID}
```

# Applets

If you've ever used IFTTT you already understand the fundamentals. **ultrasonics** works with the concept of 'applets'. Each applet you create contains plugins which fit into one of four categories:

### Inputs

These plugins connect to a service to get a list of songs or playlists, and pass that list onto the Modifiers and Output plugins.

### Modifiers (Optional)

These plugins take a list of songs or playlists from one or more input plugins, and modify the list in some way. For example, they may merge duplicate playlists, or replace the songs with similar songs using a music discovery api.

### Outputs

These plugins take the list of playlists passed to them, and save them to a service. Maybe they update or create your playlists in Plex, or save them to a .m3u file on your home server.

### Triggers

These plugins aren't part of the songs / playlist flow, but instead determine when the applet actually runs. The most simple trigger is time-based, e.g. 'Run once every 6 hours'.

You can build your custom applets using the installed plugins, save it to the database, and then it will run automatically from a Trigger plugin, or by manually running the applet from the homepage.

# Plugins

**ultrasonics** comes bundled with several official plugins. For more info, see [documentation incomplete].

New plugins can be installed by simply copying the plugin containing folder into the `plugins` directory.

Each applet needs at least one input and one output plugin. To run automatically, it also needs at a trigger plugin.

Most plugins will have settings to configure, which could be global persistent settings (common for all instances of the plugin, across all your applets), or specific for this instance of the plugin.

You will be prompted to enter any required settings when you are building your applet.

Settings can always be left blank! In some cases, this is fine or expected, however in other cases this can result in plugin errors which might require manual fixing of the ultrasonics database! Make sure you fill out any settings you are supposed to!

# Playlists Mode vs Songs Mode

Some plugins are designed to work with playlists - e.g. the Spotify plugin interacts with your Spotify playlists. Some plugins are designed to work with songs, e.g. your top 100 songs on Last.fm.

If a plugin only works in songs-mode, a warning will be displayed on the "select plugin" screen.

Adding a songs-mode plugin to an input will effectively work by adding a single playlist to the applet flow. This *should* work without an issue, as long as the plugin in question provides a name for this single playlist.

Trying to feed multiple playlists into a single songs-mode output plugin will likely cause issues, it's not recommended.

# Contributing

So you want to help improve ultrasonics? First of all - thank you! As someone who is *not* a software engineer, this is one of the biggest projects I've worked on. Any help or suggestions are greatly appreciated!

## Writing Your Own Plugin
Expanding on the functionality of ultrasonics is easy! A plugin is a drag-and-drop installation, and so can greatly improve the project with minimal complexity. The best way to learn is [through the wiki](https://github.com/XDGFX/ultrasonics/wiki/Writing-a-Plugin). You can fork this project, or create your own repo specifically for your plugin. It can be kept separate, or if you feel it would benefit the community by making if a default plugin, let me know through a GitHub issue!

## Improving ultrasonics Source Code
I will put any future plans, known issues, or general improvements in the [issues](https://github.com/XDGFX/ultrasonics/issues). Also have a look at the [projects boards](https://github.com/XDGFX/ultrasonics/projects), which should show the issues that are high priority.

Or, if you have a new idea, give it a go and let me know with a pull request or issue! 😇
