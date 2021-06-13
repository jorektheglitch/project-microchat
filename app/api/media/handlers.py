from aiohttp import web
from aiohttp import streamer

from app.utils import server_timing
from app.core.auth import auth_required
from app.core import media


@auth_required
async def store(request: web.Request):
    reader = await request.multipart()
    with media.tempfile() as tmpstore, server_timing(request, 'file_loading'):
        async for part in reader:
            if part.name == 'filename':
                content = await part.read()
                tmpstore.filename = content.decode()
            if part.name == 'mimetype':
                content = await part.read()
                tmpstore.mimetype = content.decode()
            if part.name == 'content':
                while True:
                    chunk = await part.read_chunk()
                    if not chunk:
                        break
                    tmpstore.append_content(chunk)
        if not tmpstore.filename:
            raise ValueError("file name does not specified")
    file_id = await media.store(tmpstore)
    return web.json_response({
        "status": 0,
        "file": {
            "id": file_id
        }
    })


# @auth_required
async def load(request: web.Request):
    data = request.rel_url.query
    message_id = data.get('message')
    attach_id = data.get('id')
    message_id, attach_id = map(int, (message_id, attach_id))
    file_hash, file_name = await media.resolve(message_id, attach_id)
    headers = {
        "Content-disposition": "attachment; filename={}".format(file_name)
    }

    file_path = media.MEDIA_DIRECTORY / file_hash.hex()

    if not file_path.exists():
        return web.Response(
            body='File <{}> does not exist'.format(file_name),
            status=404
        )
    return web.Response(
        body=file_sender(file_path=file_path),  # Could be a HUGE file
        headers=headers
    )


@streamer
async def file_sender(writer, file_path=None):
    """
    This function reads large file chunk by chunk and send it through HTTP
    without reading them into memory
    """
    with open(file_path, 'rb') as f:
        chunk = f.read(2 ** 16)
        while chunk:
            await writer.write(chunk)
            chunk = f.read(2 ** 16)
