# Microchat HTTP API documentation

- `/api/users`
  - ❌ POST (unauthorized access)
- `/api/bots`
  - ❌ POST

## Authentication

- `/api/auth/tokens`
  - ✅ GET offset, count
  - ✅ POST login, password

- `/api/auth/tokens/{token}`
  - ✅ DELETE

## Chats

- `/api/chats`
  - ✅ GET offset, count

- `/api/chats/@{alias}`
  - ⚠️ GET
    - avatar
    for users:
    - name
    - surname
    - bio
    - common_conferences
    - (viewer's) permissions
    for conferences and bots:
    - title
    - description
  - ✅ DELETE (owner and admin)

- `/api/chats/@{alias}/avatars`
  - ⚠️ GET
  - ⚠️ POST (for self only)

- `/api/chats/@{alias}/avatars/{id}`
  - ⚠️ DELETE (for self and admins only)

- `/api/chats/@{alias}/messages`
  - ❌ GET offset, count
  - ❌ POST

- `/api/chats/@{alias}/messages/{id}`
  - ❌ GET
  - ❌ PATCH (author only)
  - ❌ DELETE (author and conference admins only)

- `/api/chats/@{alias}/messages/photos`
- `/api/chats/@{alias}/messages/videos`
- `/api/chats/@{alias}/messages/files`
- `/api/chats/@{alias}/messages/audios`
- `/api/chats/@{alias}/messages/links`
- `/api/chats/@{alias}/messages/animations`
  - ❌ GET offset, count

- `/api/chats/@{alias}/messages/photos/{id}`
- `/api/chats/@{alias}/messages/videos/{id}`
- `/api/chats/@{alias}/messages/files/{id}`
- `/api/chats/@{alias}/messages/audios/{id}`
- `/api/chats/@{alias}/messages/links/{id}`
- `/api/chats/@{alias}/messages/animations/{id}`
  - ❌ GET
  - ❌ DELETE (author and conference admins only)

## Conferences

- `/api/chats/@{alias}/members (conferences only)`
  - ❌ GET offset, count
  - ❌ POST

- `/api/chats/@{alias}/members/{id} (conferences only)`
- `/api/chats/@{alias}/members/@{alias} (conferences only)`
  - ❌ GET
  - ❌ DELETE (self-delete or conference admins only)

- `/api/chats/@{alias}/members/{id}/permissions (conferences only)`
- `/api/chats/@{alias}/members/@{alias}/permissions (conferences only)`
  - ❌ GET
  - ❌ PATCH (conference admins only)

## Media

- `/api/media`
  - ❌ POST

## Contacts

- `/api/contacts`
  - ❌ GET offset, count
  - ❌ POST username, [name], [surname]

- `/api/contacts/@{username}`
- `/api/contacts/{id}`
  - ❌ GET
  - ❌ PATCH
  - ❌ DELETE

## Events

- `/api/events`
  - ❌ GET (Server Sent Events)
