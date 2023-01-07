# Microchat HTTP API documentation

## Endpoints statuses

- ✅ Implemented
- ⚠️ Partially implemented
- ❌ Not implemented

## Overview

- Service ❌
  - `/api/supported_versions`: `GET` ❌ (unauthenticated access)
- Authentication ✅
  - `/api/v0/auth/sessions`: `GET` ✅, `POST` ✅ (unauthenticated access)
  - `/api/v0/auth/sessions/{session_id}`: `DELETE` ✅
- Users and bots ❌
  - `/api/v0/users`: `POST` ❌ (unauthenticated access)
  - `/api/v0/bots`: `POST` ❌
- Entities (users, bots, conferences) ✅
  - `/api/v0/entities/self`: `GET` ✅, `PATCH` ✅, `DELETE` ✅
  - `/api/v0/entities/({eid}|@{alias})`: `GET` ✅, `PATCH` ✅, `DELETE` ✅
  - `/api/v0/entities/({eid}|@{alias})/avatars`: `GET` ✅, `POST` ✅
  - `/api/v0/entities/({eid}|@{alias})/avatars/{id}`: `DELETE` ✅
  - `/api/v0/entities/({eid}|@{alias})/pemissions`: `GET` ✅, `PATCH` ✅
    Users and bots permissons. You can't manage conference's permissions.
- Chats ✅
  - `/api/v0/chats`: `GET` ✅
  - `/api/v0/chats/({eid}|@{alias})`: `GET` ✅
  - `/api/v0/chats/({eid}|@{alias})/messages`: `GET` ✅, `POST` ✅
  - `/api/v0/chats/({eid}|@{alias})/messages/{id}`: `GET` ✅, `PATCH` ✅, `DELETE` ✅
  - `/api/v0/chats/({eid}|@{alias})/messages/{id}/attachments/{id}/preview`: `GET` ✅
  - `/api/v0/chats/({eid}|@{alias})/messages/{id}/attachments/{id}/content`: `GET` ✅
  - `/api/v0/chats/({eid}|@{alias})/(photos|audios|videos|animations|files)`: `GET` ✅
  - `/api/v0/chats/({eid}|@{alias})/(photos|audios|videos|animations|files)/{id}`: `GET` ✅, `DELETE` ✅
- Conferences ✅
  - `/api/v0/conferences`: `POST` ✅
  - `/api/v0/conferences/({eid}|@{alias})/permissions`: `GET` ✅, `PATCH` ✅
  - `/api/v0/conferences/({eid}|@{alias})/members`: `GET` ✅, `POST` ✅
  - `/api/v0/conferences/({eid}|@{alias})/members/permissions`: `GET` ✅, `PATCH` ✅
  - `/api/v0/conferences/({eid}|@{alias})/members/{id}`: `GET` ✅, `DELETE` ✅
  - `/api/v0/conferences/({eid}|@{alias})/members/@{alias}`: `GET` ✅, `DELETE` ✅
  - `/api/v0/conferences/({eid}|@{alias})/members/{id}/permissions`: `GET` ✅, `PATCH` ✅
  - `/api/v0/conferences/({eid}|@{alias})/members/@{alias}/permissions`: `GET` ✅, `PATCH` ✅
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

## Users and bots

## Entities

## Chats

## Conferences

## Media

## Contacts

## Events

- `/api/v0/events`
  - ❌ GET (Server Sent Events)
