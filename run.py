import os

import uvicorn


def main():
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'recommend.settings')

    uvicorn.run(
        "recommend.asgi:application",
        host="0.0.0.0",
        port=8000,
        log_level="debug",
        reload=True,
    )


if __name__ == "main":
    main()
