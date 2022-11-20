# Microchat HTTP API documentation

## Endpoints statuses

- ✅ Implemented
- ⚠️ Partially implemented
- ❌ Not implemented

## Overview

- Service ❌
  - `/api/v0/supported_versions`: `GET` ❌
- Authentication ✅
  - `/api/v0/auth/sessions`: `GET` ✅, `POST` ✅
  - `/api/v0/auth/sessions/{session_id}`: `DELETE` ✅
- Users and bots ❌
  - `/api/v0/users`: `POST` ❌ (unauthenticated access)
  - `/api/v0/bots`: `POST` ❌
- Entities (users, bots, conferences) ⚠️
  - `/api/v0/entities/self`: `GET` ✅, `PATCH` ✅, `DELETE` ✅
  - `/api/v0/entities/({eid}|@{alias})`: `GET` ✅, `PATCH` ✅, `DELETE` ✅
  - `/api/v0/entities/({eid}|@{alias})/avatars`: `GET` ✅, `POST` ✅
  - `/api/v0/entities/({eid}|@{alias})/avatars/{id}`: `DELETE` ✅
  - `/api/v0/entities/({eid}|@{alias})/pemissions`: `GET` ✅, `PATCH` ⚠️
    Users and bots permissons. You can't manage conference's permissions.
- Chats ❌
  - `/api/v0/chats`: `GET` ❌
  - `/api/v0/chats/({eid}|@{alias})`: `GET` ❌, `DELETE` ❌
  - `/api/v0/chats/({eid}|@{alias})/messages`: `GET` ❌, `POST` ❌
  - `/api/v0/chats/({eid}|@{alias})/messages/{id}`: `GET` ❌, `PATCH` ❌, `DELETE` ❌
  - `/api/v0/chats/({eid}|@{alias})/messages/{id}/attachments/{id}/preview`: `GET` ❌
  - `/api/v0/chats/({eid}|@{alias})/messages/{id}/attachments/{id}/content`: `GET` ❌
  - `/api/v0/chats/({eid}|@{alias})/(photos|audios|videos|animations|files)`: `GET` ❌
  - `/api/v0/chats/({eid}|@{alias})/(photos|audios|videos|animations|files)/{id}`: `GET` ❌, `DELETE` ❌
- Conferences ❌
  - `/api/v0/conferences`: `POST` ❌
  - `/api/v0/conferences/({eid}|@{alias})/members`: `GET` ❌, `POST` ❌
  - `/api/v0/conferences/({eid}|@{alias})/members/permissions`: `GET` ❌, `PATCH` ❌
  - `/api/v0/conferences/({eid}|@{alias})/members/{id}`: `GET` ❌, `DELETE` ❌
  - `/api/v0/conferences/({eid}|@{alias})/members/@{alias}`: `GET` ❌, `DELETE` ❌
  - `/api/v0/conferences/({eid}|@{alias})/members/{id}/permissions`: `GET` ❌, `PATCH` ❌
  - `/api/v0/conferences/({eid}|@{alias})/members/@{alias}/permissions`: `GET` ❌, `PATCH` ❌
- Media ✅
  - `/api/v0/media`: `POST` ✅
  - `/api/v0/media/{hash}`: `GET` ✅
  - `/api/v0/media/{hash}/content`: `GET` ✅
  - `/api/v0/media/{hash}/preview`: `GET` ✅
- Contacts ❌
  - `/api/v0/contacts`: `GET` ❌, `POST` ❌
  - `/api/v0/contacts/@{alias}`: `GET` ❌, `PATCH` ❌, `DELETE` ❌
  - `/api/v0/contacts/{id}`: `GET` ❌, `PATCH` ❌, `DELETE` ❌
- Events
  - `/api/v0/events`: `GET (Server-Sent Events)` ❌

## Authentication

- `/api/v0/auth/sessions`
  - ✅ GET offset, count
  - ✅ POST login, password

- `/api/v0/auth/sessions/{sessions_id}`
  - ✅ DELETE

## Users and bots

- `/api/v0/users`
  - ❌ POST alias, password (unauthorized access)
    Register new user

- `/api/v0/bots`
  - ❌ POST alias
    Register new bot

## Entities

- `/api/v0/entities/self`
  - ❌ GET
  - ❌ PATCH
  - ❌ DELETE

- `/api/v0/entities/{eid}`
- `/api/v0/entities/@{alias}`
  - ❌ GET
  - ❌ PATCH
  - ❌ DELETE

- `/api/v0/entities/{eid}/avatars`
- `/api/v0/entities/@{alias}/avatars`
  - ❌ GET
  - ❌ POST

- `/api/v0/entities/{eid}/avatars/{id}`
- `/api/v0/entities/@{alias}/avatars/{id}`
  - ❌ GET
  - ❌ DELETE

