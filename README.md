# Whakarere App Roadmap

## Objective
I just haven't had a good experience with the current whatsapps client available for linux, so I decided to create a flatpak whatsapp client using python and gnome technologies for its frontend and for the backend we'll user project based on [whatsapp-api](https://github.com/chrishubert/whatsapp-api) with few modifications to accommodate out use case. 

## Technology Stack
### Frontend
- Python3
- Gtk4
- Libadwaita

### Backend
- NodeJs App

## Development Phases
### Phase 1 (v0.1.0) - Next Release
- [X] Organize the structure of the project folder.
- [X] Add meson build system to the folder structure
- [x] Update Flatpak manifest to reflect changes made to the project.
- [X] UI design of a session management screen/window.
- [X] Implementing session management functions(Create, authenticate and remove session).
- [X] UI design for a authentication screen/window with Qr Code.
- [X] Implement Qr Code functions related functions.
- [ ] Implement backend Qr Code callback functions.
- [X] UI design of a basic WhatsApp screen/window.
- [X] Implementing load session details and displaing all whatsapp chats/groups informations on sidebar, including chat avatar, most type of last messages, timestamp and etc.
- [ ] Implementing loading of all messages upon selecting a chat/group chat.
- [ ] implementing basic text message sending functions.
- [ ] Implementing basic notification for incoming messages.

### Phase 2 (v0.2.0) - Database Update
- [ ] Add a database to improve performance and eliminate the need for constant api calls.
- [ ] Implement WhatsAppManager to handle the newly added database and minimize calls to to the api.
- [ ] Refactor code to use database calls instead of the api.

### Phase 3 (0.3.0 - Message Types Updates.
- [ ] 
- [ ] Improve message sending functions to include media types(Photo, video, poll, share, location and etc).
- [ ] Improve notifications to handle new the newly included message types.
- [ ] 
- [ ]
- [ ] 

## Milestones and Timeline (Current planned release dates based on me working alone at the point)
- Phase 1: 15/12/2023
- Phase 2: 01/02/2024
- Phase 3: 01/05/2024

## Helping the project
### What can I do to help
- Clone the repo and pick an a feature in need of development and push your changes.
- Open bug reports, some bugs aren't noticed without your help.
- Request new features, but be sure to read the roadmap to not requested features already planned for future releases.

### Requeriments for a dev environment
- Phython 3.11+
- Flatpak
- Flatpak-Builder
- Meson

### Building the project from source
```shell
flatpak-builder --user --install --force-clean flatpak com.mudeprolinux.whakarere.yml
```

## Thanks/Shoutout
Without the work of [Christophe Hubert](https://github.com/chrishubert) and everyone on the [whatsapp-api](https://github.com/chrishubert/whatsapp-api), and in turn the work of [Pedro S. Lopez](https://github.com/pedroslopez) and everyone on the [whatsapp-web.js](https://github.com/pedroslopez/whatsapp-web.js) which is used for the development of [whatsapp-api](https://github.com/chrishubert/whatsapp-api) mine would never exist, Big Thanks for everyone involved.

Thanks as well to everyone that has contributed to the project so far, either pushing code, reporting bugs or requesting features. Every little bit helps.