- `/api/v0/entities/{eid}/permissions`
- `/api/v0/entities/@{alias}/pemissions`
  Users and bots permissons. You can't manage conference's permissions.
  - ❌ GET
  - ❌ PATCH

## Chats

- `/api/v0/chats`
  - ✅ GET offset, count
    List of entities, where every entity have fields above:
    - alias
    - type
    - avatar
    Additional fields for users:
    - name
    - surname
    - bio
    - common_conferences
    - (viewer's) permissions
    Additional fields for conferences and bots:
    - title
    - description

- `/api/v0/chats/{eid}`
- `/api/v0/chats/@{alias}`
  - ⚠️ GET
    - type
    - avatar
    for users:
    - name
    - surname
    - bio
    - common_conferences (?)
    - (viewer's) permissions
    for conferences and bots:
    - title
    - description
  - ⚠️ DELETE (owner and admin)

- `/api/v0/chats/{eid}/messages`
- `/api/v0/chats/@{alias}/messages`
  - ⚠️ GET offset, count
  - ⚠️ POST

- `/api/v0/chats/{eid}/messages/{id}`
- `/api/v0/chats/@{alias}/messages/{id}`
  - ⚠️ GET
  - ⚠️ PATCH (author only)
  - ⚠️ DELETE (author and conference admins only)

- `/api/v0/chats/{eid}/messages/{id}/attachments/{id}/preview`
- `/api/v0/chats/@{alias}/messages/{id}/attachments/{id}/preview`
  - ❌ GET

- `/api/v0/chats/{eid}/messages/{id}/attachments/{id}/preview`
- `/api/v0/chats/@{alias}/messages/{id}/attachments/{id}/content`
  - ❌ GET

- `/api/v0/chats/{eid}/messages/photos`
- `/api/v0/chats/{eid}/messages/audios`
- `/api/v0/chats/{eid}/messages/videos`
- `/api/v0/chats/{eid}/messages/animations`
- `/api/v0/chats/{eid}/messages/files`
- `/api/v0/chats/{eid}/messages/links`
- `/api/v0/chats/@{alias}/messages/photos`
- `/api/v0/chats/@{alias}/messages/audios`
- `/api/v0/chats/@{alias}/messages/videos`
- `/api/v0/chats/@{alias}/messages/animations`
- `/api/v0/chats/@{alias}/messages/files`
- `/api/v0/chats/@{alias}/messages/links`
  - ⚠️ GET offset, count

- `/api/v0/chats/{eid}/messages/photos/{id}`
- `/api/v0/chats/{eid}/messages/audios/{id}`
- `/api/v0/chats/{eid}/messages/videos/{id}`
- `/api/v0/chats/{eid}/messages/animations/{id}`
- `/api/v0/chats/{eid}/messages/files/{id}`
- `/api/v0/chats/{eid}/messages/links/{id}`
- `/api/v0/chats/@{alias}/messages/photos/{id}`
- `/api/v0/chats/@{alias}/messages/audios/{id}`
- `/api/v0/chats/@{alias}/messages/videos/{id}`
- `/api/v0/chats/@{alias}/messages/animations/{id}`
- `/api/v0/chats/@{alias}/messages/files/{id}`
- `/api/v0/chats/@{alias}/messages/links/{id}`
  - ⚠️ GET
  - ⚠️ DELETE (author and conference admins only)

## Conferences

- `/api/v0/conferences/{eid}/members`
- `/api/v0/conferences/@{alias}/members`
  - ⚠️ GET offset, count
  - ⚠️ POST

- `/api/v0/conferences/{eid}/members/{id}`
- `/api/v0/conferences/{eid}/members/@{alias}`
- `/api/v0/conferences/@{alias}/members/{id}`
- `/api/v0/conferences/@{alias}/members/@{alias}`
  - ⚠️ GET
  - ⚠️ DELETE (self-delete or conference admins only)

- `/api/v0/conferences/{eid}/members/{id}/permissions`
- `/api/v0/conferences/{eid}/members/@{alias}/permissions`
- `/api/v0/conferences/@{alias}/members/{id}/permissions`
- `/api/v0/conferences/@{alias}/members/@{alias}/permissions`
  - ⚠️ GET
  - ⚠️ PATCH (conference admins only)

## Media

- `/api/v0/media`
  - ✅ POST
- `/api/v0/media/{hash}`
  - ✅ GET
- `/api/v0/media/{hash}/content`
  - ✅ GET
- `/api/v0/media/{hash}/preview`
  - ✅ GET

## Contacts

- `/api/v0/contacts`
  - ❌ GET offset, count
  - ❌ POST username, [name], [surname]

- `/api/v0/contacts/@{alias}`
- `/api/v0/contacts/{id}`
  - ❌ GET
  - ❌ PATCH
  - ❌ DELETE

## Events

- `/api/v0/events`
  - ❌ GET (Server Sent Events)
